import requests
import geopandas as gpd
import pandas as pd
import numpy as np
import os
import concurrent.futures
import json
import time
from tqdm import tqdm  # For progress bars

# Configuration
CITIES_GRID_DIR = "grades_1km_por_cidade"
SAVE_DIRECTORY = "resultados"
TOP_CELLS_PER_CITY = 10
INTERVAL = "2018-11-01/2021-05-01/P1D"
MAX_WORKERS = 10
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Create directories
os.makedirs(SAVE_DIRECTORY, exist_ok=True)

# Create a global session for connection pooling
session = requests.Session()

# City GeoJSON files
CIDADES = [
    "grade_1km_Curitiba_4674.geojson",
    "grade_1km_São Paulo_4674.geojson",
    "grade_1km_Rio de Janeiro_4674.geojson",
    "grade_1km_Belo Horizonte_4674.geojson",
    "grade_1km_Porto Alegre_4674.geojson",
    "grade_1km_Florianópolis_4674.geojson",
    "grade_1km_Vitória_4674.geojson",
    "grade_1km_Guarulhos_4674.geojson",
    "grade_1km_Campinas_4674.geojson",
    "grade_1km_São Gonçalo_4674.geojson",
    "grade_1km_Duque de Caxias_4674.geojson"
]

def query_ohsome(geojson_str, interval, retry_count=0):
    """
    Query the OHSOME API with retry mechanism.
    Returns both grouped and total contribution data.
    """
    params = {
        "bpolys": geojson_str,
        "time": interval,
        "groupBy": "contributionType"
    }
    
    try:
        response = session.post("https://api.ohsome.org/v1/contributions/count", data=params, timeout=30)
        
        if response.status_code == 200:
            return response.json().get("result", [])
        elif response.status_code == 429 and retry_count < MAX_RETRIES:  # Rate limit
            time.sleep(RETRY_DELAY * (retry_count + 1))  # Exponential backoff
            return query_ohsome(geojson_str, interval, retry_count + 1)
        else:
            print(f"Error {response.status_code}: {response.text}")
            return []
            
    except requests.exceptions.RequestException as e:
        if retry_count < MAX_RETRIES:
            time.sleep(RETRY_DELAY * (retry_count + 1))
            return query_ohsome(geojson_str, interval, retry_count + 1)
        else:
            print(f"Request failed after {MAX_RETRIES} retries: {e}")
            return []

def extract_total(data):
    """Extract total contributions from OHSOME API response."""
    if not data:
        return 0
        
    try:
        # Sum contributions across all types (creation, modification, deletion)
        return sum([item["value"] for item in data 
                   if item.get("contributionType") in ["creation", "modification", "deletion"]])
    except (KeyError, TypeError):
        return 0

def calculate_cell_activity(row, interval, city_name):
    """Calculate activity for a single cell."""
    cell_id = row["id"]
    
    try:
        # Convert to EPSG:4326 for the API
        cell_gdf = gpd.GeoDataFrame([row], geometry=[row.geometry], crs="EPSG:4674").to_crs(epsg=4326)
        cell_geojson = cell_gdf.to_json()
        
        # Query the API
        result = query_ohsome(cell_geojson, interval)
        total_activity = extract_total(result)
        
        # Return tuple of id, activity count, and contribution details
        return (cell_id, total_activity, result)
        
    except Exception as e:
        print(f"Error processing cell {cell_id} in {city_name}: {str(e)}")
        return (cell_id, 0, [])

def process_city(cidade_geojson, interval=INTERVAL):
    """Process a single city to find top cells."""
    cidade_nome = cidade_geojson.split("_")[2]
    print(f"\nProcessing {cidade_nome}...")
    
    # Load and prepare the grid
    try:
        grid_path = os.path.join(CITIES_GRID_DIR, cidade_geojson)
        grade = gpd.read_file(grid_path)
        
        # Convert to EPSG:4326 once for the entire grid
        grade = grade.to_crs(epsg=4326)
        
        # Sample a subset of cells for testing if needed
        # grade = grade.sample(10)  # Uncomment for testing with fewer cells
        
        # Process all cells with concurrent execution
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Create a list of futures
            futures = {
                executor.submit(calculate_cell_activity, row, interval, cidade_nome): row["id"] 
                for _, row in grade.iterrows()
            }
            
            # Process results as they complete with a progress bar
            for future in tqdm(concurrent.futures.as_completed(futures), 
                              total=len(futures), 
                              desc=f"{cidade_nome} cells"):
                cell_id = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"Cell {cell_id} processing failed: {e}")
        
        # Convert results to DataFrame and sort
        df_activity = pd.DataFrame(
            [(id, total) for id, total, _ in results],
            columns=["id", "total_activity"]
        ).sort_values(by="total_activity", ascending=False)
        
        # Save detailed results for all cells
        df_activity.to_csv(os.path.join(SAVE_DIRECTORY, f"all_cells_{cidade_nome}.csv"), index=False)
        
        # Extract top cells and save as GeoJSON
        top_cells = df_activity.head(TOP_CELLS_PER_CITY)["id"].tolist()
        top_cells_gdf = grade[grade["id"].isin(top_cells)].copy()
        
        # Add activity data to the GeoDataFrame
        top_cells_gdf = top_cells_gdf.merge(df_activity, on="id", how="left")
        
        # Save the top cells
        output_path = os.path.join(SAVE_DIRECTORY, f"top_{TOP_CELLS_PER_CITY}_{cidade_nome}.geojson")
        top_cells_gdf.to_file(output_path, driver="GeoJSON")
        
        print(f"✅ Completed {cidade_nome}: Found {len(top_cells)} top cells")
        return top_cells_gdf
        
    except Exception as e:
        print(f"❌ Error processing city {cidade_nome}: {str(e)}")
        return None

def main():
    """Main execution function."""
    print(f"Starting analysis of {len(CIDADES)} cities...")
    
    # Process all cities
    results = {}
    for cidade_geojson in CIDADES:
        results[cidade_geojson] = process_city(cidade_geojson)
    
    print("\nAll cities processed successfully!")
    
    # Create a summary DataFrame
    summary_rows = []
    for cidade_geojson, gdf in results.items():
        if gdf is not None:
            cidade_nome = cidade_geojson.split("_")[2]
            total_activity = gdf["total_activity"].sum()
            avg_activity = gdf["total_activity"].mean()
            max_activity = gdf["total_activity"].max()
            
            summary_rows.append({
                "city": cidade_nome,
                "total_activity": total_activity,
                "average_activity": avg_activity,
                "max_activity": max_activity,
                "cells_processed": len(gdf)
            })
    
    # Save summary
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(os.path.join(SAVE_DIRECTORY, "cities_summary.csv"), index=False)
    print(f"\nSummary saved to {os.path.join(SAVE_DIRECTORY, 'cities_summary.csv')}")

if __name__ == "__main__":
    main()
