"""
This code extends the one you provided to handle **two separate time intervals** in the OHSOME API query
and avoid the previous "NameError: name 'row' is not defined". We now ensure `row` is used only inside 
the loop, and we merge data from multiple intervals into a single figure for each cell.

**CHANGES**:
1. We define a list of time intervals (two chunks) instead of using a single interval.
2. We created a helper function `query_ohsome_in_chunks` to handle multiple intervals for each cell.
3. We keep the `for idx, row in cells_of_interest.iterrows()` loop, but no longer reference `row` outside it.
4. We avoid the `NameError` by building the output file name using `row['id']` inside the loop.
5. Each cell is plotted in one figure that merges the data from all intervals.

You can adapt the time intervals or the filter as needed.
"""

import requests
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import os

# Path to the GeoJSON file
geojson_path = 'C:/Users/natha/OneDrive - ufpr.br/Doutorado UFPR/dados_IBGE/grade_1km_only_CWB_4674.geojson'

# Load the GeoJSON file and filter cells 523 and 557
gdf = gpd.read_file(geojson_path)
cells_of_interest = gdf[gdf['id'].isin([523, 557])]  # You can add [523, 557] if you want two cells

# OHSOME API endpoint and directory for saving figures
url = "https://api.ohsome.org/v1/contributions/count"
SAVE_DIRECTORY = "C:/Users/natha/OneDrive - ufpr.br/Doutorado UFPR/Doutorado Sanduíche/2024/osm-contribution-patterns-brazil/figs/CWB/test_CWB"
os.makedirs(SAVE_DIRECTORY, exist_ok=True)

print(f"Figures will be saved in: {SAVE_DIRECTORY}")

# We define **two** time intervals to avoid large queries, merging results later
time_intervals = [
    "2019-11-01/2020-02-01/P1D",  # first interval
    "2020-02-01/2021-05-01/P1D"   # second interval
]

# Filter for deletions only
contribution_type = "deletion"
# Additional filter can be customized below
filter_changesets = "highway=* or (building=* and addr:street!=*)"

def query_ohsome_in_chunks(geojson_str, intervals, base_url, contribution_type, ohsome_filter):
    """
    Queries the Ohsome API for multiple time intervals and returns a concatenated DataFrame.
    
    :param geojson_str: GeoJSON string for the filtered cells.
    :param intervals: List of time intervals, e.g. ["YYYY-MM-DD/YYYY-MM-DD/P1D", ...].
    :param base_url: Ohsome API endpoint, e.g. "https://api.ohsome.org/v1/contributions/count".
    :param contribution_type: e.g. "deletion", "creation".
    :param ohsome_filter: Additional filter string, e.g. "(highway=* or building=*)".
    :return: A pandas DataFrame combining data from all intervals.
    """
    frames = []
    for interval in intervals:
        print(f"\nQuerying interval: {interval}")
        params = {
            "bpolys": geojson_str,
            "time": interval,
            "contributionType": contribution_type,
            "filter": ohsome_filter
        }
        response = requests.post(base_url, data=params)
        if response.status_code == 200:
            data_json = response.json()
            partial_df = pd.DataFrame(data_json.get("result", []))
            frames.append(partial_df)
        else:
            print(f"Error {response.status_code}: {response.text}")

    if not frames:
        raise ValueError("No valid data returned for any interval.")
    
    # Concatenate partial DataFrames
    df_combined = pd.concat(frames, ignore_index=True)
    return df_combined

# Loop through each cell and query the OHSOME API for multiple intervals
for idx, row in cells_of_interest.iterrows():
    print(f"\nProcessing Cell ID: {row['id']}")
    cell_geojson_data = gpd.GeoDataFrame([row], columns=gdf.columns).to_json()

    df_merged = query_ohsome_in_chunks(
        geojson_str=cell_geojson_data,
        intervals=time_intervals,
        base_url=url,
        contribution_type=contribution_type,
        ohsome_filter=filter_changesets
    )

    # Convert timestamps to datetime
    if "fromTimestamp" in df_merged.columns:
        df_merged["fromTimestamp"] = pd.to_datetime(df_merged["fromTimestamp"])
        df_merged.rename(columns={"fromTimestamp": "timestamp"}, inplace=True)
    else:
        print("No 'fromTimestamp' column found. Possibly no data returned.")
        continue

    # Sort by timestamp
    df_merged.sort_values("timestamp", inplace=True)

    # Plot the deletions over time for the current cell (merged intervals)
    plt.figure(figsize=(10, 6))
    plt.plot(df_merged["timestamp"], df_merged["value"], marker='o', linestyle='-', label=f"Cell {row['id']}")
    plt.title(f"Number of Deletions (Merged intervals) - Cell {row['id']}")
    plt.xlabel("Date")
    plt.ylabel("Number of Deletions")
    plt.legend()
    plt.grid()

    # Save the figure
    output_path = os.path.join(SAVE_DIRECTORY, f"cell_{row['id']}_merged_deletions.png")
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Figure saved to: {output_path}")
