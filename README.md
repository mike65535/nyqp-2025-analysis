# NYQP 2025 Contest Analysis

Analysis tools and visualizations for the 2025 New York QSO Party contest data.

## Project Structure

```
├── scripts/           # Python analysis scripts
├── outputs/           # Generated files
│   ├── charts/        # PNG visualizations
│   ├── html/          # Web pages and statistics
│   ├── data/          # Databases and JSON files
│   └── stats/         # Analysis reports and errata
├── config/            # Configuration files
└── logs/              # Source log files (not in git)
```

## Workflow

### 1. Database Creation
```bash
cd scripts
python3 create_sql_db.py
```
- Processes all Cabrillo log files from `../logs/`
- Creates `contest_meta.db` (station metadata) and `contest_qsos.db` (QSO records)
- Validates QSO format and rejects malformed lines
- Includes all logs (contest + checklogs) for flexibility

### 2. Generate Statistics
```bash
python3 generate_stats.py
```
- Creates summary statistics (participation, QSO counts, categories)
- Outputs `contest_stats.json` and `contest_stats.html`
- Excludes checklogs from competitive analysis

### 3. Create Visualizations
```bash
python3 create_charts.py
```
- Generates three main charts:
  - Box plot of QSO counts by category (25 categories)
  - Distribution of QSOs by location and mode
  - Histogram of QSO totals per station
- Uses consistent TX-side QSO counting methodology

## Key Features

- **Clean Data**: Validates Cabrillo format and handles parsing errors gracefully
- **Flexible Analysis**: Can include/exclude checklogs as needed
- **Comprehensive Categories**: Operator type, power level, mode, station type
- **Consistent Methodology**: All charts use same QSO counting approach
- **Data Quality Tracking**: Documents parsing issues and edge cases

## Data Quality

See `outputs/stats/data_quality_errata.txt` for known data issues and their impact on analysis.

## Dependencies

- Python 3.x
- pandas
- matplotlib
- sqlite3 (built-in)

## Contest Details

- **Event**: 2025 New York QSO Party
- **Date**: October 18-19, 2025
- **Logs Processed**: 515 total (508 contest + 7 checklogs)
- **Valid QSOs**: 79,468 (after format validation)
