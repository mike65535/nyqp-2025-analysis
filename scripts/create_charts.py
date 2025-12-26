#!/usr/bin/env python3
"""
Generate NYQP 2025 analysis charts matching 2024 style
"""

import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path

def create_charts():
    """Generate the three main analysis charts."""
    
    # Database connections
    meta_db = '/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/analysis/outputs/data/contest_meta.db'
    qso_db = '/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/analysis/outputs/data/contest_qsos.db'
    output_dir = Path('/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/analysis/outputs/charts')
    
    # Chart 1: Box Plot of Score by Category
    create_score_boxplot(meta_db, qso_db, output_dir)
    
    # Chart 2: Distribution of QSOs by Location and Mode
    create_qso_distribution(meta_db, qso_db, output_dir)
    
    # Chart 3: Histogram of QSO Totals
    create_qso_histogram(qso_db, output_dir)
    
    # Chart 4: Band Activity Over Time (individual charts)
    create_band_activity_chart(meta_db, qso_db, output_dir)
    
    # Chart 5: Stacked Band Activity by Mode
    create_stacked_band_charts(meta_db, qso_db, output_dir)

def create_score_boxplot(meta_db, qso_db, output_dir):
    """Create box plot of scores by category using claimed scores with QSO count fallback."""
    
    # Get station metadata
    meta_conn = sqlite3.connect(meta_db)
    stations = pd.read_sql_query("""
        SELECT callsign, operator_category, transmitter_category, station_type, power, mode, claimed_score
        FROM stations
        WHERE operator_category != 'CHECKLOG'
    """, meta_conn)
    meta_conn.close()
    
    # Get QSO counts per station (deduplicated)
    qso_conn = sqlite3.connect(qso_db)
    qso_counts = pd.read_sql_query("""
        SELECT station_call, COUNT(*) as qso_count
        FROM (
            SELECT DISTINCT station_call, datetime, freq, tx_call, rx_call
            FROM qsos
        )
        GROUP BY station_call
    """, qso_conn)
    qso_conn.close()
    
    # Merge data
    data = pd.merge(stations, qso_counts, left_on='callsign', right_on='station_call', how='left')
    
    # Use QSO count (TX-side) for all stations
    data['score'] = data['qso_count']
    
    # Filter out any remaining nulls and zeros
    data = data[(data['score'].notna()) & (data['score'] > 0)]
    
    # Create abbreviated category labels
    def abbreviate_category(row):
        # Operator abbreviations
        if row['operator_category'] == 'SINGLE-OP':
            op_abbrev = 'SO'
        elif row['operator_category'] == 'MULTI-OP' and row['transmitter_category'] == 'ONE':
            op_abbrev = 'MS'  # Multi-single
        elif row['operator_category'] == 'MULTI-OP' and row['transmitter_category'] == 'UNLIMITED':
            op_abbrev = 'MM'  # Multi-multi
        else:
            op_abbrev = row['operator_category']
        
        # Power abbreviations
        power_map = {'HIGH': 'HP', 'LOW': 'LP', 'QRP': 'QRP'}
        power_abbrev = power_map.get(row['power'], row['power'])
        
        # Mode abbreviations
        mode_map = {'SSB': 'PH', 'MIXED': 'MIX', 'CW': 'CW'}
        mode_abbrev = mode_map.get(row['mode'], row['mode'])
        
        # Station type abbreviations
        station_map = {'FIXED': 'F', 'PORTABLE': 'P', 'MOBILE': 'M'}
        station_abbrev = station_map.get(row['station_type'], row['station_type'])
        
        return f"{op_abbrev}-{power_abbrev}-{mode_abbrev}-{station_abbrev}"
    
    data['category_id'] = data.apply(abbreviate_category, axis=1)
    
    # Filter to categories with at least 1 station
    category_counts = data['category_id'].value_counts()
    main_categories = category_counts[category_counts >= 1].index
    plot_data = data[data['category_id'].isin(main_categories)]
    
    plt.figure(figsize=(12, 8))  # Skinnier chart
    categories_list = sorted(plot_data['category_id'].unique())
    box_data = [plot_data[plot_data['category_id'] == cat]['score'].values for cat in categories_list]
    
    # Create box plot with custom styling
    bp = plt.boxplot(box_data, tick_labels=categories_list, whis=1.5, showfliers=True,
                     patch_artist=True,  # Enable fill
                     boxprops=dict(facecolor='#1f77b4', alpha=0.7),  # Blue fill
                     medianprops=dict(color='lightgray', linewidth=2),  # Light gray median line
                     flierprops=dict(marker='o', markerfacecolor='#1f77b4', markersize=4, alpha=0.7))  # Blue dots
    categories_list = sorted(plot_data['category_id'].unique())
    box_data = [plot_data[plot_data['category_id'] == cat]['score'].values for cat in categories_list]
    
    # Create box plot with standard whisker calculation
    bp = plt.boxplot(box_data, tick_labels=categories_list, whis=1.5, showfliers=True)
    
    plt.title('Box Plot of QSO Count by Category', fontsize=16)
    plt.xlabel('category_id', fontsize=12)
    plt.ylabel('QSO Count', fontsize=12)
    plt.xticks(rotation=90, ha='right')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_dir / 'NYQP_2025_BoxPlotOfScoreByCategory.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Count how many stations included
    total_stations = len(data)
    print(f"Created box plot with {len(categories_list)} categories")
    print(f"Total stations: {total_stations} (all using TX-side QSO counts)")

def create_qso_distribution(meta_db, qso_db, output_dir):
    """Create QSO distribution by location and mode."""
    
    # Get NY stations
    meta_conn = sqlite3.connect(meta_db)
    ny_stations = pd.read_sql_query("SELECT callsign FROM stations WHERE location = 'NY'", meta_conn)['callsign'].tolist()
    meta_conn.close()
    
    # Get deduplicated QSO data (TX-side only)
    qso_conn = sqlite3.connect(qso_db)
    qsos = pd.read_sql_query("""
        SELECT DISTINCT station_call, mode, tx_call, rx_call, datetime, freq
        FROM qsos
    """, qso_conn)
    qso_conn.close()
    
    # Categorize by TX station location and mode
    qsos['tx_location'] = qsos['tx_call'].apply(lambda x: 'NY' if x in ny_stations else 'Non-NY')
    qsos['mode_clean'] = qsos['mode'].apply(lambda x: 'CW' if 'CW' in x else 'Phone')
    
    # Count categories based on TX station
    ny_cw = len(qsos[(qsos['tx_location'] == 'NY') & (qsos['mode_clean'] == 'CW')])
    ny_phone = len(qsos[(qsos['tx_location'] == 'NY') & (qsos['mode_clean'] == 'Phone')])
    non_ny_cw = len(qsos[(qsos['tx_location'] == 'Non-NY') & (qsos['mode_clean'] == 'CW')])
    non_ny_phone = len(qsos[(qsos['tx_location'] == 'Non-NY') & (qsos['mode_clean'] == 'Phone')])
    
    categories = ['NY CW QSOs', 'NY Phone QSOs', 'Non-NY CW QSOs', 'Non-NY Phone QSOs']
    counts = [ny_cw, ny_phone, non_ny_cw, non_ny_phone]
    
    plt.figure(figsize=(10, 6))
    colors = ['#1f77b4', '#17becf', '#e377c2', '#ff7f0e']
    bars = plt.bar(range(len(categories)), counts, color=colors)
    
    plt.title('Distribution of QSOs by Location and Mode', fontsize=16)
    plt.xlabel('Location and Mode', fontsize=12)
    plt.ylabel('Number of QSOs', fontsize=12)
    plt.xticks(range(len(categories)), categories, rotation=45, ha='right')
    
    # Add value labels on bars
    for bar, value in zip(bars, counts):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(counts)*0.01, 
                f'{value:,}', ha='center', va='bottom')
    
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_dir / 'NYQP_2025_DistributionOfQSOsByLocationAndMode.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Created QSO distribution chart - Total QSOs: {sum(counts):,}")

def create_qso_histogram(qso_db, output_dir):
    """Create histogram of QSO totals per station."""
    
    qso_conn = sqlite3.connect(qso_db)
    qso_counts = pd.read_sql_query("""
        SELECT station_call, COUNT(*) as qso_total
        FROM qsos 
        GROUP BY station_call
    """, qso_conn)
    qso_conn.close()
    
    plt.figure(figsize=(10, 6))
    
    # Create histogram with bins similar to 2024
    bins = range(0, 1600, 100)
    plt.hist(qso_counts['qso_total'], bins=bins, color='#1f77b4', alpha=0.7, edgecolor='black')
    
    plt.title('Histogram of QSO Totals', fontsize=16)
    plt.xlabel('QSO Total', fontsize=12)
    plt.ylabel('Number of Logs', fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Set x-axis ticks
    plt.xticks(range(0, 1600, 200))
    
    plt.tight_layout()
    
    plt.savefig(output_dir / 'NYQP_2025_HistogramOfQSO_Totals.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Created QSO histogram")

def create_band_activity_chart(meta_db, qso_db, output_dir):
    """Create stacked area chart of QSO activity by band and mode over time."""
    
    # Get QSO data with time and band info
    qso_conn = sqlite3.connect(qso_db)
    qsos = pd.read_sql_query("""
        SELECT DISTINCT station_call, freq, mode, date, time
        FROM qsos
        ORDER BY date, time
    """, qso_conn)
    qso_conn.close()
    
    # Convert frequency to band
    def freq_to_band(freq_str):
        try:
            freq = int(freq_str)
            if 1800 <= freq <= 2000: return '160m'
            elif 3500 <= freq <= 4000: return '80m'
            elif 7000 <= freq <= 7300: return '40m'
            elif 14000 <= freq <= 14350: return '20m'
            elif 21000 <= freq <= 21450: return '15m'
            elif 28000 <= freq <= 29700: return '10m'
            else: return 'VHF+'
        except:
            return 'Unknown'
    
    qsos['band'] = qsos['freq'].apply(freq_to_band)
    qsos['mode_clean'] = qsos['mode'].apply(lambda x: 'CW' if x == 'CW' else 'PH')
    
    # Create 15-minute intervals from date and time
    qsos['time_minutes'] = qsos['time'].str[:2].astype(int) * 60 + qsos['time'].str[2:4].astype(int)
    qsos['time_15min'] = (qsos['time_minutes'] // 15) * 15  # Round down to 15-minute intervals
    qsos['hour_15min'] = qsos['time_15min'] // 60
    qsos['min_15min'] = qsos['time_15min'] % 60
    qsos['time_str'] = qsos['hour_15min'].astype(str).str.zfill(2) + ':' + qsos['min_15min'].astype(str).str.zfill(2) + ':00'
    qsos['datetime_15min'] = qsos['date'] + ' ' + qsos['time_str']
    qsos['dt'] = pd.to_datetime(qsos['datetime_15min'], format='%Y-%m-%d %H:%M:%S')
    
    # Count QSOs per 15-minute interval by band and mode
    interval_counts = qsos.groupby(['dt', 'band', 'mode_clean']).size().reset_index(name='count')
    
    # Create separate charts for each band
    bands = ['160m', '80m', '40m', '20m', '15m', '10m', 'VHF+']
    
    for band in bands:
        band_data = interval_counts[interval_counts['band'] == band]
        
        if len(band_data) > 0:
            plt.figure(figsize=(12, 6))
            
            # Pivot to get CW and PH as separate columns
            pivot_data = band_data.pivot_table(index='dt', columns='mode_clean', values='count', fill_value=0)
            
            # Create smooth stacked area chart
            if 'CW' in pivot_data.columns and 'PH' in pivot_data.columns:
                plt.fill_between(pivot_data.index, 0, pivot_data['CW'], alpha=0.7, color='#1f77b4', label='CW')
                plt.fill_between(pivot_data.index, pivot_data['CW'], pivot_data['CW'] + pivot_data['PH'], 
                               alpha=0.7, color='#ff7f0e', label='PH')
            elif 'CW' in pivot_data.columns:
                plt.fill_between(pivot_data.index, 0, pivot_data['CW'], alpha=0.7, color='#1f77b4', label='CW')
            elif 'PH' in pivot_data.columns:
                plt.fill_between(pivot_data.index, 0, pivot_data['PH'], alpha=0.7, color='#ff7f0e', label='PH')
            
            plt.title(f'{band} Band Activity Over Time', fontsize=16)
            plt.xlabel('Time (UTC)', fontsize=12)
            plt.ylabel('QSOs', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Set x-axis limits to contest period (14:00 to 02:00 = 12 hours)
            contest_start = pivot_data.index.min().replace(hour=14, minute=0, second=0)
            contest_end = contest_start + pd.Timedelta(hours=12)  # Exactly 12 hours later (02:00 next day)
            plt.xlim(contest_start, contest_end)
            
            # Format x-axis to show only HH:MM times
            import matplotlib.dates as mdates
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))  # Show every 2 hours
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save individual band chart
            safe_band = band.replace('+', 'Plus')
            plt.savefig(output_dir / f'NYQP_2025_{safe_band}_Activity.png', dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"Created {band} activity chart")
        else:
            print(f"No data for {band}")
    
    print("Created all band activity charts")

def create_stacked_band_charts(meta_db, qso_db, output_dir):
    """Create stacked area charts showing all bands by mode (CW and PH)."""
    
    # Get QSO data with time and band info
    qso_conn = sqlite3.connect(qso_db)
    qsos = pd.read_sql_query("""
        SELECT DISTINCT station_call, freq, mode, date, time
        FROM qsos
        ORDER BY date, time
    """, qso_conn)
    qso_conn.close()
    
    # Convert frequency to band
    def freq_to_band(freq_str):
        try:
            freq = int(freq_str)
            if 1800 <= freq <= 2000: return '160m'
            elif 3500 <= freq <= 4000: return '80m'
            elif 7000 <= freq <= 7300: return '40m'
            elif 14000 <= freq <= 14350: return '20m'
            elif 21000 <= freq <= 21450: return '15m'
            elif 28000 <= freq <= 29700: return '10m'
            else: return 'VHF+'
        except:
            return 'Unknown'
    
    qsos['band'] = qsos['freq'].apply(freq_to_band)
    qsos['mode_clean'] = qsos['mode'].apply(lambda x: 'CW' if x == 'CW' else 'PH')
    
    # Create 15-minute intervals from date and time
    qsos['time_minutes'] = qsos['time'].str[:2].astype(int) * 60 + qsos['time'].str[2:4].astype(int)
    qsos['time_15min'] = (qsos['time_minutes'] // 15) * 15
    qsos['hour_15min'] = qsos['time_15min'] // 60
    qsos['min_15min'] = qsos['time_15min'] % 60
    qsos['time_str'] = qsos['hour_15min'].astype(str).str.zfill(2) + ':' + qsos['min_15min'].astype(str).str.zfill(2) + ':00'
    qsos['datetime_15min'] = qsos['date'] + ' ' + qsos['time_str']
    qsos['dt'] = pd.to_datetime(qsos['datetime_15min'], format='%Y-%m-%d %H:%M:%S')
    
    # Filter out VHF+
    qsos = qsos[qsos['band'] != 'VHF+']
    
    # Count QSOs per 15-minute interval by band and mode
    interval_counts = qsos.groupby(['dt', 'band', 'mode_clean']).size().reset_index(name='count')
    
    # Band order (160m on bottom, 10m on top) and colors
    bands = ['160m', '80m', '40m', '20m', '15m', '10m']
    colors = ['#8B4513', '#FF6347', '#32CD32', '#1E90FF', '#FFD700', '#FF69B4']  # Brown, Tomato, Lime, Blue, Gold, Pink
    
    # Create charts for each mode
    modes = ['CW', 'PH']
    
    for mode in modes:
        mode_data = interval_counts[interval_counts['mode_clean'] == mode]
        
        if len(mode_data) > 0:
            plt.figure(figsize=(12, 8))
            
            # Pivot to get bands as columns
            pivot_data = mode_data.pivot_table(index='dt', columns='band', values='count', fill_value=0)
            
            # Ensure all bands are present
            for band in bands:
                if band not in pivot_data.columns:
                    pivot_data[band] = 0
            
            # Reorder columns to match band order
            pivot_data = pivot_data[bands]
            
            # Create stacked area chart
            plt.stackplot(pivot_data.index, *[pivot_data[band] for band in bands], 
                         labels=bands, colors=colors, alpha=0.8)
            
            plt.title(f'All Bands Activity Over Time - {mode} Mode', fontsize=16)
            plt.xlabel('Time (UTC)', fontsize=12)
            plt.ylabel('QSOs', fontsize=12)
            plt.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
            plt.grid(True, alpha=0.3)
            
            # Set x-axis limits to contest period (14:00 to 02:00 = 12 hours)
            contest_start = pivot_data.index.min().replace(hour=14, minute=0, second=0)
            contest_end = contest_start + pd.Timedelta(hours=12)
            plt.xlim(contest_start, contest_end)
            
            # Format x-axis to show only HH:MM times
            import matplotlib.dates as mdates
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save chart
            plt.savefig(output_dir / f'NYQP_2025_AllBands_{mode}_Activity.png', dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"Created stacked {mode} band activity chart")
        else:
            print(f"No data for {mode} mode")
    
    print("Created stacked band activity charts")

if __name__ == '__main__':
    create_charts()
