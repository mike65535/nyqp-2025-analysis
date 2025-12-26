#!/usr/bin/env python3
"""
Generate enhanced interactive map from SQL databases.
Creates county-level QSO activity visualization for NYQP 2025.
"""

import sqlite3
import json
from pathlib import Path

def get_county_data():
    """Extract county QSO data from databases."""
    db_path = Path("/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/analysis/outputs/data")
    
    # Connect to databases
    meta_conn = sqlite3.connect(db_path / "contest_meta.db")
    qso_conn = sqlite3.connect(db_path / "contest_qsos.db")
    
    # Count QSOs by county from tx_county field
    county_qsos = {}
    county_top_stations = {}
    
    # Valid NY county abbreviations
    valid_ny_counties = {
        'ALB', 'ALL', 'BRM', 'BRX', 'CAT', 'CAY', 'CHA', 'CHE', 'CGO', 'CLI', 
        'COL', 'COR', 'DEL', 'DUT', 'ERI', 'ESS', 'FRA', 'FUL', 'GEN', 'GRE',
        'HAM', 'HER', 'JEF', 'KIN', 'LEW', 'LIV', 'MAD', 'MON', 'MTG', 'NAS',
        'NEW', 'NIA', 'ONE', 'ONO', 'ONT', 'ORA', 'ORL', 'OSW', 'OTS', 'PUT',
        'QUE', 'REN', 'RIC', 'ROC', 'SAR', 'SCH', 'SCO', 'SCU', 'SEN', 'STE',
        'STL', 'SUF', 'SUL', 'TIO', 'TOM', 'ULS', 'WAR', 'WAS', 'WAY', 'WES',
        'WYO', 'YAT'
    }
    
    # Get total QSO count first
    total_cursor = qso_conn.execute("SELECT COUNT(*) FROM qsos")
    total_qsos = total_cursor.fetchone()[0]
    
    # Get QSO counts by TX county (NY stations transmitting)
    cursor = qso_conn.execute("""
        SELECT tx_county, tx_call, COUNT(*) as qso_count
        FROM qsos 
        WHERE tx_county IS NOT NULL AND tx_county != ''
        GROUP BY tx_county, tx_call
        ORDER BY tx_county, qso_count DESC
    """)
    
    for county, callsign, qso_count in cursor.fetchall():
        county = county.upper()
        # Only include valid NY counties
        if county in valid_ny_counties:
            if county not in county_qsos:
                county_qsos[county] = 0
                county_top_stations[county] = []
            
            county_qsos[county] += qso_count
            county_top_stations[county].append({"call": callsign, "qsos": qso_count})
    
    # Sort and limit top stations per county
    for county in county_top_stations:
        county_top_stations[county].sort(key=lambda x: x["qsos"], reverse=True)
        county_top_stations[county] = county_top_stations[county][:5]
    
    meta_conn.close()
    qso_conn.close()
    
    return county_qsos, county_top_stations, total_qsos

def generate_map_html():
    """Generate the complete HTML map file."""
    county_qsos, county_top_stations, total_qsos = get_county_data()
    
    # County name to abbreviation mapping
    name_map = {
        "Albany": "ALB", "Allegany": "ALL", "Broome": "BRM", "Bronx": "BRX",
        "Cattaraugus": "CAT", "Cayuga": "CAY", "Chautauqua": "CHA", "Chemung": "CHE",
        "Chenango": "CGO", "Clinton": "CLI", "Columbia": "COL", "Cortland": "COR",
        "Delaware": "DEL", "Dutchess": "DUT", "Erie": "ERI", "Essex": "ESS",
        "Franklin": "FRA", "Fulton": "FUL", "Genesee": "GEN", "Greene": "GRE",
        "Hamilton": "HAM", "Herkimer": "HER", "Jefferson": "JEF", "Kings": "KIN",
        "Lewis": "LEW", "Livingston": "LIV", "Madison": "MAD", "Monroe": "MON",
        "Montgomery": "MTG", "Nassau": "NAS", "New York": "NEW", "Niagara": "NIA",
        "Oneida": "ONE", "Onondaga": "ONO", "Ontario": "ONT", "Orange": "ORA",
        "Orleans": "ORL", "Oswego": "OSW", "Otsego": "OTS", "Putnam": "PUT",
        "Queens": "QUE", "Rensselaer": "REN", "Richmond": "RIC", "Rockland": "ROC",
        "Saratoga": "SAR", "Schenectady": "SCH", "Schoharie": "SCO", "Schuyler": "SCU",
        "Seneca": "SEN", "Steuben": "STE", "St. Lawrence": "STL", "Suffolk": "SUF",
        "Sullivan": "SUL", "Tioga": "TIO", "Tompkins": "TOM", "Ulster": "ULS",
        "Warren": "WAR", "Washington": "WAS", "Wayne": "WAY", "Westchester": "WES",
        "Wyoming": "WYO", "Yates": "YAT"
    }
    
    # Convert to format expected by map
    county_data = {}
    for county_abbrev, qso_count in county_qsos.items():
        county_data[county_abbrev] = {
            "qsos": qso_count,
            "top5": county_top_stations.get(county_abbrev, [])
        }
    
    total_qsos_by_county = sum(county_qsos.values())
    active_counties = len([c for c in county_qsos.values() if c > 0])
    
    print(f"Debug: Total QSOs in database: {total_qsos}")
    print(f"Debug: QSOs from NY counties: {total_qsos_by_county}")
    print(f"Debug: Active NY counties: {active_counties}")
    print(f"Debug: County count breakdown: {len(county_qsos)} counties with data")
    
    # Load NY county boundaries from JSON file
    boundaries_file = '/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/analysis/outputs/data/ny_counties.json'
    try:
        with open(boundaries_file, 'r') as f:
            boundaries_data = json.load(f)
        boundaries_json = json.dumps(boundaries_data)
        print(f"Loaded boundaries from {boundaries_file}")
    except Exception as e:
        print(f"Error loading boundaries from {boundaries_file}: {e}")
        boundaries_json = '{"type": "FeatureCollection", "features": []}'
    
    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>QSOs made from NY stations</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/@turf/turf@6/turf.min.js"></script>
    <style>
        body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; background: white; }}
        #map {{ position: absolute; top: 0; bottom: 50px; left: 0; right: 0; background: white; }}
        #info {{ position: absolute; bottom: 0; left: 0; right: 0; height: 50px; background: #2c3e50; color: white; padding: 15px; text-align: center; z-index: 1000; font-size: 16px; }}
        .popup-content {{ min-width: 250px; font-size: 16px; }}
        .popup-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
        .popup-qsos {{ font-size: 16px; margin-bottom: 12px; }}
        .popup-zero {{ color: #e74c3c; font-style: italic; font-size: 16px; }}
        .callsign-item {{ display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #ecf0f1; font-size: 15px; }}
        .callsign-rank {{ color: #95a5a6; margin-right: 8px; }}
        .callsign-call {{ font-weight: bold; color: #2980b9; }}
        .callsign-count {{ color: #7f8c8d; }}
        
        @media (max-width: 768px) {{
            #info {{ font-size: 14px; padding: 10px; }}
            .popup-content {{ min-width: 220px; }}
        }}
        
        .leaflet-popup-content-wrapper {{ padding: 15px !important; }}
        .leaflet-popup-content {{ font-size: 16px !important; }}
        
        /* Disable selection outline */
        .leaflet-interactive {{ outline: none !important; }}
        .leaflet-interactive:focus {{ outline: none !important; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div id="info">QSOs made from NY stations | {total_qsos_by_county:,} QSOs from {active_counties} of 62 NY Counties</div>
    <script>
        const boundaries = {boundaries_json};
        const countyData = {json.dumps(county_data, indent=2)};
        const nameMap = {json.dumps(name_map, indent=2)};
        
        // Create map - no tile layer initially
        const map = L.map('map', {{
            zoomControl: true,
            scrollWheelZoom: true,
            doubleClickZoom: true,
            boxZoom: true,
            keyboard: true,
            dragging: true,
            minZoom: 6,
            maxZoom: 11
        }});
        
        // Create NY state boundary merge first
        const allFeatures = boundaries.features;
        let merged = allFeatures[0];
        for (let i = 1; i < allFeatures.length; i++) {{
            try {{
                merged = turf.union(merged, allFeatures[i]);
            }} catch(e) {{
                console.log('Union failed for feature', i);
            }}
        }}
        
        // Create a white background layer
        L.tileLayer('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=', {{
            attribution: ''
        }}).addTo(map);

        // Calculate color based on QSO count
        function getColor(qsos) {{
            const maxQsos = Math.max(...Object.values(countyData).map(d => d.qsos));
            if (qsos === 0) return '#e8e8e8';
            const intensity = qsos / maxQsos;
            if (intensity > 0.8) return '#800026';
            if (intensity > 0.6) return '#BD0026';
            if (intensity > 0.4) return '#E31A1C';
            if (intensity > 0.2) return '#FC4E2A';
            if (intensity > 0.1) return '#FD8D3C';
            if (intensity > 0.05) return '#FEB24C';
            return '#FED976';
        }}

        // Add county layers
        const countyLayer = L.geoJSON(boundaries, {{
            style: function(feature) {{
                const countyName = feature.properties.NAME;
                const abbrev = nameMap[countyName];
                const qsos = countyData[abbrev] ? countyData[abbrev].qsos : 0;
                
                return {{
                    fillColor: getColor(qsos),
                    weight: 1,
                    opacity: 0.8,
                    color: '#666',
                    fillOpacity: 0.7
                }};
            }},
            onEachFeature: function(feature, layer) {{
                const countyName = feature.properties.NAME;
                const abbrev = nameMap[countyName];
                const data = countyData[abbrev];
                
                let popupContent = `<div class="popup-content">
                    <div class="popup-title">${{abbrev}} - ${{countyName}}</div>`;
                
                if (data && data.qsos > 0) {{
                    popupContent += `<div class="popup-qsos">Total QSOs: ${{data.qsos.toLocaleString()}}</div>`;
                    if (data.top5.length > 0) {{
                        popupContent += '<div><strong>Top Stations:</strong></div>';
                        data.top5.forEach((station, i) => {{
                            popupContent += `<div class="callsign-item">
                                <span><span class="callsign-rank">${{i+1}}.</span><span class="callsign-call">${{station.call}}</span></span>
                                <span class="callsign-count">${{station.qsos.toLocaleString()}}</span>
                            </div>`;
                        }});
                    }}
                }} else {{
                    popupContent += '<div class="popup-zero">No QSO activity recorded</div>';
                }}
                
                popupContent += '</div>';
                layer.bindPopup(popupContent);
                
                // Add hover effects
                layer.on({{
                    mouseover: function(e) {{
                        const layer = e.target;
                        layer.setStyle({{
                            weight: 3,
                            color: '#2c3e50',
                            fillOpacity: 0.9
                        }});
                        
                        // Show tooltip
                        const qsoCount = data && data.qsos > 0 ? data.qsos.toLocaleString() : '0';
                        layer.bindTooltip(`${{abbrev}} - ${{countyName}}<br>${{qsoCount}} QSOs`, {{
                            permanent: false,
                            direction: 'top'
                        }}).openTooltip();
                    }},
                    mouseout: function(e) {{
                        const layer = e.target;
                        layer.setStyle({{
                            weight: 1,
                            color: '#666',
                            fillOpacity: 0.7
                        }});
                        layer.closeTooltip();
                        layer.closePopup();
                    }},
                    click: function(e) {{
                        // Prevent default selection highlight
                        L.DomEvent.stopPropagation(e);
                    }}
                }});
            }}
        }}).addTo(map);

        // Add mask layer to hide everything outside NY
        if (merged) {{
            // Create inverse mask: world bbox minus NY state
            const worldBbox = [[-90, -180], [90, 180]];
            const worldPolygon = turf.bboxPolygon([-180, -90, 180, 90]);
            
            try {{
                const mask = turf.difference(worldPolygon, merged);
                if (mask) {{
                    L.geoJSON(mask, {{
                        style: {{
                            fillColor: 'white',
                            fillOpacity: 1,
                            weight: 0,
                            stroke: false
                        }},
                        interactive: false,
                        pane: 'overlayPane'
                    }}).addTo(map);
                }}
            }} catch(e) {{
                console.log('Mask creation failed:', e);
            }}
            
            // Add NY state boundary outline
            L.geoJSON(merged, {{
                style: {{
                    fillColor: 'transparent',
                    weight: 3,
                    opacity: 1,
                    color: '#1a252f',
                    fillOpacity: 0
                }},
                interactive: false
            }}).addTo(map);
        }}

        // Fit map to NY bounds with padding
        map.fitBounds([
            [40.4, -79.8],
            [45.1, -71.8]
        ], {{padding: [30, 30]}});
        
        // Restrict panning to NY area
        map.setMaxBounds([
            [39.5, -80.5],
            [45.5, -71.0]
        ]);
    </script>
</body>
</html>'''
    
    return html_content

def main():
    """Generate enhanced map HTML file."""
    output_path = Path("/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/analysis/outputs/html/nyqp_enhanced_map.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    html_content = generate_map_html()
    
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"Enhanced map generated: {output_path}")

if __name__ == "__main__":
    main()
