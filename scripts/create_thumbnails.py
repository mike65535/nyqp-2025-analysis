#!/usr/bin/env python3
"""
Create thumbnail images for the chart gallery
"""

from PIL import Image
import os
from pathlib import Path

def create_thumbnails():
    """Create thumbnail versions of all chart images."""
    
    charts_dir = Path('/home/mgilmer/Downloads/QSO_PARTIES/NYQP-2025/analysis/outputs/charts')
    thumbs_dir = charts_dir / 'thumbnails'
    thumbs_dir.mkdir(exist_ok=True)
    
    # Thumbnail size
    thumb_size = (300, 200)
    
    # List of chart files to create thumbnails for
    chart_files = [
        'NYQP_2025_BoxPlotOfScoreByCategory.png',
        'NYQP_2025_DistributionOfQSOsByLocationAndMode.png', 
        'NYQP_2025_HistogramOfQSO_Totals.png',
        'NYQP_2025_160m_Activity.png',
        'NYQP_2025_80m_Activity.png',
        'NYQP_2025_40m_Activity.png',
        'NYQP_2025_20m_Activity.png',
        'NYQP_2025_15m_Activity.png',
        'NYQP_2025_10m_Activity.png',
        'NYQP_2025_AllBands_CW_Activity.png',
        'NYQP_2025_AllBands_PH_Activity.png'
    ]
    
    for chart_file in chart_files:
        chart_path = charts_dir / chart_file
        thumb_path = thumbs_dir / f"thumb_{chart_file}"
        
        if chart_path.exists():
            try:
                # Open and resize image
                with Image.open(chart_path) as img:
                    # Convert to RGB if necessary (for PNG with transparency)
                    if img.mode in ('RGBA', 'LA'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                    
                    # Create thumbnail maintaining aspect ratio
                    img.thumbnail(thumb_size, Image.Resampling.LANCZOS)
                    
                    # Save thumbnail
                    img.save(thumb_path, 'PNG', quality=85)
                    print(f"Created thumbnail: {thumb_path.name}")
                    
            except Exception as e:
                print(f"Error creating thumbnail for {chart_file}: {e}")
        else:
            print(f"Chart file not found: {chart_file}")
    
    print(f"\nThumbnails saved to: {thumbs_dir}")

if __name__ == '__main__':
    create_thumbnails()
