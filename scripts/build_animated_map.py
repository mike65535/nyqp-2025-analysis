#!/usr/bin/env python3
"""
Template-based HTML map generator for state QSO party contests.
Creates animated timeline maps from contest data.
"""

import json
from pathlib import Path
from string import Template

class AnimatedMapBuilder:
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
    
    def build_animated_map(self):
        """Build animated timeline map from template."""
        # Load the HTML template
        template_file = Path(__file__).parent / 'animated_map_template.html'
        with open(template_file, 'r') as f:
            template = Template(f.read())
        
        # Prepare template variables
        template_vars = {
            'contest_name': self.config['contest_name'],
            'state_name': self.config['state_name'],
            'mobile_tracks_json': json.dumps(self.mobile_tracks, indent=2),
            'timeline_data_json': json.dumps(self.timeline_data, indent=2),
            'boundaries_json': json.dumps(self.boundaries, indent=2),
            'mobile_configs': json.dumps(self.config['mobiles'], indent=2)
        }
        
        # Generate HTML from template
        html = template.substitute(template_vars)
        
        # Save output
        output_file = self.output_dir / f"{self.config['contest_name'].lower().replace(' ', '_')}_animated.html"
        with open(output_file, 'w') as f:
            f.write(html)
        
        print(f"Animated map saved to: {output_file}")
        return output_file

def main():
    if len(sys.argv) != 2:
        print("Usage: ./build_animated_map.py contest_config.json")
        sys.exit(1)
    
    builder = AnimatedMapBuilder(sys.argv[1])
    builder.load_data()
    builder.build_animated_map()

if __name__ == "__main__":
    import sys
    main()
