"""
TAZ-level Population Control Mapping Tool

This script creates interactive maps of PopulationSim control data at the TAZ level.
Maps are configurable and allow selection of different metrics via radio buttons.

Dependencies:
- geopandas
- folium
- pandas
- matplotlib
- seaborn

Usage:
    python taz_mapper.py
    
Configuration is handled via config.py
"""

import pandas as pd
import geopandas as gpd
import folium
from folium import plugins
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Import configuration
try:
    from config import (
        TAZ_MARGINALS_FILE, TAZ_SHAPEFILE_DIR, TAZ_SHAPEFILE_NAME, 
        TAZ_JOIN_FIELD, MAP_OUTPUT_DIR, MAP_OUTPUT_FORMAT, 
        ENABLE_TAZ_MAPPING, PRIMARY_OUTPUT_DIR
    )
except ImportError:
    # Fallback defaults if config import fails
    TAZ_MARGINALS_FILE = "taz_marginals.csv"
    TAZ_SHAPEFILE_DIR = r"C:\GitHub\tm2py-utils\tm2py_utils\inputs\maz_taz"
    TAZ_SHAPEFILE_NAME = "taz_shapes.shp"
    TAZ_JOIN_FIELD = "TAZ"
    MAP_OUTPUT_DIR = "output_2023"
    MAP_OUTPUT_FORMAT = "html"
    ENABLE_TAZ_MAPPING = True
    PRIMARY_OUTPUT_DIR = "output_2023"


class TAZMapper:
    """Class for creating TAZ-level control maps."""
    
    def __init__(self, data_dir=None, shapefile_dir=None, output_dir=None):
        """
        Initialize TAZMapper.
        
        Parameters:
        -----------
        data_dir : str, optional
            Directory containing TAZ marginals CSV file
        shapefile_dir : str, optional  
            Directory containing TAZ shapefile
        output_dir : str, optional
            Directory for map outputs
        """
        self.data_dir = data_dir or PRIMARY_OUTPUT_DIR
        self.shapefile_dir = shapefile_dir or TAZ_SHAPEFILE_DIR
        self.output_dir = output_dir or MAP_OUTPUT_DIR
        self.shapefile_name = TAZ_SHAPEFILE_NAME
        self.join_field = TAZ_JOIN_FIELD
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize data containers
        self.taz_data = None
        self.taz_shapes = None
        self.merged_data = None
        
    def load_taz_data(self):
        """Load TAZ marginals data from CSV file."""
        data_path = os.path.join(self.data_dir, TAZ_MARGINALS_FILE)
        
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"TAZ marginals file not found: {data_path}")
            
        self.taz_data = pd.read_csv(data_path)
        print(f"Loaded TAZ data: {len(self.taz_data)} records")
        print(f"Columns: {list(self.taz_data.columns)}")
        
        return self.taz_data
        
    def load_taz_shapes(self):
        """Load TAZ shapefile."""
        shapefile_path = os.path.join(self.shapefile_dir, self.shapefile_name)
        
        if not os.path.exists(shapefile_path):
            # Try to find any shapefile in the directory
            shapefiles = list(Path(self.shapefile_dir).glob("*.shp"))
            if shapefiles:
                shapefile_path = str(shapefiles[0])
                print(f"Using shapefile: {shapefile_path}")
            else:
                raise FileNotFoundError(f"No shapefile found in: {self.shapefile_dir}")
                
        self.taz_shapes = gpd.read_file(shapefile_path)
        print(f"Loaded TAZ shapes: {len(self.taz_shapes)} features")
        print(f"Shapefile columns: {list(self.taz_shapes.columns)}")
        
        # Try to identify the TAZ ID field if not explicitly set
        taz_fields = [col for col in self.taz_shapes.columns 
                     if 'taz' in col.lower() and col != 'geometry']
        if taz_fields and self.join_field not in self.taz_shapes.columns:
            self.join_field = taz_fields[0]
            print(f"Using TAZ join field: {self.join_field}")
            
        return self.taz_shapes
        
    def merge_data(self):
        """Merge TAZ data with shapefile."""
        if self.taz_data is None:
            self.load_taz_data()
        if self.taz_shapes is None:
            self.load_taz_shapes()
            
        # Identify TAZ field in data
        taz_data_field = 'TAZ'
        if 'TAZ' not in self.taz_data.columns:
            taz_fields = [col for col in self.taz_data.columns 
                         if 'taz' in col.lower()]
            if taz_fields:
                taz_data_field = taz_fields[0]
            else:
                raise ValueError("No TAZ field found in data")
                
        # Ensure both fields are same type
        self.taz_data[taz_data_field] = self.taz_data[taz_data_field].astype(str)
        self.taz_shapes[self.join_field] = self.taz_shapes[self.join_field].astype(str)
        
        # Merge data
        self.merged_data = self.taz_shapes.merge(
            self.taz_data, 
            left_on=self.join_field, 
            right_on=taz_data_field, 
            how='left'
        )
        
        print(f"Merged data: {len(self.merged_data)} records")
        
        # Check for unmatched records
        unmatched = self.merged_data[self.merged_data[taz_data_field].isna()]
        if len(unmatched) > 0:
            print(f"Warning: {len(unmatched)} TAZ shapes have no data")
            
        return self.merged_data
        
    def get_numeric_columns(self):
        """Get list of numeric columns suitable for mapping."""
        if self.merged_data is None:
            self.merge_data()
            
        # Get numeric columns excluding ID fields and geometry
        exclude_cols = [self.join_field, 'geometry'] + \
                      [col for col in self.merged_data.columns 
                       if 'id' in col.lower() or 'geoid' in col.lower()]
        
        numeric_cols = []
        for col in self.merged_data.columns:
            if col not in exclude_cols:
                if pd.api.types.is_numeric_dtype(self.merged_data[col]):
                    # Check if column has non-zero variance
                    if self.merged_data[col].notna().sum() > 0:
                        if self.merged_data[col].std() > 0:
                            numeric_cols.append(col)
                            
        return numeric_cols
        
    def create_folium_map(self, column, title=None):
        """
        Create an interactive Folium map for a specific column.
        
        Parameters:
        -----------
        column : str
            Column name to map
        title : str, optional
            Map title
        """
        if self.merged_data is None:
            self.merge_data()
            
        if column not in self.merged_data.columns:
            raise ValueError(f"Column '{column}' not found in data")
            
        # Calculate map bounds
        bounds = self.merged_data.total_bounds
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=10,
            tiles='OpenStreetMap'
        )
        
        # Add alternative tile layers
        folium.TileLayer('CartoDB positron', name='Light Map').add_to(m)
        folium.TileLayer('CartoDB dark_matter', name='Dark Map').add_to(m)
        
        # Prepare data for choropleth
        data_clean = self.merged_data.dropna(subset=[column])
        
        if len(data_clean) == 0:
            print(f"Warning: No valid data for column '{column}'")
            return m
            
        # Create choropleth layer
        folium.Choropleth(
            geo_data=data_clean,
            name=f'{column} Choropleth',
            data=data_clean,
            columns=[self.join_field, column],
            key_on=f'feature.properties.{self.join_field}',
            fill_color='YlOrRd',
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name=column,
            nan_fill_color='lightgray',
            nan_fill_opacity=0.3
        ).add_to(m)
        
        # Add tooltips with detailed information
        folium.GeoJson(
            data_clean,
            name=f'{column} Details',
            tooltip=folium.GeoJsonTooltip(
                fields=[self.join_field, column],
                aliases=[f'TAZ:', f'{column}:'],
                localize=True,
                sticky=False,
                labels=True,
                style="""
                    background-color: #F0EFEF;
                    border: 2px solid black;
                    border-radius: 3px;
                    box-shadow: 3px;
                """,
                max_width=800,
            ),
            style_function=lambda x: {
                'fillColor': 'transparent',
                'color': 'transparent',
                'weight': 0
            }
        ).add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Add title
        if title:
            title_html = f'''
                <h3 align="center" style="font-size:20px"><b>{title}</b></h3>
            '''
            m.get_root().html.add_child(folium.Element(title_html))
        
        return m
        
    def create_static_map(self, column, title=None, figsize=(12, 8)):
        """
        Create a static matplotlib map for a specific column.
        
        Parameters:
        -----------
        column : str
            Column name to map
        title : str, optional
            Map title
        figsize : tuple
            Figure size (width, height)
        """
        if self.merged_data is None:
            self.merge_data()
            
        if column not in self.merged_data.columns:
            raise ValueError(f"Column '{column}' not found in data")
            
        fig, ax = plt.subplots(1, 1, figsize=figsize)
        
        # Create choropleth
        self.merged_data.plot(
            column=column,
            ax=ax,
            legend=True,
            cmap='YlOrRd',
            missing_kwds={'color': 'lightgray'},
            edgecolor='white',
            linewidth=0.5
        )
        
        # Styling
        ax.set_axis_off()
        if title:
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
        # Add colorbar label
        cbar = ax.get_figure().get_axes()[-1]
        cbar.set_ylabel(column, rotation=270, labelpad=20)
        
        plt.tight_layout()
        return fig
        
    def create_interactive_dashboard(self):
        """Create an interactive HTML dashboard with radio button selection."""
        if self.merged_data is None:
            self.merge_data()
            
        numeric_cols = self.get_numeric_columns()
        
        if not numeric_cols:
            print("No numeric columns found for mapping")
            return None
            
        # Create the HTML structure
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>TAZ Population Controls Dashboard</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .controls {{
            padding: 20px;
            background-color: #ecf0f1;
            border-bottom: 1px solid #bdc3c7;
        }}
        .control-group {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            align-items: center;
        }}
        .radio-group {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
        }}
        .radio-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .radio-item input[type="radio"] {{
            margin: 0;
        }}
        .radio-item label {{
            margin: 0;
            cursor: pointer;
            padding: 5px 10px;
            border-radius: 5px;
            background-color: white;
            border: 1px solid #bdc3c7;
            transition: all 0.3s ease;
        }}
        .radio-item input[type="radio"]:checked + label {{
            background-color: #3498db;
            color: white;
            border-color: #3498db;
        }}
        #map {{
            height: 600px;
            width: 100%;
        }}
        .stats {{
            padding: 20px;
            background-color: #f8f9fa;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 20px;
        }}
        .stat-item {{
            text-align: center;
            padding: 10px;
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            min-width: 120px;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .stat-label {{
            font-size: 12px;
            color: #7f8c8d;
            text-transform: uppercase;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>TAZ Population Controls Dashboard</h1>
            <p>Interactive visualization of PopulationSim control data at the TAZ level</p>
        </div>
        
        <div class="controls">
            <div class="control-group">
                <strong>Select Metric:</strong>
                <div class="radio-group" id="metricSelector">
                    {self._generate_radio_buttons(numeric_cols)}
                </div>
            </div>
        </div>
        
        <div id="map"></div>
        
        <div class="stats" id="statsPanel">
            <!-- Statistics will be populated by JavaScript -->
        </div>
    </div>

    <script>
        // Initialize map
        var map = L.map('map').setView([37.7749, -122.4194], 9);
        
        // Add base layers
        var osm = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);
        
        var cartodb = L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© CartoDB'
        }});
        
        // Layer control
        var baseLayers = {{
            "OpenStreetMap": osm,
            "Light Map": cartodb
        }};
        L.control.layers(baseLayers).addTo(map);
        
        // Global variables
        var currentLayer = null;
        var geoData = {json.dumps(self.merged_data.to_json())};
        var geojsonData = JSON.parse(geoData);
        
        // Color scale function
        function getColor(value, min, max) {{
            var ratio = (value - min) / (max - min);
            var colors = [
                [255, 255, 178],
                [254, 217, 118],
                [254, 178, 76],
                [253, 141, 60],
                [252, 78, 42],
                [227, 26, 28],
                [177, 0, 38]
            ];
            
            var colorIndex = Math.floor(ratio * (colors.length - 1));
            colorIndex = Math.max(0, Math.min(colors.length - 1, colorIndex));
            
            var color = colors[colorIndex];
            return 'rgb(' + color[0] + ',' + color[1] + ',' + color[2] + ')';
        }}
        
        // Style function
        function style(feature, metric) {{
            var value = feature.properties[metric];
            var values = geojsonData.features
                .map(f => f.properties[metric])
                .filter(v => v !== null && v !== undefined && !isNaN(v));
            
            var min = Math.min(...values);
            var max = Math.max(...values);
            
            return {{
                fillColor: value !== null && !isNaN(value) ? getColor(value, min, max) : '#gray',
                weight: 1,
                opacity: 1,
                color: 'white',
                fillOpacity: 0.7
            }};
        }}
        
        // Update map for selected metric
        function updateMap(metric) {{
            // Remove existing layer
            if (currentLayer) {{
                map.removeLayer(currentLayer);
            }}
            
            // Add new layer
            currentLayer = L.geoJSON(geojsonData, {{
                style: function(feature) {{
                    return style(feature, metric);
                }},
                onEachFeature: function(feature, layer) {{
                    var props = feature.properties;
                    var tazId = props['{self.join_field}'] || 'N/A';
                    var value = props[metric];
                    var displayValue = value !== null && !isNaN(value) ? 
                        value.toLocaleString() : 'No data';
                    
                    layer.bindTooltip(
                        '<strong>TAZ: ' + tazId + '</strong><br>' +
                        metric + ': ' + displayValue,
                        {{permanent: false, direction: 'auto'}}
                    );
                }}
            }}).addTo(map);
            
            // Update statistics
            updateStats(metric);
            
            // Fit bounds
            map.fitBounds(currentLayer.getBounds());
        }}
        
        // Update statistics panel
        function updateStats(metric) {{
            var values = geojsonData.features
                .map(f => f.properties[metric])
                .filter(v => v !== null && v !== undefined && !isNaN(v));
            
            if (values.length === 0) {{
                document.getElementById('statsPanel').innerHTML = 
                    '<div class="stat-item"><div class="stat-value">No Data</div><div class="stat-label">Available</div></div>';
                return;
            }}
            
            var sum = values.reduce((a, b) => a + b, 0);
            var mean = sum / values.length;
            var min = Math.min(...values);
            var max = Math.max(...values);
            var median = values.sort((a, b) => a - b)[Math.floor(values.length / 2)];
            
            document.getElementById('statsPanel').innerHTML = `
                <div class="stat-item">
                    <div class="stat-value">${{sum.toLocaleString()}}</div>
                    <div class="stat-label">Total</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${{mean.toLocaleString(undefined, {{maximumFractionDigits: 1}})}}</div>
                    <div class="stat-label">Average</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${{median.toLocaleString()}}</div>
                    <div class="stat-label">Median</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${{min.toLocaleString()}}</div>
                    <div class="stat-label">Minimum</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${{max.toLocaleString()}}</div>
                    <div class="stat-label">Maximum</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${{values.length}}</div>
                    <div class="stat-label">TAZs with Data</div>
                </div>
            `;
        }}
        
        // Radio button event handlers
        document.addEventListener('DOMContentLoaded', function() {{
            var radios = document.querySelectorAll('input[name="metric"]');
            radios.forEach(function(radio) {{
                radio.addEventListener('change', function() {{
                    if (this.checked) {{
                        updateMap(this.value);
                    }}
                }});
            }});
            
            // Initialize with first metric
            if (radios.length > 0) {{
                radios[0].checked = true;
                updateMap(radios[0].value);
            }}
        }});
    </script>
</body>
</html>
        """
        
        # Save HTML file
        output_path = os.path.join(self.output_dir, 'taz_controls_dashboard.html')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"Interactive dashboard saved to: {output_path}")
        return output_path
        
    def _generate_radio_buttons(self, columns):
        """Generate HTML for radio button controls."""
        buttons = []
        for i, col in enumerate(columns):
            # Create friendly label
            label = col.replace('_', ' ').title()
            checked = 'checked' if i == 0 else ''
            
            button_html = f'''
                <div class="radio-item">
                    <input type="radio" id="metric_{col}" name="metric" value="{col}" {checked}>
                    <label for="metric_{col}">{label}</label>
                </div>
            '''
            buttons.append(button_html)
        
        return '\n'.join(buttons)
        
    def create_all_maps(self):
        """Create maps for all numeric columns."""
        if not ENABLE_TAZ_MAPPING:
            print("TAZ mapping is disabled in configuration")
            return
            
        numeric_cols = self.get_numeric_columns()
        
        if not numeric_cols:
            print("No numeric columns found for mapping")
            return
            
        print(f"Creating maps for {len(numeric_cols)} columns...")
        
        # Create interactive dashboard
        if MAP_OUTPUT_FORMAT in ['html', 'both']:
            self.create_interactive_dashboard()
        
        # Create individual static maps
        if MAP_OUTPUT_FORMAT in ['png', 'both']:
            for col in numeric_cols:
                try:
                    fig = self.create_static_map(col, title=f'TAZ {col.replace("_", " ").title()}')
                    output_path = os.path.join(self.output_dir, f'taz_map_{col}.png')
                    fig.savefig(output_path, dpi=300, bbox_inches='tight')
                    plt.close(fig)
                    print(f"Static map saved: {output_path}")
                except Exception as e:
                    print(f"Error creating map for {col}: {str(e)}")
                    
        print("Map creation completed!")


def main():
    """Main function to run TAZ mapping."""
    if not ENABLE_TAZ_MAPPING:
        print("TAZ mapping is disabled in configuration")
        return
        
    try:
        # Initialize mapper
        mapper = TAZMapper()
        
        # Create all maps
        mapper.create_all_maps()
        
        print("\nTAZ mapping completed successfully!")
        print(f"Check output directory: {mapper.output_dir}")
        
    except Exception as e:
        print(f"Error in TAZ mapping: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
