# NYQP 2025 Analysis

Analysis tools and visualizations for the New York QSO Party 2025 contest data.

## Features

- **Interactive Animated Map**: Real-time visualization of mobile station activity during the contest
- **Statistical Charts**: Band activity, QSO distributions, and performance analysis
- **Enhanced Static Map**: County-by-county activity overview
- **Chart Gallery**: Comprehensive collection of contest statistics

## Generated Outputs

- `outputs/html/nyqp_animated_map.html` - Interactive animated map showing mobile station movement
- `outputs/html/nyqp_enhanced_map.html` - Static enhanced map with county statistics  
- `outputs/html/chart_gallery.html` - Gallery of all generated charts
- `outputs/charts/` - Individual chart images and thumbnails

## Key Scripts

- `scripts/new_generate_animated_map.py` - Main animated map generator
- `scripts/generate_enhanced_map.py` - Static enhanced map generator
- `scripts/create_charts.py` - Statistical chart generator
- `scripts/create_sql_db.py` - Database creation from contest logs
- `scripts/setup_instructions.html` - Complete setup guide

## Requirements

- Python 3.x (built-in libraries only: sqlite3, json)
- Contest log files in Cabrillo format
- NY state geographic boundary data

## Quick Start

1. Create database from contest logs:
   ```bash
   python scripts/create_sql_db.py
   ```

2. Generate animated map:
   ```bash
   python scripts/new_generate_animated_map.py
   ```

3. Create charts and enhanced map:
   ```bash
   python scripts/create_charts.py
   python scripts/generate_enhanced_map.py
   ```

## Data Sources

- Contest logs: Cabrillo format files from NYQP 2025 participants
- Geographic data: NY county boundaries and coordinates
- QSO database: SQLite database generated from contest logs

## Mobile Station Tracking

The animated map tracks 15 mobile stations with 7,575 total QSOs, showing:
- Real-time station movement between counties
- QSO activity visualization with time progression
- County coverage and activity statistics
- Touch-friendly controls for mobile devices

## Project Structure

```
├── scripts/           # Python analysis scripts
├── outputs/           # Generated files
│   ├── charts/        # PNG visualizations and thumbnails
│   ├── html/          # Interactive maps and galleries
│   ├── data/          # Databases and geographic data
│   └── stats/         # Analysis reports
├── charts/            # Chart HTML files
└── logs/              # Contest log files (not in git)
```

## Data Quality

- **Logs Processed**: 515 total (508 contest + 7 checklogs)
- **Valid QSOs**: 79,468 (after format validation)
- **Mobile Stations**: 15 stations with 7,575 QSOs tracked
- See `outputs/stats/data_quality_errata.txt` for detailed quality notes

## Dependencies

- Python 3.x standard library (sqlite3, json)
- pandas, matplotlib (for chart generation)

See `scripts/setup_instructions.html` for complete setup documentation.
