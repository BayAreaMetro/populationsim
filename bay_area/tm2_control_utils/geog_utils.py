import os
import pandas as pd
import requests
import re
from bs4 import BeautifulSoup


def read_ipums_api_key():
    with open(IPUMS_API_KEY_FILE) as f:
        return f.read().strip()

def add_aggregate_geography_colums(table_df):
    """
    Given a table with column GEOID_block, creates columns for GEOID_[county,tract,block group]
    """
    if "GEOID_block" in table_df.columns:
        table_df["GEOID_county"     ] = table_df["GEOID_block"].str[:5 ]
        table_df["GEOID_tract"      ] = table_df["GEOID_block"].str[:11]
        table_df["GEOID_block group"] = table_df["GEOID_block"].str[:12]

def fetch_nhgis_crosswalk(source_year, target_year, geography, download_dir, api_key=None):
    """
    Download the NHGIS geographic crosswalk CSV for the given source and target years
    and geography level into download_dir.
    """
    src = str(source_year)
    tgt = str(target_year)
    geo = geography.lower().replace(" ", "")
    
    # 1. Scrape the NHGIS crosswalks page
    page_url = "https://www.nhgis.org/geographic-crosswalks"
    resp = requests.get(page_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, 'html.parser')
    
    # 2. Find matching CSV link
    pattern = re.compile(rf"{src}.*{geo}.*{tgt}.*\.csv", re.IGNORECASE)
    links = [a['href'] for a in soup.find_all('a', href=True) if pattern.search(a['href'])]
    if not links:
        raise FileNotFoundError(f"No crosswalk link for {src} → {tgt} at {geo} level.")
    link = links[0]
    if link.startswith('/'):
        link = "https://secure-assets.ipums.org" + link
    download_url = link.replace(
        "https://secure-assets.ipums.org/nhgis/",
        "https://api.ipums.org/supplemental-data/nhgis/"
    )
    
    # 3. Download via IPUMS API
    headers = {}
    key = read_ipums_api_key()
    if not key:
        raise EnvironmentError("Set IPUMS_API_KEY env var or pass api_key.")
    headers["Authorization"] = key
    dl = requests.get(download_url, headers=headers)
    dl.raise_for_status()
    
    # 4. Save file
    os.makedirs(download_dir, exist_ok=True)
    fname = download_url.split("/")[-1]
    out_path = os.path.join(download_dir, fname)
    with open(out_path, "wb") as f:
        f.write(dl.content)
    
    return out_path

def interpolate_est(control_df, dataset, year, table, geo, target_geo_year, source_geo_year,
                    crosswalk_dir="nhgis_crosswalks", api_key=None):
    """
    Interpolate a control DataFrame from one geography vintage to another,
    fetching the NHGIS crosswalk if not already cached.
    """
    # Prepare names
    geo_name = geo.lower().replace(" ", "")
    fname = f"nhgis{source_geo_year}_{geo_name}_to_{geo_name}_{target_geo_year}.csv"
    cw_path = os.path.join(crosswalk_dir, fname)
    
    # Fetch if missing
    if not os.path.exists(cw_path):
        fetch_nhgis_crosswalk(source_year=source_geo_year,
                              target_year=target_geo_year,
                              geography=geo_name,
                              download_dir=crosswalk_dir,
                              api_key=api_key)
    
    # Load crosswalk
    cw = pd.read_csv(cw_path, dtype=str)
    cw["WEIGHT"] = cw["WEIGHT"].astype(float)
    
    # Identify source ID column
    possible = [c for c in control_df.columns if c.lower() in ("geoid", geo_name)]
    if not possible:
        raise ValueError(f"No source ID column matching '{geo}' in control_df")
    src_col = possible[0]
    
    # Merge & weight
    df = control_df.copy()
    df[src_col] = df[src_col].astype(str)
    merged = df.merge(cw, left_on=src_col, right_on="SOURCEID", how="inner")
    
    # Apply weights to numeric columns
    data_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c != src_col]
    for col in data_cols:
        merged[col] = merged[col] * merged["WEIGHT"]
    
    # Aggregate to target geography
    result = (merged
              .groupby("TARGETID")[data_cols]
              .sum()
              .reset_index()
              .rename(columns={"TARGETID": src_col}))
    
    return result