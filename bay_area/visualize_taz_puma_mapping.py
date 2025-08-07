#!/usr/bin/env python3
"""
TAZ-PUMA Spatial Visualization and Analysis Tool

Creates an interactive map showing TAZs and PUMAs with the ability to toggle layers.
Also generates detailed area analysis for each TAZ showing overlaps with PUMAs.

Features:
- Interactive map with toggleable layers
- PUMA boundaries in thick red lines
- TAZ boundaries in dotted blue lines
- Area analysis for TAZ-PUMA overlaps
- Summary statistics
"""

import pandas as pd
import geopandas as gpd
import folium
from folium import plugins
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class TAZPUMAVisualizer:
    """Interactive visualization of TAZ and PUMA spatial relationships"""
    
    def __init__(self):
        self.base_dir = Path("c:/GitHub/populationsim/bay_area")
        self.shapefiles_dir = Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles")
        self.output_dir = self.base_dir / "output_2023" / "spatial_analysis"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.taz_shapefile = self.shapefiles_dir / "tazs_TM2_v2_2.shp"
        self.puma_shapefile = self.shapefiles_dir / "tl_2022_06_puma20.shp"
        
        # Bay Area counties for filtering PUMAs
        self.bay_area_counties = ['001', '013', '041', '055', '075', '081', '085', '095', '097']
        
        print("🗺️  TAZ-PUMA Spatial Visualization Tool")
        print("=" * 50)
    
    def load_spatial_data(self):
        """Load TAZ and PUMA shapefiles"""
        print("📂 Loading spatial data...")
        
        # Load TAZ shapefile
        print(f"   Loading TAZs: {self.taz_shapefile}")
        if not self.taz_shapefile.exists():
            raise FileNotFoundError(f"TAZ shapefile not found: {self.taz_shapefile}")
        
        self.taz_gdf = gpd.read_file(self.taz_shapefile, engine='pyogrio')
        print(f"   ✅ Loaded {len(self.taz_gdf):,} TAZ zones")
        print(f"      Columns: {list(self.taz_gdf.columns)}")
        
        # Determine TAZ ID column
        if 'TAZ1454' in self.taz_gdf.columns:
            self.taz_id_col = 'TAZ1454'
        elif 'TAZ' in self.taz_gdf.columns:
            self.taz_id_col = 'TAZ'
        else:
            self.taz_id_col = self.taz_gdf.columns[0]
        print(f"      Using TAZ ID column: {self.taz_id_col}")
        
        # Load PUMA shapefile
        print(f"   Loading PUMAs: {self.puma_shapefile}")
        if not self.puma_shapefile.exists():
            raise FileNotFoundError(f"PUMA shapefile not found: {self.puma_shapefile}")
        
        puma_gdf_full = gpd.read_file(self.puma_shapefile, engine='pyogrio')
        print(f"   ✅ Loaded {len(puma_gdf_full):,} total PUMA zones")
        
        # Filter to Bay Area counties
        county_col = None
        for col in ['COUNTYFP20', 'COUNTYFP10', 'COUNTYFP', 'COUNTY']:
            if col in puma_gdf_full.columns:
                county_col = col
                break
        
        if county_col:
            self.puma_gdf = puma_gdf_full[puma_gdf_full[county_col].isin(self.bay_area_counties)].copy()
            print(f"   🌉 Filtered to Bay Area: {len(self.puma_gdf):,} PUMA zones")
        else:
            print("   ⚠️  No county column found, using all PUMAs")
            self.puma_gdf = puma_gdf_full.copy()
        
        # Determine PUMA ID column
        if 'PUMACE20' in self.puma_gdf.columns:
            self.puma_id_col = 'PUMACE20'
        elif 'PUMA20' in self.puma_gdf.columns:
            self.puma_id_col = 'PUMA20'
        else:
            self.puma_id_col = self.puma_gdf.columns[0]
        print(f"      Using PUMA ID column: {self.puma_id_col}")
        
        # Ensure same CRS
        if self.taz_gdf.crs != self.puma_gdf.crs:
            print(f"   🔧 Reprojecting TAZs from {self.taz_gdf.crs} to {self.puma_gdf.crs}")
            self.taz_gdf = self.taz_gdf.to_crs(self.puma_gdf.crs)
        
        print(f"   📍 Working CRS: {self.taz_gdf.crs}")
        
    def analyze_taz_puma_overlaps(self):
        """Analyze area overlaps between TAZs and PUMAs"""
        print("\n🔍 Analyzing TAZ-PUMA spatial overlaps...")
        
        # Perform spatial overlay to find intersections
        print("   Calculating intersections...")
        overlays = gpd.overlay(
            self.taz_gdf[[self.taz_id_col, 'geometry']], 
            self.puma_gdf[[self.puma_id_col, 'geometry']], 
            how='intersection'
        )
        
        if len(overlays) == 0:
            print("   ❌ No overlaps found! Check coordinate systems.")
            return None
        
        print(f"   ✅ Found {len(overlays):,} TAZ-PUMA intersection polygons")
        
        # Calculate areas
        print("   Calculating areas...")
        overlays['overlap_area'] = overlays.geometry.area
        
        # Get total TAZ areas for percentage calculations
        taz_areas = self.taz_gdf.copy()
        taz_areas['total_area'] = taz_areas.geometry.area
        taz_area_dict = dict(zip(taz_areas[self.taz_id_col], taz_areas['total_area']))
        
        overlays['total_taz_area'] = overlays[self.taz_id_col].map(taz_area_dict)
        overlays['overlap_pct'] = (overlays['overlap_area'] / overlays['total_taz_area']) * 100
        
        # Create summary by TAZ
        self.taz_puma_summary = overlays.groupby(self.taz_id_col).agg({
            self.puma_id_col: lambda x: list(x),
            'overlap_area': 'sum',
            'overlap_pct': 'sum',
            'total_taz_area': 'first'
        }).reset_index()
        
        self.taz_puma_summary['num_pumas'] = self.taz_puma_summary[self.puma_id_col].apply(len)
        self.taz_puma_summary['primary_puma'] = overlays.loc[
            overlays.groupby(self.taz_id_col)['overlap_area'].idxmax()
        ].set_index(self.taz_id_col)[self.puma_id_col]
        
        print(f"   📊 Summary created for {len(self.taz_puma_summary):,} TAZs")
        
        # Show statistics
        print("\n📈 TAZ-PUMA Overlap Statistics:")
        print(f"   • TAZs touching 1 PUMA: {(self.taz_puma_summary['num_pumas'] == 1).sum():,}")
        print(f"   • TAZs touching 2+ PUMAs: {(self.taz_puma_summary['num_pumas'] > 1).sum():,}")
        print(f"   • Max PUMAs per TAZ: {self.taz_puma_summary['num_pumas'].max()}")
        print(f"   • Unique PUMAs found: {len(set([p for pumas in self.taz_puma_summary[self.puma_id_col] for p in pumas]))}")
        
        # Save detailed analysis
        detailed_analysis = overlays[[self.taz_id_col, self.puma_id_col, 'overlap_area', 'overlap_pct']].copy()
        detailed_analysis.columns = ['TAZ_ID', 'PUMA_ID', 'Overlap_Area_SqM', 'Overlap_Percent']
        detailed_analysis = detailed_analysis.sort_values(['TAZ_ID', 'Overlap_Percent'], ascending=[True, False])
        
        # Store overlays for visualization
        self.detailed_overlays = overlays
        
        analysis_file = self.output_dir / "taz_puma_detailed_analysis.csv"
        detailed_analysis.to_csv(analysis_file, index=False)
        print(f"   💾 Detailed analysis saved: {analysis_file}")
        
        # Save summary
        summary_for_export = self.taz_puma_summary.copy()
        summary_for_export['PUMA_List'] = summary_for_export[self.puma_id_col].apply(lambda x: ';'.join(map(str, x)))
        summary_for_export = summary_for_export.drop(self.puma_id_col, axis=1)
        summary_for_export.columns = ['TAZ_ID', 'Total_Overlap_Area', 'Total_Overlap_Pct', 'TAZ_Total_Area', 'Num_PUMAs', 'Primary_PUMA', 'PUMA_List']
        
        summary_file = self.output_dir / "taz_puma_summary.csv"
        summary_for_export.to_csv(summary_file, index=False)
        print(f"   💾 Summary saved: {summary_file}")
        
        return overlays
    
    def create_interactive_map(self):
        """Create interactive Folium map with toggleable layers"""
        print("\n🗺️  Creating interactive map...")
        
        # Calculate map center
        bounds = self.taz_gdf.total_bounds
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=9,
            tiles='OpenStreetMap'
        )
        
        # Add alternative tile layers
        folium.TileLayer('CartoDB positron', name='Light Map').add_to(m)
        folium.TileLayer('CartoDB dark_matter', name='Dark Map').add_to(m)
        
        # Convert to Web Mercator for visualization
        taz_web = self.taz_gdf.to_crs('EPSG:4326')
        puma_web = self.puma_gdf.to_crs('EPSG:4326')
        
        print("   Adding PUMA boundaries (thick red)...")
        # Add PUMA boundaries - thick red lines
        puma_layer = folium.FeatureGroup(name='PUMA Boundaries (Red)', show=True)
        
        for idx, puma in puma_web.iterrows():
            # Calculate area in square kilometers
            puma_proj = gpd.GeoDataFrame([puma], crs='EPSG:4326').to_crs('EPSG:3310')  # CA Albers
            area_sqkm = puma_proj.geometry.area.iloc[0] / 1_000_000
            
            folium.GeoJson(
                puma.geometry,
                style_function=lambda x: {
                    'fillColor': 'none',
                    'color': 'red',
                    'weight': 3,
                    'opacity': 0.8,
                    'fillOpacity': 0
                },
                popup=folium.Popup(f"PUMA: {puma[self.puma_id_col]}<br>Area: {area_sqkm:.1f} km²", parse_html=True),
                tooltip=f"PUMA {puma[self.puma_id_col]} ({area_sqkm:.1f} km²)"
            ).add_to(puma_layer)
        
        puma_layer.add_to(m)
        
        # Add PUMA ID labels
        print("   Adding PUMA ID labels...")
        puma_labels = folium.FeatureGroup(name='PUMA Labels', show=True)
        
        for idx, puma in puma_web.iterrows():
            # Calculate area in square kilometers
            puma_proj = gpd.GeoDataFrame([puma], crs='EPSG:4326').to_crs('EPSG:3310')  # CA Albers
            area_sqkm = puma_proj.geometry.area.iloc[0] / 1_000_000
            
            # Add PUMA ID label at centroid with area information
            centroid = puma.geometry.centroid
            folium.Marker(
                location=[centroid.y, centroid.x],
                icon=folium.DivIcon(
                    html=f"<div style='background: white; border: 2px solid red; padding: 3px; font-weight: bold; font-size: 11px; text-align: center; border-radius: 3px;'>PUMA {puma[self.puma_id_col]}<br>{area_sqkm:.1f} km²</div>",
                    icon_size=(80, 35),
                    icon_anchor=(40, 17)
                ),
                popup=f"PUMA {puma[self.puma_id_col]}<br>Area: {area_sqkm:.1f} km²"
            ).add_to(puma_labels)
        
        puma_labels.add_to(m)
        
        print("   Adding TAZ boundaries (dotted blue)...")
        # Add TAZ boundaries - dotted blue lines  
        taz_layer = folium.FeatureGroup(name='TAZ Boundaries (Blue Dotted)', show=True)
        
        for idx, taz in taz_web.iterrows():
            # Calculate area in square kilometers
            taz_proj = gpd.GeoDataFrame([taz], crs='EPSG:4326').to_crs('EPSG:3310')  # CA Albers
            area_sqkm = taz_proj.geometry.area.iloc[0] / 1_000_000
            
            folium.GeoJson(
                taz.geometry,
                style_function=lambda x: {
                    'fillColor': 'none',
                    'color': 'blue',
                    'weight': 1,
                    'opacity': 0.6,
                    'dashArray': '5, 5',
                    'fillOpacity': 0
                },
                popup=folium.Popup(f"TAZ: {taz[self.taz_id_col]}<br>Area: {area_sqkm:.3f} km²", parse_html=True),
                tooltip=f"TAZ {taz[self.taz_id_col]} ({area_sqkm:.3f} km²)"
            ).add_to(taz_layer)
        
        taz_layer.add_to(m)
        
        # Add TAZ ID labels
        print("   Adding TAZ ID labels...")
        taz_labels = folium.FeatureGroup(name='TAZ Labels', show=False)  # Start hidden due to potential clutter
        
        for idx, taz in taz_web.iterrows():
            # Calculate area in square kilometers
            taz_proj = gpd.GeoDataFrame([taz], crs='EPSG:4326').to_crs('EPSG:3310')  # CA Albers
            area_sqkm = taz_proj.geometry.area.iloc[0] / 1_000_000
            
            # Get PUMA info for this TAZ if available
            taz_id = taz[self.taz_id_col]
            puma_info = ""
            if hasattr(self, 'taz_puma_summary'):
                taz_summary = self.taz_puma_summary[self.taz_puma_summary[self.taz_id_col] == taz_id]
                if not taz_summary.empty:
                    primary_puma = taz_summary.iloc[0]['primary_puma']
                    puma_info = f"<br>PUMA: {primary_puma}"
            
            # Add TAZ ID label at centroid
            centroid = taz.geometry.centroid
            folium.Marker(
                location=[centroid.y, centroid.x],
                icon=folium.DivIcon(
                    html=f"<div style='background: white; border: 1px solid blue; padding: 2px; font-weight: bold; font-size: 9px; text-align: center; border-radius: 2px;'>TAZ {taz_id}<br>{area_sqkm:.3f} km²{puma_info}</div>",
                    icon_size=(60, 30),
                    icon_anchor=(30, 15)
                ),
                popup=f"TAZ {taz_id}<br>Area: {area_sqkm:.3f} km²{puma_info}"
            ).add_to(taz_labels)
        
        taz_labels.add_to(m)
        
        # Add TAZ centroids for easier identification
        print("   Adding TAZ centroids...")
        centroid_layer = folium.FeatureGroup(name='TAZ Centroids', show=False)
        
        for idx, taz in taz_web.iterrows():
            centroid = taz.geometry.centroid
            
            # Get PUMA info for this TAZ if available
            taz_id = taz[self.taz_id_col]
            puma_info = "No PUMA data"
            if hasattr(self, 'taz_puma_summary'):
                taz_summary = self.taz_puma_summary[self.taz_puma_summary[self.taz_id_col] == taz_id]
                if not taz_summary.empty:
                    pumas = taz_summary.iloc[0][self.puma_id_col]
                    primary_puma = taz_summary.iloc[0]['primary_puma']
                    puma_info = f"Primary PUMA: {primary_puma}<br>All PUMAs: {', '.join(map(str, pumas))}"
            
            folium.CircleMarker(
                location=[centroid.y, centroid.x],
                radius=3,
                popup=folium.Popup(f"<b>TAZ {taz_id}</b><br>{puma_info}", parse_html=True),
                color='darkblue',
                fill=True,
                fillColor='lightblue',
                fillOpacity=0.7
            ).add_to(centroid_layer)
        
        centroid_layer.add_to(m)
        
        # Add detailed PUMA area analysis within TAZs
        if hasattr(self, 'taz_puma_summary'):
            print("   Adding PUMA area analysis within TAZs...")
            area_analysis_layer = folium.FeatureGroup(name='PUMA Areas in TAZs', show=False)
            
            # Create detailed analysis from the overlays
            if hasattr(self, 'detailed_overlays'):
                overlays_web = self.detailed_overlays.to_crs('EPSG:4326')
                
                for idx, overlap in overlays_web.iterrows():
                    taz_id = overlap[self.taz_id_col]
                    puma_id = overlap[self.puma_id_col]
                    area_sqm = overlap['overlap_area']
                    area_sqkm = area_sqm / 1_000_000
                    overlap_pct = overlap['overlap_pct']
                    
                    # Color code by overlap percentage
                    if overlap_pct >= 90:
                        color = 'green'
                        fill_color = 'lightgreen'
                    elif overlap_pct >= 50:
                        color = 'orange'
                        fill_color = 'lightyellow'
                    else:
                        color = 'red'
                        fill_color = 'lightcoral'
                    
                    folium.GeoJson(
                        overlap.geometry,
                        style_function=lambda x, color=color, fill_color=fill_color: {
                            'fillColor': fill_color,
                            'color': color,
                            'weight': 2,
                            'opacity': 0.8,
                            'fillOpacity': 0.3
                        },
                        popup=folium.Popup(
                            f"<b>TAZ {taz_id} ∩ PUMA {puma_id}</b><br>"
                            f"Area: {area_sqkm:.3f} km²<br>"
                            f"% of TAZ: {overlap_pct:.1f}%", 
                            parse_html=True
                        ),
                        tooltip=f"TAZ {taz_id} ∩ PUMA {puma_id}: {overlap_pct:.1f}%"
                    ).add_to(area_analysis_layer)
            
            area_analysis_layer.add_to(m)
        
        # Add layer control
        folium.LayerControl(collapsed=False).add_to(m)
        
        # Add title and instructions
        title_html = '''
        <div style="position: fixed; 
                    top: 10px; left: 50px; width: 450px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:13px; padding: 10px">
        <h4>TAZ-PUMA Spatial Analysis</h4>
        <p><b>Red lines:</b> PUMA boundaries (thick)<br>
           <b>Red labels:</b> PUMA IDs with areas<br>
           <b>Blue dotted:</b> TAZ boundaries<br>
           <b>Blue labels:</b> TAZ IDs with areas (toggle on/off)<br>
           <b>Blue dots:</b> TAZ centroids (click for PUMA info)<br>
           <b>Color areas:</b> PUMA portions within TAZs</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        # Save map
        map_file = self.output_dir / "taz_puma_interactive_map.html"
        m.save(str(map_file))
        print(f"   💾 Interactive map saved: {map_file}")
        
        return m
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        print("\n📄 Generating summary report...")
        
        report_lines = [
            "TAZ-PUMA SPATIAL ANALYSIS REPORT",
            "=" * 50,
            "",
            f"Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "DATA SOURCES:",
            f"• TAZ Shapefile: {self.taz_shapefile}",
            f"• PUMA Shapefile: {self.puma_shapefile}",
            "",
            "SPATIAL DATA SUMMARY:",
            f"• Total TAZ zones: {len(self.taz_gdf):,}",
            f"• Total PUMA zones (Bay Area): {len(self.puma_gdf):,}",
            f"• TAZ ID column: {self.taz_id_col}",
            f"• PUMA ID column: {self.puma_id_col}",
            f"• Coordinate system: {self.taz_gdf.crs}",
            ""
        ]
        
        if hasattr(self, 'taz_puma_summary'):
            unique_pumas = set([p for pumas in self.taz_puma_summary[self.puma_id_col] for p in pumas])
            
            report_lines.extend([
                "OVERLAP ANALYSIS RESULTS:",
                f"• TAZs with spatial overlaps: {len(self.taz_puma_summary):,}",
                f"• TAZs touching exactly 1 PUMA: {(self.taz_puma_summary['num_pumas'] == 1).sum():,}",
                f"• TAZs touching 2+ PUMAs: {(self.taz_puma_summary['num_pumas'] > 1).sum():,}",
                f"• Maximum PUMAs per TAZ: {self.taz_puma_summary['num_pumas'].max()}",
                f"• Unique PUMAs found in overlaps: {len(unique_pumas)}",
                "",
                "PUMA IDs FOUND IN SPATIAL OVERLAPS:",
                f"{sorted(unique_pumas)}",
                "",
                "EXPECTED vs ACTUAL PUMA COUNT:",
                f"• PUMAs in shapefile (Bay Area): {len(self.puma_gdf)}",
                f"• PUMAs found in TAZ overlaps: {len(unique_pumas)}",
                f"• Missing PUMAs: {len(self.puma_gdf) - len(unique_pumas)}",
                ""
            ])
            
            # Check for missing PUMAs
            all_puma_ids = set(self.puma_gdf[self.puma_id_col])
            missing_pumas = all_puma_ids - unique_pumas
            if missing_pumas:
                report_lines.extend([
                    "MISSING PUMA IDs (no TAZ overlaps):",
                    f"{sorted(missing_pumas)}",
                    ""
                ])
        
        report_lines.extend([
            "OUTPUT FILES:",
            f"• Interactive map: {self.output_dir}/taz_puma_interactive_map.html",
            f"• Detailed analysis: {self.output_dir}/taz_puma_detailed_analysis.csv",
            f"• Summary data: {self.output_dir}/taz_puma_summary.csv",
            f"• This report: {self.output_dir}/analysis_report.txt",
            "",
            "USAGE INSTRUCTIONS:",
            "1. Open the interactive map in a web browser",
            "2. Use layer controls to toggle TAZ/PUMA visibility",
            "3. Click on TAZ centroids to see PUMA assignments",
            "4. Review CSV files for detailed analysis",
            ""
        ])
        
        # Save report
        report_file = self.output_dir / "analysis_report.txt"
        with open(report_file, 'w') as f:
            f.write('\n'.join(report_lines))
        
        print(f"   💾 Report saved: {report_file}")
        
        # Print key findings to console
        print("\n🎯 KEY FINDINGS:")
        if hasattr(self, 'taz_puma_summary'):
            unique_pumas = set([p for pumas in self.taz_puma_summary[self.puma_id_col] for p in pumas])
            print(f"   • Found {len(unique_pumas)} PUMAs with TAZ overlaps")
            print(f"   • Expected {len(self.puma_gdf)} PUMAs in Bay Area")
            if len(unique_pumas) < len(self.puma_gdf):
                missing = len(self.puma_gdf) - len(unique_pumas)
                print(f"   ⚠️  {missing} PUMAs have no TAZ overlaps!")
        
    def run_analysis(self):
        """Run complete TAZ-PUMA analysis"""
        try:
            self.load_spatial_data()
            overlays = self.analyze_taz_puma_overlaps()
            
            if overlays is not None:
                self.create_interactive_map()
                self.generate_summary_report()
                
                print("\n✅ Analysis complete!")
                print(f"📁 Results saved to: {self.output_dir}")
                print(f"🗺️  Open the interactive map: {self.output_dir}/taz_puma_interactive_map.html")
            else:
                print("\n❌ Analysis failed due to no spatial overlaps")
                
        except Exception as e:
            print(f"\n❌ Analysis failed: {e}")
            raise

def main():
    """Main execution function"""
    visualizer = TAZPUMAVisualizer()
    visualizer.run_analysis()

if __name__ == "__main__":
    main()
