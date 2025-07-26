"""
Example integration of TAZ mapping into control generation workflow.

Add this to the end of your control generation script to automatically
create maps after generating TAZ marginals.
"""

def create_maps_after_controls():
    """
    Example function to integrate mapping into control generation workflow.
    Call this after generating your TAZ marginals CSV file.
    """
    try:
        # Import mapping functionality
        from taz_mapper import TAZMapper
        from config import ENABLE_TAZ_MAPPING
        
        if not ENABLE_TAZ_MAPPING:
            print("TAZ mapping is disabled. Set ENABLE_TAZ_MAPPING = True in config.py to enable.")
            return
            
        print("\n" + "="*60)
        print("CREATING TAZ CONTROL MAPS")
        print("="*60)
        
        # Initialize mapper
        mapper = TAZMapper()
        
        # Create all maps
        mapper.create_all_maps()
        
        print("\nMap creation completed successfully!")
        print(f"Maps saved to: {mapper.output_dir}")
        print("Open 'taz_controls_dashboard.html' to view interactive dashboard")
        
    except ImportError:
        print("Mapping dependencies not installed. Run:")
        print("pip install -r tm2_control_utils/mapping_requirements.txt")
    except Exception as e:
        print(f"Warning: Could not create maps - {str(e)}")
        print("Maps are optional. Control generation was successful.")


# Example of how to add to your existing script:
if __name__ == "__main__":
    # Your existing code here...
    # generate_controls()
    # save_taz_marginals()
    
    # Add mapping at the end
    create_maps_after_controls()
