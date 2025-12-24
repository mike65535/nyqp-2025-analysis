#!/usr/bin/env python3
"""
Generate contest statistics for web display
"""

import sqlite3
import json
from pathlib import Path

def generate_contest_stats():
    """Generate summary statistics from the databases."""
    
    meta_db = Path('/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/analysis/outputs/data/contest_meta.db')
    qso_db = Path('/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/analysis/outputs/data/contest_qsos.db')
    
    stats = {}
    
    # Meta database stats
    meta_conn = sqlite3.connect(meta_db)
    
    # Total logs submitted
    stats['total_logs'] = meta_conn.execute("SELECT COUNT(*) FROM stations").fetchone()[0]
    
    # Unique callsigns (should be same as total logs)
    stats['unique_callsigns'] = meta_conn.execute("SELECT COUNT(DISTINCT callsign) FROM stations").fetchone()[0]
    
    # NY vs Non-NY stations (based on location field)
    ny_count = meta_conn.execute("SELECT COUNT(*) FROM stations WHERE location = 'NY'").fetchone()[0]
    stats['ny_stations'] = ny_count
    stats['non_ny_stations'] = stats['total_logs'] - ny_count
    
    # Official overlay categories
    overlay_counts = {}
    for overlay in ['ROOKIE', 'YOUTH12', 'YOUTH17', 'YL']:
        count = meta_conn.execute("SELECT COUNT(*) FROM stations WHERE overlay = ?", (overlay,)).fetchone()[0]
        if count > 0:
            overlay_counts[overlay] = count
    stats['official_overlays'] = overlay_counts
    
    # Unofficial overlay categories
    unofficial_overlays = {}
    for row in meta_conn.execute("SELECT overlay, COUNT(*) FROM stations WHERE overlay NOT IN ('ROOKIE', 'YOUTH12', 'YOUTH17', 'YL') AND overlay IS NOT NULL AND overlay != '' GROUP BY overlay"):
        unofficial_overlays[row[0]] = row[1]
    stats['unofficial_overlays'] = unofficial_overlays
    
    # Station types
    station_types = {}
    for row in meta_conn.execute("SELECT station_type, COUNT(*) FROM stations WHERE station_type IS NOT NULL AND station_type != '' GROUP BY station_type"):
        station_types[row[0]] = row[1]
    stats['station_types'] = station_types
    
    # Operator categories
    operator_categories = {}
    for row in meta_conn.execute("SELECT operator_category, COUNT(*) FROM stations WHERE operator_category IS NOT NULL AND operator_category != '' GROUP BY operator_category"):
        operator_categories[row[0]] = row[1]
    stats['operator_categories'] = operator_categories
    
    # Power levels
    power_levels = {}
    for row in meta_conn.execute("SELECT power, COUNT(*) FROM stations WHERE power IS NOT NULL AND power != '' GROUP BY power"):
        power_levels[row[0]] = row[1]
    stats['power_levels'] = power_levels
    
    # Get NY callsigns first
    ny_callsigns = [row[0] for row in meta_conn.execute("SELECT callsign FROM stations WHERE location = 'NY'")]
    
    meta_conn.close()
    
    # QSO database stats
    qso_conn = sqlite3.connect(qso_db)
    
    # Total QSOs
    stats['total_qsos'] = qso_conn.execute("SELECT COUNT(*) FROM qsos").fetchone()[0]
    
    # QSOs by NY stations
    if ny_callsigns:
        placeholders = ','.join('?' * len(ny_callsigns))
        stats['qsos_by_ny'] = qso_conn.execute(f"SELECT COUNT(*) FROM qsos WHERE station_call IN ({placeholders})", ny_callsigns).fetchone()[0]
    else:
        stats['qsos_by_ny'] = 0
    
    qso_conn.close()
    
    return stats

def format_stats_html(stats):
    """Format stats as HTML for web display."""
    
    html = f"""
<div class="contest-stats">
    <h2>2025 New York QSO Party Statistics</h2>
    
    <div class="stat-section">
        <h3>Participation</h3>
        <ul>
            <li><strong>Total Logs Submitted:</strong> {stats['total_logs']:,}</li>
            <li><strong>Unique Callsigns:</strong> {stats['unique_callsigns']:,}</li>
            <li><strong>New York Stations:</strong> {stats['ny_stations']:,}</li>
            <li><strong>Non-New York Stations:</strong> {stats['non_ny_stations']:,}</li>
        </ul>
    </div>
    
    <div class="stat-section">
        <h3>QSO Activity</h3>
        <ul>
            <li><strong>Total QSOs:</strong> {stats['total_qsos']:,}</li>
            <li><strong>QSOs by NY Stations:</strong> {stats['qsos_by_ny']:,}</li>
        </ul>
    </div>
"""
    
    if stats['official_overlays']:
        html += """
    <div class="stat-section">
        <h3>Official Overlay Categories</h3>
        <ul>
"""
        for overlay, count in stats['official_overlays'].items():
            html += f"            <li><strong>{overlay}:</strong> {count}</li>\n"
        html += "        </ul>\n    </div>\n"
    
    if stats['unofficial_overlays']:
        html += """
    <div class="stat-section">
        <h3>Unofficial Overlay Categories</h3>
        <ul>
"""
        for overlay, count in stats['unofficial_overlays'].items():
            html += f"            <li><strong>{overlay}:</strong> {count}</li>\n"
        html += "        </ul>\n    </div>\n"
    
    if stats['station_types']:
        html += """
    <div class="stat-section">
        <h3>Station Types</h3>
        <ul>
"""
        for stype, count in stats['station_types'].items():
            html += f"            <li><strong>{stype}:</strong> {count}</li>\n"
        html += "        </ul>\n    </div>\n"
    
    if stats['operator_categories']:
        html += """
    <div class="stat-section">
        <h3>Operator Categories</h3>
        <ul>
"""
        for opcat, count in stats['operator_categories'].items():
            html += f"            <li><strong>{opcat}:</strong> {count}</li>\n"
        html += "        </ul>\n    </div>\n"
    
    if stats['power_levels']:
        html += """
    <div class="stat-section">
        <h3>Power Levels</h3>
        <ul>
"""
        for power, count in stats['power_levels'].items():
            html += f"            <li><strong>{power}:</strong> {count}</li>\n"
        html += "        </ul>\n    </div>\n"
    
    html += "</div>"
    return html

if __name__ == '__main__':
    stats = generate_contest_stats()
    
    # Save as JSON
    with open('/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/analysis/outputs/data/contest_stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    # Save as HTML
    html = format_stats_html(stats)
    with open('/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/analysis/outputs/html/contest_stats.html', 'w') as f:
        f.write(html)
    
    print("Contest Statistics:")
    print(f"Total Logs: {stats['total_logs']}")
    print(f"NY Stations: {stats['ny_stations']}")
    print(f"Non-NY Stations: {stats['non_ny_stations']}")
    print(f"Total QSOs: {stats['total_qsos']:,}")
