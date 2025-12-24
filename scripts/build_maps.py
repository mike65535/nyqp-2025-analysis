#!/usr/bin/env python3
"""
Build interactive and animated HTML maps for state QSO party contests.
Generates two versions:
1. Static interactive map with county heat map and mobile markers
2. Animated timeline map with playback controls
"""

import json
from pathlib import Path
from datetime import datetime

class MapBuilder:
    def __init__(self, config_file):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.output_dir = Path(self.config['output_directory'])
        
    def load_data(self):
        """Load all required data files."""
        with open(self.output_dir / 'mobile_tracks.json', 'r') as f:
            self.mobile_tracks = json.load(f)
        
        with open(self.output_dir / 'timeline_data.json', 'r') as f:
            self.timeline_data = json.load(f)
        
        with open(self.output_dir / 'ny-counties-boundaries.json', 'r') as f:
            self.boundaries = json.load(f)
    
    def calculate_county_coords(self):
        """Calculate center coordinates for each county."""
        coords = {}
        for feature in self.boundaries['features']:
            name = feature['properties']['NAME']
            geom = feature['geometry']
            
            # Get all coordinates
            all_coords = []
            if geom['type'] == 'MultiPolygon':
                for polygon in geom['coordinates']:
                    for ring in polygon:
                        all_coords.extend(ring)
            else:  # Polygon
                all_coords = geom['coordinates'][0]
            
            # Calculate centroid
            lats = [c[1] for c in all_coords]
            lons = [c[0] for c in all_coords]
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            
            # Get county code
            county_code = None
            for code, full_name in self.config['county_codes'].items():
                if full_name == name:
                    county_code = code
                    break
            
            if county_code:
                coords[county_code] = [center_lat, center_lon]
        
        return coords
    
    def build_static_map(self):
        """Build static interactive map (no animation)."""
        county_coords = self.calculate_county_coords()
        
        # Count QSOs per county
        county_counts = {}
        for qso in self.timeline_data:
            county = qso['county']
            county_counts[county] = county_counts.get(county, 0) + 1
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{self.config['contest_name']} - Interactive Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; }}
        #map {{ position: absolute; top: 0; bottom: 0; left: 0; right: 0; }}
        .info {{ padding: 10px; background: white; border-radius: 5px; box-shadow: 0 0 15px rgba(0,0,0,0.2); }}
        .info h4 {{ margin: 0 0 5px; color: #777; }}
        .legend {{ line-height: 18px; color: #555; }}
        .legend i {{ width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        const boundaries = {json.dumps(self.boundaries)};
        const countyCoords = {json.dumps(county_coords)};
        const countyCounts = {json.dumps(county_counts)};
        const mobileConfig = {json.dumps(self.config['mobile_icons'])};
        const mobileTracks = {json.dumps(self.mobile_tracks)};
        
        const map = L.map('map');
        
        function getColor(count, max) {{
            const ratio = count / max;
            if (ratio > 0.8) return '#800026';
            if (ratio > 0.6) return '#BD0026';
            if (ratio > 0.4) return '#E31A1C';
            if (ratio > 0.2) return '#FC4E2A';
            if (ratio > 0.1) return '#FD8D3C';
            if (ratio > 0.05) return '#FEB24C';
            if (ratio > 0) return '#FED976';
            return '#e8e8e8';
        }}
        
        const maxCount = Math.max(...Object.values(countyCounts));
        
        const nyOutline = L.geoJSON(boundaries);
        const bounds = nyOutline.getBounds();
        map.fitBounds(bounds, {{padding: [20, 20]}});
        
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);
        
        const nyLayer = L.geoJSON(boundaries, {{
            style: (feature) => {{
                const countyName = feature.properties.NAME;
                let countyCode = null;
                for (const [code, name] of Object.entries({json.dumps(self.config['county_codes'])})) {{
                    if (name === countyName) {{
                        countyCode = code;
                        break;
                    }}
                }}
                const count = countyCounts[countyCode] || 0;
                return {{
                    fillColor: getColor(count, maxCount),
                    weight: 2,
                    color: '#666',
                    fillOpacity: 0.7
                }};
            }},
            onEachFeature: (feature, layer) => {{
                const countyName = feature.properties.NAME;
                let countyCode = null;
                for (const [code, name] of Object.entries({json.dumps(self.config['county_codes'])})) {{
                    if (name === countyName) {{
                        countyCode = code;
                        break;
                    }}
                }}
                const count = countyCounts[countyCode] || 0;
                layer.bindPopup(`<b>${{countyName}} (${{countyCode}})</b><br>QSOs: ${{count}}`);
            }}
        }}).addTo(map);
        
        // Add mobile markers at their final positions
        Object.keys(mobileTracks).forEach(call => {{
            const track = mobileTracks[call];
            if (track.length === 0) return;
            
            const lastPos = track[track.length - 1];
            const county = lastPos.county;
            let coords;
            
            if (county.includes('/')) {{
                const counties = county.split('/');
                const c1 = countyCoords[counties[0]];
                const c2 = countyCoords[counties[1]];
                if (c1 && c2) {{
                    coords = [(c1[0] + c2[0]) / 2, (c1[1] + c2[1]) / 2];
                }}
            }} else {{
                coords = countyCoords[county];
            }}
            
            if (coords && mobileConfig[call]) {{
                const icon = L.divIcon({{
                    html: mobileConfig[call].icon,
                    className: 'mobile-marker',
                    iconSize: [32, 32]
                }});
                
                const uniqueCounties = new Set();
                track.forEach(entry => {{
                    if (entry.county.includes('/')) {{
                        entry.county.split('/').forEach(c => uniqueCounties.add(c));
                    }} else {{
                        uniqueCounties.add(entry.county);
                    }}
                }});
                
                L.marker([coords[0], coords[1]], {{icon}})
                    .bindPopup(`<b>${{call}}</b><br>Counties: ${{uniqueCounties.size}}<br>${{Array.from(uniqueCounties).sort().join(', ')}}`)
                    .addTo(map);
            }}
        }});
        
        // Add legend
        const legend = L.control({{position: 'bottomright'}});
        legend.onAdd = function(map) {{
            const div = L.DomUtil.create('div', 'info legend');
            div.innerHTML = '<h4>QSO Activity</h4>';
            const grades = [0, maxCount * 0.05, maxCount * 0.1, maxCount * 0.2, maxCount * 0.4, maxCount * 0.6, maxCount * 0.8];
            const colors = ['#e8e8e8', '#FED976', '#FEB24C', '#FD8D3C', '#FC4E2A', '#E31A1C', '#BD0026', '#800026'];
            
            for (let i = 0; i < grades.length; i++) {{
                div.innerHTML += '<i style="background:' + colors[i] + '"></i> ' +
                    Math.round(grades[i]) + (grades[i + 1] ? '&ndash;' + Math.round(grades[i + 1]) + '<br>' : '+');
            }}
            return div;
        }};
        legend.addTo(map);
    </script>
</body>
</html>"""
        
        output_file = self.output_dir / "nyqp_2025_animated.html"
        with open(output_file, 'w') as f:
            f.write(html)
        
        print(f"Static map saved to: {output_file}")
        return output_file
    
    def build_animated_map(self):
        """Build animated timeline map."""
        # This would be the full animated version
        # For now, just copy the existing one as template
        print("Animated map builder - use existing nyqp_2025_animated.html as template")
        print("TODO: Templatize the animated version")
    
    def build_all(self):
        """Build all map versions."""
        print(f"Building maps for {self.config['contest_name']}...")
        self.load_data()
        self.build_static_map()
        self.build_animated_map()
        print("Done!")


if __name__ == '__main__':
    builder = MapBuilder('contest_config.json')
    builder.build_all()
