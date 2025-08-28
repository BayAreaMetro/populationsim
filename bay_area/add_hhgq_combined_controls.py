USAGE=r"""
Modify controls slightly for populationsim.

Mostly, this amounts to making group quarters into one-person households.

For TM1: 
  Input:  hh_gq/data/taz_summaries.csv
  Output: hh_gq/data/taz_summaries_hhgq.csv

For TM2:
  Input:  hh_gq/data/maz_marginals.csv
  Output: hh_gq/data/maz_marginals_hhgq.csv

"""

import argparse
import numpy
import pandas
import pathlib
import sys

if __name__ == '__main__':
    pandas.options.display.width    = 180
    pandas.options.display.max_rows = 1000

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=USAGE)
    parser.add_argument("--model_type", choices=['TM1','TM2'], required=True, help="Model type - one of TM1 or TM2")
    parser.add_argument("--input_dir", type=str, help="Input directory containing control files (default: auto-detect)")
    parser.add_argument("--output_dir", type=str, help="Output directory for HHGQ files (default: auto-detect)")
    args = parser.parse_args()

    # Set up directories
    if args.input_dir:
        input_dir = pathlib.Path(args.input_dir)
    else:
        input_dir = pathlib.Path("output_2023")  # Default
    
    if args.output_dir:
        output_dir = pathlib.Path(args.output_dir)
    else:
        output_dir = pathlib.Path("hh_gq/tm2_working_dir/data")  # Default

    if args.model_type == 'TM1':
        # control files are: 
        #  - [run_num]_taz_summaries_[year].csv
        taz_controls_file = input_dir / "taz_summaries.csv"
        taz_controls_df   = pandas.read_csv(taz_controls_file)
        print("Read {} controls from {}".format(len(taz_controls_df), taz_controls_file))

        # lowercase these fields
        field_list = ['hh_size_1','hh_size_2','hh_size_3','hh_size_4_plus',
          'hh_wrks_0','hh_wrks_1','hh_wrks_2','hh_wrks_3_plus',
          'gq_type_univ','gq_type_mil','gq_type_othnon','gq_tot_pop'
        ]
        rename_dict = { field.upper():field for field in field_list }
        taz_controls_df.rename(columns=rename_dict, inplace=True)
        print(taz_controls_df.dtypes)

        # total households: combine actual tothh + gq_tot_pop
        taz_controls_df["numhh_gq"] = taz_controls_df.TOTHH + taz_controls_df.gq_tot_pop
        # GQ are 1-person households
        taz_controls_df["hh_size_1_gq"] = taz_controls_df.hh_size_1 + taz_controls_df.gq_tot_pop

        # note that hh_wrks and hh_inc categories specify households.TYPE==1 so no need to modify those

        taz_controls_output = output_dir / "taz_summaries_hhgq.csv"
        taz_controls_df.to_csv(taz_controls_output, index=False)
        print("Wrote {}".format(taz_controls_output))

        # small update to county controls file
        county_controls_file = input_dir / "county_marginals.csv"
        county_controls_df   = pandas.read_csv(county_controls_file, index_col=0)
        print(f"Read county controls from {county_controls_file}")
        # print(county_controls_df)
        # for base years, COUNTY is present. for BAUS, county_name is present
        county_col = 'county_name'
        if county_controls_df.index.name == 'COUNTY':
            county_col = 'COUNTY'

        # add COUNTY or county_name depending on which is mmissing
        geo_crosswalk_file = input_dir / "geo_cross_walk_tm1.csv"
        geo_crosswalk_df   = pandas.read_csv(geo_crosswalk_file)
        geo_crosswalk_df = geo_crosswalk_df[['COUNTY','county_name']].drop_duplicates().reset_index(drop=True)
        # print(geo_crosswalk_df)

        county_controls_df = pandas.merge(
          left = county_controls_df,
          right = geo_crosswalk_df,
          left_index = True,
          right_on = county_col,
          how = 'left'
        )
        # how it has columns, COUNTY and county_name
        print(county_controls_df)
        county_controls_df.to_csv(county_controls_file, index=False)
        print(f"Wrote {county_controls_file}")

    elif args.model_type == 'TM2':
        print("\n" + "="*60)
        print("PROCESSING TM2 MODEL")
        print("="*60)
        
        maz_controls_file = input_dir / "maz_marginals.csv"
        maz_controls_df   = pandas.read_csv(maz_controls_file)
        print("Read {} MAZ controls from {}".format(len(maz_controls_df), maz_controls_file))
        print("MAZ columns:", list(maz_controls_df.columns))
        print("MAZ data types:")
        print(maz_controls_df.dtypes)
        print("\nMAZ sample data:")
        print(maz_controls_df.head())

        # total households: combine actual tothh + gq_tot_pop
        print("\n--- PROCESSING MAZ CONTROLS ---")
        
        # Check for different possible household column names
        household_cols = [col for col in maz_controls_df.columns if 'hh' in col.lower() or 'household' in col.lower()]
        print(f"Available household-related columns: {household_cols}")
        
        # Try to find the correct household column
        if 'num_hh' in maz_controls_df.columns:
            hh_col = 'num_hh'
        elif 'tothh' in maz_controls_df.columns:
            hh_col = 'tothh'
        elif len(household_cols) > 0:
            hh_col = household_cols[0]
            print(f"Using {hh_col} as household column")
        else:
            raise ValueError(f"No household column found in MAZ controls. Available columns: {list(maz_controls_df.columns)}")
        
        # Check for group quarters column
        gq_cols = [col for col in maz_controls_df.columns if 'gq' in col.lower()]
        print(f"Available group quarters columns: {gq_cols}")
        
        if 'gq_pop' in maz_controls_df.columns:
            gq_col = 'gq_pop'
        elif len(gq_cols) > 0:
            gq_col = gq_cols[0]
            print(f"Using {gq_col} as group quarters column")
        else:
            print("No group quarters column found, using 0")
            maz_controls_df['gq_pop'] = 0
            gq_col = 'gq_pop'
        
        print(f"MAZ {hh_col} stats: min={maz_controls_df[hh_col].min()}, max={maz_controls_df[hh_col].max()}, sum={maz_controls_df[hh_col].sum():,.0f}")
        print(f"MAZ {gq_col} stats: min={maz_controls_df[gq_col].min()}, max={maz_controls_df[gq_col].max()}, sum={maz_controls_df[gq_col].sum():,.0f}")
        maz_controls_df["numhh_gq"] = maz_controls_df[hh_col] + maz_controls_df[gq_col]
        print(f"MAZ numhh_gq stats: min={maz_controls_df.numhh_gq.min()}, max={maz_controls_df.numhh_gq.max()}, sum={maz_controls_df.numhh_gq.sum():,.0f}")
        
        # Note: hh_size_1 is not in MAZ controls, it's in TAZ controls
        # So we don't add hh_size_1_gq here - it will be handled at TAZ level
        print("Note: hh_size_1 controls will be handled at TAZ level")

        # note that hh_wrks and hh_inc categories specify households.TYPE==1 so no need to modify those
        print("Note: hh_wrks and hh_inc categories already specify households.TYPE==1")

        maz_controls_output = output_dir / "maz_marginals_hhgq.csv"
        maz_controls_df.to_csv(maz_controls_output, index=False)
        print("Wrote MAZ controls to {}".format(maz_controls_output))

        # Also process TAZ controls for household size adjustments
        print("\n" + "-"*60)
        print("PROCESSING TAZ CONTROLS")
        print("-"*60)
        taz_controls_file = input_dir / "taz_marginals.csv"
        taz_controls_df   = pandas.read_csv(taz_controls_file)
        print("Read {} TAZ controls from {}".format(len(taz_controls_df), taz_controls_file))
        print("TAZ columns:", list(taz_controls_df.columns))
        print("TAZ data types:")
        print(taz_controls_df.dtypes)
        print("\nTAZ sample data:")
        print(taz_controls_df.head())
        
        # Calculate total households for TAZ (sum of all household size categories)
        print("\n--- CALCULATING TAZ HOUSEHOLD TOTALS ---")
        household_size_cols = [col for col in taz_controls_df.columns if col.startswith('hh_size_')]
        print(f"Found household size columns: {household_size_cols}")
        
        if household_size_cols:
            print("Using household size columns to calculate numhh_gq")
            for col in household_size_cols:
                print(f"  {col}: min={taz_controls_df[col].min()}, max={taz_controls_df[col].max()}, sum={taz_controls_df[col].sum():,.0f}")
            taz_controls_df["numhh_gq"] = taz_controls_df[household_size_cols].sum(axis=1)
            print(f"Initial TAZ numhh_gq from hh_size: min={taz_controls_df['numhh_gq'].min()}, max={taz_controls_df['numhh_gq'].max()}, sum={taz_controls_df['numhh_gq'].sum():,.0f}")
        else:
            # Fallback: try to sum household income categories
            household_income_cols = [col for col in taz_controls_df.columns if col.startswith('hh_inc_')]
            print(f"No hh_size columns found. Trying household income columns: {household_income_cols}")
            if household_income_cols:
                print("Using household income columns to calculate numhh_gq")
                for col in household_income_cols:
                    print(f"  {col}: min={taz_controls_df[col].min()}, max={taz_controls_df[col].max()}, sum={taz_controls_df[col].sum():,.0f}")
                taz_controls_df["numhh_gq"] = taz_controls_df[household_income_cols].sum(axis=1)
                print(f"TAZ numhh_gq from hh_inc: min={taz_controls_df['numhh_gq'].min()}, max={taz_controls_df['numhh_gq'].max()}, sum={taz_controls_df['numhh_gq'].sum():,.0f}")
            else:
                # Last resort: try worker categories
                household_worker_cols = [col for col in taz_controls_df.columns if col.startswith('hh_wrks_')]
                print(f"No hh_inc columns found. Trying household worker columns: {household_worker_cols}")
                if household_worker_cols:
                    print("Using household worker columns to calculate numhh_gq")
                    for col in household_worker_cols:
                        print(f"  {col}: min={taz_controls_df[col].min()}, max={taz_controls_df[col].max()}, sum={taz_controls_df[col].sum():,.0f}")
                    taz_controls_df["numhh_gq"] = taz_controls_df[household_worker_cols].sum(axis=1)
                    print(f"TAZ numhh_gq from hh_wrks: min={taz_controls_df['numhh_gq'].min()}, max={taz_controls_df['numhh_gq'].max()}, sum={taz_controls_df['numhh_gq'].sum():,.0f}")
                else:
                    print("WARNING: Could not determine total households for TAZ - setting numhh_gq to 0")
                    taz_controls_df["numhh_gq"] = 0
        
        # Need to add GQ population to 1-person households at TAZ level
        # Sum GQ population by TAZ from MAZ level
        print("\n--- PROCESSING GROUP QUARTERS INTEGRATION ---")
        print("Checking if TAZ column exists in MAZ data...")
        if 'TAZ' in maz_controls_df.columns:
            print("TAZ column found in MAZ data - proceeding with GQ aggregation")
            maz_gq_by_taz = maz_controls_df.groupby('TAZ')['gq_pop'].sum().reset_index()
            print(f"Aggregated GQ by TAZ: {len(maz_gq_by_taz)} TAZ zones")
            print(f"GQ population stats: min={maz_gq_by_taz['gq_pop'].min()}, max={maz_gq_by_taz['gq_pop'].max()}, sum={maz_gq_by_taz['gq_pop'].sum():,.0f}")
            
            # Show sample of GQ by TAZ
            print("Sample GQ by TAZ:")
            print(maz_gq_by_taz.head(10))
        else:
            print("TAZ column NOT found in MAZ data - skipping GQ aggregation")
            maz_gq_by_taz = None
        
        if maz_gq_by_taz is not None:
            print("Merging GQ population with TAZ controls...")
            print(f"TAZ controls before merge: {len(taz_controls_df)} rows")
            print(f"GQ by TAZ: {len(maz_gq_by_taz)} rows")
            
            taz_controls_df = taz_controls_df.merge(maz_gq_by_taz, on='TAZ', how='left')
            print(f"TAZ controls after merge: {len(taz_controls_df)} rows")
            
            # Check for missing GQ data
            missing_gq = taz_controls_df['gq_pop'].isna().sum()
            print(f"TAZ zones with missing GQ data: {missing_gq}")
            
            taz_controls_df['gq_pop'] = taz_controls_df['gq_pop'].fillna(0)
            print(f"Filled missing GQ values with 0")
            print(f"Final GQ population stats: min={taz_controls_df['gq_pop'].min()}, max={taz_controls_df['gq_pop'].max()}, sum={taz_controls_df['gq_pop'].sum():,.0f}")
            
            # Check hh_size_1 column exists
            if 'hh_size_1' in taz_controls_df.columns:
                print(f"hh_size_1 stats before GQ: min={taz_controls_df['hh_size_1'].min()}, max={taz_controls_df['hh_size_1'].max()}, sum={taz_controls_df['hh_size_1'].sum():,.0f}")
                taz_controls_df["hh_size_1_gq"] = taz_controls_df.hh_size_1 + taz_controls_df.gq_pop
                print(f"hh_size_1_gq stats after GQ: min={taz_controls_df['hh_size_1_gq'].min()}, max={taz_controls_df['hh_size_1_gq'].max()}, sum={taz_controls_df['hh_size_1_gq'].sum():,.0f}")
            else:
                print("ERROR: hh_size_1 column not found in TAZ controls!")
                taz_controls_df["hh_size_1_gq"] = taz_controls_df.gq_pop
            
            # Also add GQ to total household count
            print(f"numhh_gq before adding GQ: min={taz_controls_df['numhh_gq'].min()}, max={taz_controls_df['numhh_gq'].max()}, sum={taz_controls_df['numhh_gq'].sum():,.0f}")
            taz_controls_df["numhh_gq"] = taz_controls_df["numhh_gq"] + taz_controls_df.gq_pop
            print(f"numhh_gq after adding GQ: min={taz_controls_df['numhh_gq'].min()}, max={taz_controls_df['numhh_gq'].max()}, sum={taz_controls_df['numhh_gq'].sum():,.0f}")
            
            # Clean up temporary column
            taz_controls_df.drop('gq_pop', axis=1, inplace=True)
            print("Dropped temporary gq_pop column")
        else:
            # If no TAZ column in MAZ data, assume no GQ adjustment needed
            print("No GQ adjustment - using original hh_size_1 values")
            if 'hh_size_1' in taz_controls_df.columns:
                taz_controls_df["hh_size_1_gq"] = taz_controls_df.hh_size_1
                print(f"hh_size_1_gq = hh_size_1: min={taz_controls_df['hh_size_1_gq'].min()}, max={taz_controls_df['hh_size_1_gq'].max()}, sum={taz_controls_df['hh_size_1_gq'].sum():,.0f}")
            else:
                print("ERROR: hh_size_1 column not found and no GQ data available!")
                taz_controls_df["hh_size_1_gq"] = 0

        print(f"TAZ numhh_gq total: {taz_controls_df['numhh_gq'].sum():,.0f}")
        
        # Data quality checks
        print("\n--- FINAL DATA QUALITY CHECKS ---")
        print(f"TAZ zones processed: {len(taz_controls_df)}")
        
        # Check for zero population zones
        age_cols = [col for col in taz_controls_df.columns if col.startswith('pers_age_')]
        if age_cols:
            print(f"Age columns found: {age_cols}")
            taz_controls_df['total_population'] = taz_controls_df[age_cols].sum(axis=1)
            zero_pop_count = (taz_controls_df['total_population'] == 0).sum()
            print(f"Zones with zero population: {zero_pop_count}")
            if zero_pop_count > 0:
                zero_pop_tazs = taz_controls_df[taz_controls_df['total_population'] == 0]['TAZ'].tolist()
                print(f"Zero population TAZ IDs: {zero_pop_tazs[:10]}{'...' if len(zero_pop_tazs) > 10 else ''}")
            taz_controls_df.drop('total_population', axis=1, inplace=True)
        
        # Check for zero household zones
        zero_hh_count = (taz_controls_df['numhh_gq'] == 0).sum()
        print(f"Zones with zero households: {zero_hh_count}")
        if zero_hh_count > 0:
            zero_hh_tazs = taz_controls_df[taz_controls_df['numhh_gq'] == 0]['TAZ'].tolist()
            print(f"Zero household TAZ IDs: {zero_hh_tazs[:10]}{'...' if len(zero_hh_tazs) > 10 else ''}")
        
        # Check for NaN values
        nan_cols = []
        for col in taz_controls_df.columns:
            nan_count = taz_controls_df[col].isna().sum()
            if nan_count > 0:
                nan_cols.append(f"{col}({nan_count})")
        if nan_cols:
            print(f"Columns with NaN values: {', '.join(nan_cols)}")
        else:
            print("No NaN values detected")
        
        # Final column summary
        print(f"Final TAZ file columns: {list(taz_controls_df.columns)}")
        print(f"Key statistics:")
        print(f"  numhh_gq: min={taz_controls_df['numhh_gq'].min()}, max={taz_controls_df['numhh_gq'].max()}, sum={taz_controls_df['numhh_gq'].sum():,.0f}")
        if 'hh_size_1_gq' in taz_controls_df.columns:
            print(f"  hh_size_1_gq: min={taz_controls_df['hh_size_1_gq'].min()}, max={taz_controls_df['hh_size_1_gq'].max()}, sum={taz_controls_df['hh_size_1_gq'].sum():,.0f}")
        
        taz_controls_output = output_dir / "taz_marginals_hhgq.csv"
        taz_controls_df.to_csv(taz_controls_output, index=False)
        print("Wrote TAZ controls to {}".format(taz_controls_output))
        print("=" * 60)
