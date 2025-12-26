#!/usr/bin/env python3
import sqlite3
import json

def get_mobile_logs():
    """Return list of mobile log files based on CATEGORY-STATION: MOBILE"""
    return [
        '/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/logs/ab1bl.log',
        # '/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/logs/ad4eb.log',  # Outside NY
        '/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/logs/k2a.log',
        '/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/logs/k2g.log',
        '/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/logs/k2q-r.log',
        '/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/logs/k2v.log',
        '/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/logs/kq2r.log',
        '/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/logs/kv2x-m.log',
        '/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/logs/n1gbe.log',
        '/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/logs/n2b.log',
        '/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/logs/n2cu.log',
        '/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/logs/n2t.log',
        '/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/logs/w1wv-m.log',
        '/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/logs/wi2m.log',
        '/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/logs/wt2x.log'
    ]

def get_ny_counties():
    """Return list of NY county abbreviations"""
    return ['ALB','ALL','BRX','BRM','CAT','CAY','CHA','CHE','CGO','CLI','COL','COR',
            'DEL','DUT','ERI','ESS','FRA','FUL','GEN','GRE','HAM','HER','JEF','KIN',
            'LEW','LIV','MAD','MON','MTG','NAS','NEW','NIA','ONE','ONO','ONT','ORA',
            'ORL','OSW','OTS','PUT','QUE','REN','RIC','ROC','SAR','SCH','SCO','SCU',
            'SEN','STL','STE','SUF','SUL','TIO','TOM','ULS','WAR','WAS','WAY','WES',
            'WYO','YAT']

def get_county_names():
    """Return mapping of county codes to full names"""
    return {
        "ALB": "Albany", "ALL": "Allegany", "BRX": "Bronx", "BRM": "Broome", 
        "CAT": "Cattaraugus", "CAY": "Cayuga", "CHA": "Chautauqua", "CHE": "Chemung",
        "CGO": "Chenango", "CLI": "Clinton", "COL": "Columbia", "COR": "Cortland",
        "DEL": "Delaware", "DUT": "Dutchess", "ERI": "Erie", "ESS": "Essex",
        "FRA": "Franklin", "FUL": "Fulton", "GEN": "Genesee", "GRE": "Greene",
        "HAM": "Hamilton", "HER": "Herkimer", "JEF": "Jefferson", "KIN": "Kings",
        "LEW": "Lewis", "LIV": "Livingston", "MAD": "Madison", "MON": "Monroe",
        "MTG": "Montgomery", "NAS": "Nassau", "NEW": "New York", "NIA": "Niagara",
        "ONE": "Oneida", "ONO": "Onondaga", "ONT": "Ontario", "ORA": "Orange",
        "ORL": "Orleans", "OSW": "Oswego", "OTS": "Otsego", "PUT": "Putnam",
        "QUE": "Queens", "REN": "Rensselaer", "RIC": "Richmond", "ROC": "Rockland",
        "SAR": "Saratoga", "SCH": "Schenectady", "SCO": "Schoharie", "SCU": "Schuyler",
        "SEN": "Seneca", "STE": "Steuben", "STL": "St. Lawrence", "SUF": "Suffolk",
        "SUL": "Sullivan", "TIO": "Tioga", "TOM": "Tompkins", "ULS": "Ulster",
        "WAR": "Warren", "WAS": "Washington", "WAY": "Wayne", "WES": "Westchester",
        "WYO": "Wyoming", "YAT": "Yates"
    }

def load_database_data():
    """Load all required data from database"""
    conn = sqlite3.connect('/home/mgilmer/nyqp_2025.db')
    
    # Get county QSO counts for coloring
    ny_counties = get_ny_counties()
    county_counts = {}
    for row in conn.execute('''
        SELECT worked_county, COUNT(*) as qsos
        FROM qsos 
        WHERE worked_county IN ({})
        GROUP BY worked_county
    '''.format(','.join(['?']*len(ny_counties))), ny_counties):
        county_counts[row[0]] = row[1]
    
    # Get mobile QSO data
    mobile_logs = get_mobile_logs()
    mobile_qsos = {}
    for row in conn.execute('''
        SELECT call, datetime, worked_county
        FROM qsos 
        WHERE log_file IN ({})
        ORDER BY call, datetime
    '''.format(','.join(['?']*len(mobile_logs))), mobile_logs):
        call = row[0]
        if call not in mobile_qsos:
            mobile_qsos[call] = []
        mobile_qsos[call].append({
            'datetime': row[1],
            'county': row[2]
        })
    
    conn.close()
    return county_counts, mobile_qsos

def load_reference_data():
    """Load boundaries and mobile track data from reference file"""
    with open('/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/analysis/outputs/html/_nyqp_2025_animated.html', 'r') as f:
        content = f.read()
        
        # Extract boundaries
        boundaries_start = content.find('const boundaries = ') + len('const boundaries = ')
        boundaries_end = content.find('};', boundaries_start) + 1
        boundaries_json = content[boundaries_start:boundaries_end]
        
        # Extract mobile config
        mobile_config_start = content.find('const mobileConfig = ') + len('const mobileConfig = ')
        mobile_config_end = content.find('};', mobile_config_start) + 1
        mobile_config_json = content[mobile_config_start:mobile_config_end]
        
        # Extract mobile tracks
        mobile_tracks_start = content.find('const mobileTracks = ') + len('const mobileTracks = ')
        mobile_tracks_end = content.find('};', mobile_tracks_start) + 1
        mobile_tracks_json = content[mobile_tracks_start:mobile_tracks_end]
        
        # Extract county coordinates
        county_coords_start = content.find('const countyCoords = ') + len('const countyCoords = ')
        county_coords_end = content.find('};', county_coords_start) + 1
        county_coords_json = content[county_coords_start:county_coords_end]
    
    return boundaries_json, mobile_config_json, mobile_tracks_json, county_coords_json

def generate_html(county_counts, mobile_qsos, boundaries_json, mobile_config_json, mobile_tracks_json, county_coords_json):
    """Generate the complete HTML content"""
    county_names = get_county_names()
    
    return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=3.0, user-scalable=yes, viewport-fit=cover">
    <title>NYQP 2025 Mobile Activity</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/@turf/turf@6/turf.min.js"></script>
    <style>
        html {{ 
            margin: 0; 
            padding: 0; 
            width: 100%;
            height: 100%;
            overflow: hidden;
        }}
        body {{ 
            margin: 0; 
            padding: 0; 
            font-family: Arial, sans-serif; 
            background: white; 
            width: 100%;
            height: 100%;
            overflow: hidden;
        }}
        #map {{ position: absolute; top: 0; bottom: 120px; left: 0; right: 0; background: white; }}
        #controls {{ position: absolute; bottom: 0; left: 0; right: 0; height: 120px; background: #2c3e50; color: white; padding: 4px; z-index: 1000; }}
        .control-row {{ display: flex; align-items: center; justify-content: center; margin-bottom: 4px; flex-wrap: wrap; gap: 10px; }}
        .control-btn {{ padding: 12px 20px; margin: 5px; border: none; border-radius: 6px; background: #3498db; color: white; cursor: pointer; font-size: 16px; min-width: 100px; }}
        .control-btn-short {{ padding: 8px 20px; margin: 5px; border: none; border-radius: 6px; background: #3498db; color: white; cursor: pointer; font-size: 16px; min-width: 100px; }}
        .control-btn:hover {{ background: #2980b9; }}
        .control-btn-short:hover {{ background: #2980b9; }}
        .control-btn:disabled {{ background: #7f8c8d; cursor: not-allowed; }}
        #progress-container {{ flex: 1; min-width: 200px; margin: 0 15px; background: #34495e; border-radius: 15px; height: 30px; position: relative; cursor: pointer; }}
        #progress-bar {{ background: linear-gradient(90deg, #e74c3c, #f39c12); height: 100%; border-radius: 15px; width: 0%; transition: width 0.1s ease; pointer-events: none; }}
        #progress-text {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 14px; font-weight: bold; color: white; }}
        #time-display {{ font-size: 20px; font-weight: bold; margin: 0 15px; color: white; min-width: 150px; text-align: center; }}
        #stats {{ font-size: 16px; text-align: center; color: white; margin-top: 8px; padding-bottom: 25px; height: 20px; line-height: 20px; }}
        .mobile-marker {{ text-align: center; pointer-events: auto !important; cursor: pointer; }}
        .mobile-icon {{ font-size: 28px; pointer-events: none; }}
        .mobile-label {{ color: black; font-weight: bold; font-size: 12px; text-shadow: 1px 1px 2px white, -1px -1px 2px white, 1px -1px 2px white, -1px 1px 2px white; pointer-events: none; }}
        
        /* Mobile responsive styles */
        @media (max-width: 768px) {{
            .mobile-icon {{ font-size: 32px; }}
            .mobile-label {{ font-size: 14px; font-weight: bold; }}
        }}
        
        @media (max-width: 480px) {{
            .mobile-icon {{ font-size: 36px; }}
            .mobile-label {{ font-size: 16px; font-weight: bold; }}
        }}
        .info {{ padding: 10px; background: white; border-radius: 5px; box-shadow: 0 0 15px rgba(0,0,0,0.2); }}
        .info h4 {{ margin: 0 0 5px; color: #777; }}
        .legend {{ 
            line-height: 18px; 
            color: #555; 
            position: fixed !important;
            bottom: 140px !important;
            left: 10px !important;
            z-index: 1000 !important;
            background: rgba(255, 255, 255, 0.9) !important;
            padding: 10px !important;
            border-radius: 5px !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
        }}
        .legend i {{ width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7; }}
        
        /* Completely remove popup wrapper for county tooltips */
        .county-tooltip {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }}
        .county-tooltip .leaflet-popup-content-wrapper {{
            background: transparent !important;
            box-shadow: none !important;
            border: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }}
        .county-tooltip .leaflet-popup-tip-container {{
            display: block !important;
        }}
        .county-tooltip .leaflet-popup-tip {{
            display: block !important;
        }}
        .county-tooltip .leaflet-popup-content {{
            background: rgba(255, 255, 255, 0.95) !important;
            border: 1px solid #999 !important;
            border-radius: 3px !important;
            padding: 6px 8px !important;
            margin: 0 !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.3) !important;
            font-size: 14px !important;
            line-height: 1.3 !important;
        }}
        
        /* Improve touch targets for mobile */
        @media (max-width: 768px) {{
            .county-tooltip .leaflet-popup-content {{ font-size: 16px !important; min-width: 180px !important; padding: 12px !important; }}
            .mobile-marker {{ min-width: 44px; min-height: 44px; }} /* Apple's minimum touch target */
        }}
        
        /* iPad-specific improvements */
        @media (hover: none) and (pointer: coarse) {{
            .leaflet-interactive {{ 
                -webkit-tap-highlight-color: rgba(52, 152, 219, 0.3);
            }}
            .mobile-marker {{
                min-width: 50px;
                min-height: 50px;
            }}
        }}
        
        /* Prevent popup from closing during animations */
        .leaflet-popup-content-wrapper {{ pointer-events: auto; }}
        
        /* Make county polygons more touchable */
        .leaflet-interactive {{ 
            cursor: pointer;
            -webkit-tap-highlight-color: rgba(0, 0, 0, 0.2);
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div id="controls">
        <div class="control-row">
            <button class="control-btn" id="playBtn" onclick="togglePlay()">▶ Play</button>
            <button class="control-btn-short" onclick="resetAnimation()">⏹ Reset</button>
            <button class="control-btn" onclick="changeSpeed(-1)">⏪ Slower</button>
            <button class="control-btn" onclick="changeSpeed(1)">⏩ Faster</button>
        </div>
        <div class="control-row">
            <div id="time-display">2025-10-18 14:00Z</div>
            <div id="progress-container" onclick="seekToPosition(event)">
                <div id="progress-bar"></div>
                <div id="progress-text">0%</div>
            </div>
        </div>
        <div id="stats">NYQP 2025 Mobile Activity | QSOs: <span id="qso-count">0</span> | Counties Covered: <span id="active-counties">0</span></div>
    </div>
    <script>
        // Data from Python
        const boundaries = {boundaries_json};
        const countyCounts = {json.dumps(county_counts)};
        const nameMap = {json.dumps(county_names)};
        const mobileConfig = {mobile_config_json};
        const mobileTracks = {mobile_tracks_json};
        const countyCoords = {county_coords_json};
        const mobileQSOs = {json.dumps(mobile_qsos)};
        
        // Animation state
        let isPlaying = false;
        let currentTime = new Date('2025-10-18T14:00:00');
        let animationSpeed = 100;
        let animationInterval;
        let mobileMarkers = {{}};
        
        // Initialize map and layers
        const map = L.map('map', {{
            tap: true,
            tapTolerance: 20,
            touchZoom: true,
            dragging: true
        }});
        
        function calculateAnimationState(targetTime) {{
            const state = {{
                totalQSOs: 0,
                countiesCovered: new Set(),
                mobilePositions: {{}}
            }};
            
            // Count ALL mobile QSOs up to target time (use < instead of <= to exclude exact time)
            Object.keys(mobileQSOs).forEach(call => {{
                if (mobileQSOs[call]) {{
                    mobileQSOs[call].forEach(qsoEntry => {{
                        const qsoTime = new Date(qsoEntry.datetime);
                        if (qsoTime < targetTime) {{  // Changed from <= to <
                            state.totalQSOs++;
                        }}
                    }});
                }}
            }});
            
            // Calculate mobile positions and counties covered (only for stations with track data)
            Object.keys(mobileTracks).forEach(call => {{
                const track = mobileTracks[call];
                let currentPosition = null;
                
                // Track ALL counties visited up to target time (cumulative)
                for (let i = 0; i < track.length; i++) {{
                    const entry = track[i];
                    let entryTimeStr = entry.timestamp;
                    if (entryTimeStr.length === 15) {{
                        const parts = entryTimeStr.split(' ');
                        const timePart = parts[1];
                        const hour = timePart.substring(0, 2);
                        const minute = timePart.substring(2, 4);
                        entryTimeStr = parts[0] + ' ' + hour + ':' + minute + ':00';
                    }}
                    
                    const entryTime = new Date(entryTimeStr);
                    if (entryTime < targetTime) {{
                        currentPosition = {{ county: entry.county, trackIndex: i }};
                        // Add to counties covered (cumulative)
                        if (entry.county.includes('/')) {{
                            entry.county.split('/').forEach(c => state.countiesCovered.add(c));
                        }} else {{
                            state.countiesCovered.add(entry.county);
                        }}
                    }} else {{
                        break;
                    }}
                }}
                
                if (currentPosition) {{
                    state.mobilePositions[call] = currentPosition;
                }}
            }});
            
            return state;
        }}
        
        function updateDisplay(state) {{
            const timeStr = currentTime.getFullYear() + '-' + 
                          String(currentTime.getMonth() + 1).padStart(2, '0') + '-' + 
                          String(currentTime.getDate()).padStart(2, '0') + ' ' + 
                          String(currentTime.getHours()).padStart(2, '0') + ':' + 
                          String(currentTime.getMinutes()).padStart(2, '0') + 'Z';
            
            document.getElementById('time-display').textContent = timeStr;
            document.getElementById('qso-count').textContent = state.totalQSOs.toLocaleString();
            document.getElementById('active-counties').textContent = state.countiesCovered.size;
            
            const totalMinutes = (new Date('2025-10-19T02:00:00') - new Date('2025-10-18T14:00:00')) / 60000;
            const currentMinutes = (currentTime - new Date('2025-10-18T14:00:00')) / 60000;
            const progress = Math.min((currentMinutes / totalMinutes) * 100, 100);
            
            document.getElementById('progress-bar').style.width = progress + '%';
            document.getElementById('progress-text').textContent = Math.round(progress) + '%';
            
            // Update county colors based on mobile activity
            const maxCount = updateCountyColors(state);
            
            // Update legend based on current mobile activity
            updateLegend(maxCount);
        }}
        
        function updateCountyColors(state) {{
            if (window.countyLayer) {{
                // Count mobile QSOs by the county the mobile was operating FROM
                const countyCounts = {{}};
                
                // For each mobile station, count their QSOs and attribute them to counties they visited
                Object.keys(mobileTracks).forEach(call => {{
                    const track = mobileTracks[call];
                    if (!mobileQSOs[call]) return;
                    
                    // For each QSO, find which county the mobile was in at that time
                    mobileQSOs[call].forEach(qsoEntry => {{
                        const qsoTime = new Date(qsoEntry.datetime);
                        if (qsoTime < currentTime) {{
                            // Find which county the mobile was in when they made this QSO
                            let qsoCounty = null;
                            for (let i = 0; i < track.length; i++) {{
                                const entry = track[i];
                                let entryTimeStr = entry.timestamp;
                                if (entryTimeStr.length === 15) {{
                                    const parts = entryTimeStr.split(' ');
                                    const timePart = parts[1];
                                    const hour = timePart.substring(0, 2);
                                    const minute = timePart.substring(2, 4);
                                    entryTimeStr = parts[0] + ' ' + hour + ':' + minute + ':00';
                                }}
                                
                                const entryTime = new Date(entryTimeStr);
                                if (entryTime <= qsoTime) {{
                                    qsoCounty = entry.county;
                                }} else {{
                                    break;
                                }}
                            }}
                            
                            // Count the QSO for the county the mobile was operating from
                            if (qsoCounty) {{
                                if (qsoCounty.includes('/')) {{
                                    qsoCounty.split('/').forEach(c => {{
                                        countyCounts[c] = (countyCounts[c] || 0) + 1;
                                    }});
                                }} else {{
                                    countyCounts[qsoCounty] = (countyCounts[qsoCounty] || 0) + 1;
                                }}
                            }}
                        }}
                    }});
                }});
                
                const maxCount = Math.max(...Object.values(countyCounts), 1);
                
                window.countyLayer.eachLayer(function(layer) {{
                    const countyCode = layer.countyCode;
                    const count = countyCounts[countyCode] || 0;
                    
                    // Only update style if color changed
                    const newColor = getColor(count, maxCount);
                    if (!layer._lastColor || layer._lastColor !== newColor) {{
                        layer.setStyle({{
                            fillColor: newColor
                        }});
                        layer._lastColor = newColor;
                    }}
                    
                    // Only update popup if content changed
                    const countyName = layer.feature.properties.NAME;
                    const newPopupContent = `<b>${{countyName}} (${{countyCode}})</b><br>Mobile QSOs FROM here: ${{count}}`;
                    if (!layer._lastPopupContent || layer._lastPopupContent !== newPopupContent) {{
                        const popup = layer.getPopup();
                        if (popup) {{
                            popup.setContent(newPopupContent);
                            layer._lastPopupContent = newPopupContent;
                        }}
                    }}
                }});
                
                return maxCount; // Return for legend use
            }}
            return 1;
        }}
        
        function getColor(count, max) {{
            const ratio = count / max;
            if (ratio > 0.8) return '#BD0026';
            if (ratio > 0.6) return '#E31A1C';
            if (ratio > 0.4) return '#FC4E2A';
            if (ratio > 0.2) return '#FD8D3C';
            if (ratio > 0.1) return '#FEB24C';
            if (ratio > 0.05) return '#FED976';
            if (ratio > 0) return '#FFEDA0';
            return '#d0d0d0';  // Darker gray for zero
        }}
        
        function updateLegend(maxCount) {{
            if (window.mapLegend) {{
                const legendDiv = document.querySelector('.legend');
                if (legendDiv) {{
                    let legendHTML = '<h4>Mobile QSOs FROM County</h4>';
                    legendHTML += `<i style="background:#d0d0d0"></i> 0<br>`;
                    
                    if (maxCount > 0) {{
                        if (maxCount <= 5) {{
                            // Simple legend for low counts
                            legendHTML += `<i style="background:#FFEDA0"></i> 1<br>`;
                            if (maxCount >= 3) legendHTML += `<i style="background:#FEB24C"></i> 2-3<br>`;
                            if (maxCount >= 5) legendHTML += `<i style="background:#BD0026"></i> 4+<br>`;
                        }} else if (maxCount <= 20) {{
                            // Medium legend
                            const step = Math.floor(maxCount / 3);
                            legendHTML += `<i style="background:#FFEDA0"></i> 1-${{step}}<br>`;
                            legendHTML += `<i style="background:#FEB24C"></i> ${{step + 1}}-${{step * 2}}<br>`;
                            legendHTML += `<i style="background:#BD0026"></i> ${{step * 2 + 1}}+<br>`;
                        }} else {{
                            // Full legend for high counts
                            legendHTML += `<i style="background:#FFEDA0"></i> 1-${{Math.floor(maxCount * 0.05)}}<br>`;
                            legendHTML += `<i style="background:#FED976"></i> ${{Math.floor(maxCount * 0.05) + 1}}-${{Math.floor(maxCount * 0.1)}}<br>`;
                            legendHTML += `<i style="background:#FEB24C"></i> ${{Math.floor(maxCount * 0.1) + 1}}-${{Math.floor(maxCount * 0.2)}}<br>`;
                            legendHTML += `<i style="background:#FD8D3C"></i> ${{Math.floor(maxCount * 0.2) + 1}}-${{Math.floor(maxCount * 0.4)}}<br>`;
                            legendHTML += `<i style="background:#FC4E2A"></i> ${{Math.floor(maxCount * 0.4) + 1}}-${{Math.floor(maxCount * 0.6)}}<br>`;
                            legendHTML += `<i style="background:#E31A1C"></i> ${{Math.floor(maxCount * 0.6) + 1}}-${{Math.floor(maxCount * 0.8)}}<br>`;
                            legendHTML += `<i style="background:#BD0026"></i> ${{Math.floor(maxCount * 0.8) + 1}}+<br>`;
                        }}
                    }}
                    
                    legendDiv.innerHTML = legendHTML;
                }}
            }}
        }}
        
        function hasFirstHourActivity(call) {{
            if (!mobileQSOs[call]) return false;
            const firstHourEnd = new Date('2025-10-18T15:00:00');
            return mobileQSOs[call].some(qsoEntry => {{
                const qsoTime = new Date(qsoEntry.datetime);
                return qsoTime >= new Date('2025-10-18T14:00:00') && qsoTime <= firstHourEnd;
            }});
        }}
        
        function updateMobileMarkers(state) {{
            Object.keys(mobileMarkers).forEach(call => {{
                const mobile = mobileMarkers[call];
                
                // Always use first position if no current position (for reset)
                let position = state.mobilePositions[call];
                if (!position && mobileTracks[call] && mobileTracks[call].length > 0) {{
                    position = {{ county: mobileTracks[call][0].county, trackIndex: 0 }};
                }}
                
                // Count QSOs for this mobile up to current time (use < for reset)
                let qsoCount = 0;
                if (mobileQSOs[call]) {{
                    mobileQSOs[call].forEach(qsoEntry => {{
                        const qsoTime = new Date(qsoEntry.datetime);
                        if (qsoTime < currentTime) {{  // Changed from <= to <
                            qsoCount++;
                        }}
                    }});
                }}
                
                // Show logic: first hour activity OR has current QSOs
                let hasTrackData = mobileTracks[call] && mobileTracks[call].length > 0;
                let shouldShow = hasTrackData && (hasFirstHourActivity(call) || qsoCount > 0);
                
                if (shouldShow && !mobile.visible) {{
                    mobile.marker.addTo(map);
                    mobile.visible = true;
                }} else if (!shouldShow && mobile.visible) {{
                    map.removeLayer(mobile.marker);
                    mobile.visible = false;
                }}
                
                if (mobile.visible && position) {{
                    const coords = getCountyCoords(position.county, call);
                    if (coords) {{
                        // Only update if position or content has changed
                        const newLatLng = [coords[0], coords[1]];
                        const currentLatLng = mobile.marker.getLatLng();
                        
                        if (!currentLatLng || currentLatLng.lat !== newLatLng[0] || currentLatLng.lng !== newLatLng[1]) {{
                            mobile.marker.setLatLng(newLatLng);
                        }}
                        
                        // Only update popup if content changed
                        const newPopupContent = `<b>${{call}}</b> (${{qsoCount}} QSOs)<br>Current County: ${{position.county}}`;
                        if (mobile.lastPopupContent !== newPopupContent) {{
                            mobile.marker.setPopupContent(newPopupContent);
                            mobile.lastPopupContent = newPopupContent;
                        }}
                    }}
                }}
            }});
        }}
        
        function getCountyCoords(county, callsign) {{
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
            
            if (coords && callsign) {{
                const hash = callsign.split('').reduce((a, b) => a + b.charCodeAt(0), 0);
                const offsetLat = (hash % 7 - 3) * 0.01;
                const offsetLng = ((hash * 7) % 7 - 3) * 0.01;
                coords = [coords[0] + offsetLat, coords[1] + offsetLng];
            }}
            
            return coords;
        }}
        
        // Animation controls
        function togglePlay() {{
            if (isPlaying) {{
                pauseAnimation();
            }} else {{
                playAnimation();
            }}
        }}
        
        function playAnimation() {{
            isPlaying = true;
            document.getElementById('playBtn').textContent = '|| Pause';
            
            // Don't automatically close popups - let user control them
            
            animationInterval = setInterval(() => {{
                currentTime = new Date(currentTime.getTime() + 60000);
                const state = calculateAnimationState(currentTime);
                updateDisplay(state);
                updateMobileMarkers(state);
                
                if (currentTime >= new Date('2025-10-19T02:00:00')) {{
                    pauseAnimation();
                }}
            }}, animationSpeed);
        }}
        
        function pauseAnimation() {{
            isPlaying = false;
            document.getElementById('playBtn').textContent = '▶ Play';
            if (animationInterval) {{
                clearInterval(animationInterval);
            }}
        }}
        
        function resetAnimation() {{
            pauseAnimation();
            currentTime = new Date('2025-10-18T14:00:00');
            
            Object.keys(mobileMarkers).forEach(call => {{
                const mobile = mobileMarkers[call];
                if (mobile.visible) {{
                    map.removeLayer(mobile.marker);
                    mobile.visible = false;
                }}
            }});
            
            const state = calculateAnimationState(currentTime);
            updateDisplay(state);
            updateMobileMarkers(state);
        }}
        
        function changeSpeed(direction) {{
            if (direction > 0) {{
                animationSpeed = Math.max(animationSpeed / 2, 25);
            }} else {{
                animationSpeed = Math.min(animationSpeed * 2, 1000);
            }}
            
            if (isPlaying) {{
                pauseAnimation();
                playAnimation();
            }}
        }}
        
        function seekToPosition(event) {{
            const rect = event.currentTarget.getBoundingClientRect();
            const clickX = event.clientX - rect.left;
            const percentage = clickX / rect.width;
            
            const totalMinutes = (new Date('2025-10-19T02:00:00') - new Date('2025-10-18T14:00:00')) / 60000;
            const targetMinutes = percentage * totalMinutes;
            
            currentTime = new Date(new Date('2025-10-18T14:00:00').getTime() + (targetMinutes * 60000));
            
            const state = calculateAnimationState(currentTime);
            updateDisplay(state);
            updateMobileMarkers(state);
        }}
        
        // Initialize everything
        function initializeMap() {{
            // Create NY state boundary merge
            const allFeatures = boundaries.features;
            let merged = allFeatures[0];
            for (let i = 1; i < allFeatures.length; i++) {{
                try {{
                    merged = turf.union(merged, allFeatures[i]);
                }} catch(e) {{
                    console.log('Union failed for feature', i);
                }}
            }}
            
            // White background tile layer
            L.tileLayer('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=', {{
                attribution: ''
            }}).addTo(map);

            function getColor(count, max) {{
                const ratio = count / max;
                if (ratio > 0.8) return '#BD0026';
                if (ratio > 0.6) return '#E31A1C';
                if (ratio > 0.4) return '#FC4E2A';
                if (ratio > 0.2) return '#FD8D3C';
                if (ratio > 0.1) return '#FEB24C';
                if (ratio > 0.05) return '#FED976';
                if (ratio > 0) return '#FFEDA0';
                return '#f0f0f0';  // Light gray for zero instead of white
            }}
            
            const maxCount = 1; // Start with max of 1, will be updated dynamically
            
            // Add county layers (start with zero counts)
            const countyLayer = L.geoJSON(boundaries, {{
                style: function(feature) {{
                    return {{
                        fillColor: '#d0d0d0', // Darker gray for zero
                        weight: 1,
                        opacity: 0.8,
                        color: '#666',
                        fillOpacity: 0.7
                    }};
                }},
                onEachFeature: function(feature, layer) {{
                    const countyName = feature.properties.NAME;
                    let countyCode = null;
                    for (const [name, code] of Object.entries(nameMap)) {{
                        if (code === countyName) {{
                            countyCode = name;
                            break;
                        }}
                    }}
                    layer.countyCode = countyCode;
                    
                    // Use popup for better touch behavior on mobile
                    const popup = L.popup({{
                        closeButton: false,
                        autoClose: true,
                        closeOnClick: true,
                        className: 'county-tooltip'
                    }});
                    popup.setContent(`<b>${{countyName}} (${{countyCode}})</b><br>Mobile QSOs: 0`);
                    layer.bindPopup(popup);
                    
                    // Add click/tap handler with touch support
                    layer.on('click', function(e) {{
                        L.DomEvent.stopPropagation(e);
                        L.DomEvent.preventDefault(e);
                        this.openPopup();
                    }});
                    
                    layer.on('touchstart', function(e) {{
                        L.DomEvent.stopPropagation(e);
                        L.DomEvent.preventDefault(e);
                        const that = this;
                        // Small delay to let animation frame complete
                        setTimeout(() => that.openPopup(), 50);
                    }});
                }}
            }}).addTo(map);
            
            // Store reference for updates
            window.countyLayer = countyLayer;
            
            // Add mask layer
            if (merged) {{
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

            const nyOutline = L.geoJSON(boundaries);
            const bounds = nyOutline.getBounds();
            map.fitBounds(bounds, {{padding: [20, 20]}});
            
            // Add zoom-responsive icon scaling
            function updateIconSizes() {{
                const zoom = map.getZoom();
                const baseSize = Math.max(zoom - 5, 1) * 4 + 20; // Scale with zoom
                const labelSize = Math.max(zoom - 5, 1) * 2 + 10;
                
                const style = document.createElement('style');
                style.innerHTML = `
                    .mobile-icon {{ font-size: ${{baseSize}}px !important; }}
                    .mobile-label {{ font-size: ${{labelSize}}px !important; }}
                `;
                document.head.appendChild(style);
            }}
            
            map.on('zoomend', updateIconSizes);
            updateIconSizes(); // Initial sizing
            

            
            // Initialize mobile markers (show all that have track data)
            Object.keys(mobileTracks).forEach(call => {{
                const track = mobileTracks[call];
                if (track.length > 0 && mobileConfig[call]) {{
                    const firstPos = track[0];
                    let coords = getCountyCoords(firstPos.county, call);
                    
                    if (coords) {{
                        const icon = L.divIcon({{
                            html: `<div class="mobile-icon">${{mobileConfig[call].icon}}</div><div class="mobile-label">${{call}}</div>`,
                            className: 'mobile-marker',
                            iconSize: [80, 80],
                            iconAnchor: [40, 40]
                        }});
                        
                        const marker = L.marker([coords[0], coords[1]], {{icon}})
                            .bindPopup(`<b>${{call}}</b> (0 QSOs)<br>Current County: ${{firstPos.county}}`, {{
                                closeButton: false,
                                autoClose: true,
                                closeOnClick: true
                            }});
                        
                        // Add explicit tap handler for better touch support
                        marker.on('click', function(e) {{
                            L.DomEvent.stopPropagation(e);
                            L.DomEvent.preventDefault(e);
                            this.openPopup();
                        }});
                        
                        marker.on('touchstart', function(e) {{
                            L.DomEvent.stopPropagation(e);
                            L.DomEvent.preventDefault(e);
                            const that = this;
                            // Small delay to let animation frame complete
                            setTimeout(() => that.openPopup(), 50);
                        }});
                        
                        // Show immediately if station has any QSOs in contest
                        const hasQSOs = mobileQSOs[call] && mobileQSOs[call].length > 0;
                        
                        mobileMarkers[call] = {{
                            marker: marker,
                            visible: false,
                            lastPopupContent: ''
                        }};
                        
                        if (hasQSOs) {{
                            marker.addTo(map);
                            mobileMarkers[call].visible = true;
                        }}
                    }}
                }}
            }});
            
            // Add legend (will be updated dynamically)
            const legend = L.control({{position: 'bottomright'}});
            legend.onAdd = function(map) {{
                const div = L.DomUtil.create('div', 'info legend');
                div.innerHTML = '<h4>Mobile QSOs FROM County</h4><i style="background:#d0d0d0"></i> 0<br>';
                return div;
            }};
            legend.addTo(map);
            
            // Store legend reference for updates
            window.mapLegend = legend;
            
            // Initialize display
            const initialState = calculateAnimationState(currentTime);
            updateDisplay(initialState);
            updateMobileMarkers(initialState);
        }}
        
        // Start everything when page loads
        initializeMap();
    </script>
</body>
</html>'''

def generate_animated_map():
    """Main function to generate the animated map"""
    print("Loading database data...")
    county_counts, mobile_qsos = load_database_data()
    
    print("Loading reference data...")
    boundaries_json, mobile_config_json, mobile_tracks_json, county_coords_json = load_reference_data()
    
    print("Generating HTML...")
    html_content = generate_html(
        county_counts, mobile_qsos, boundaries_json, 
        mobile_config_json, mobile_tracks_json, county_coords_json
    )
    
    output_path = '/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/analysis/outputs/html/nyqp_animated_map.html'
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"Generated map with {len(county_counts)} counties")
    print(f"Total mobile QSOs: {sum(len(qsos) for qsos in mobile_qsos.values())}")
    print(f"Mobile stations: {len(mobile_qsos)}")

if __name__ == '__main__':
    generate_animated_map()