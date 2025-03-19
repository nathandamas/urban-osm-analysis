import requests
import geopandas as gpd
import pandas as pd
import numpy as np
import os
import concurrent.futures
import json
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime
import seaborn as sns
from tqdm import tqdm
import time

# Force non-interactive backend
matplotlib.use('Agg')

# Configuration
SAVE_DIRECTORY = "resultados"
VISUALIZATIONS_DIR = os.path.join(SAVE_DIRECTORY, "visualizations")
TOP_CELLS_PER_CITY = 10
MAX_WORKERS = 10
MAX_RETRIES = 3
RETRY_DELAY = 2

# Create directories
os.makedirs(VISUALIZATIONS_DIR, exist_ok=True)

# Create a global session
session = requests.Session()

# Cities to process
CIDADES = [
    "Curitiba",
    "São Paulo",
    "Rio de Janeiro",
    "Belo Horizonte",
    "Porto Alegre",
    "Florianópolis",
    "Vitória",
    "Guarulhos",
    "Campinas",
    "São Gonçalo",
    "Duque de Caxias"
]

def query_ohsome_timeseries(geojson_str, interval, retry_count=0):
    """Query OHSOME API for time series data."""
    params = {
        "bpolys": geojson_str,
        "time": interval,
        "groupBy": "contributionType"
    }
    
    try:
        response = session.post("https://api.ohsome.org/v1/contributions/count/groupBy/boundary", data=params, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429 and retry_count < MAX_RETRIES:  # Rate limit
            time.sleep(RETRY_DELAY * (retry_count + 1))
            return query_ohsome_timeseries(geojson_str, interval, retry_count + 1)
        else:
            print(f"Error {response.status_code}: {response.text}")
            return {}
            
    except requests.exceptions.RequestException as e:
        if retry_count < MAX_RETRIES:
            time.sleep(RETRY_DELAY * (retry_count + 1))
            return query_ohsome_timeseries(geojson_str, interval, retry_count + 1)
        else:
            print(f"Request failed after {MAX_RETRIES} retries: {e}")
            return {}

def extract_timeseries_data(response):
    """Extract time series data from OHSOME API response."""
    if not response or 'result' not in response:
        return pd.DataFrame()
    
    try:
        # Extract the time series data
        result = response['result']
        
        # Initialize lists to store data
        timestamps = []
        creations = []
        modifications = []
        deletions = []
        
        # Process each timestamp
        for feature in result['features']:
            for timestamp_data in feature['properties']['result']:
                timestamp = timestamp_data['timestamp']
                
                # Find values for each contribution type
                creation_val = 0
                modification_val = 0
                deletion_val = 0
                
                for group in timestamp_data['groups']:
                    if group['group'] == 'creation':
                        creation_val = group['value']
                    elif group['group'] == 'modification':
                        modification_val = group['value']
                    elif group['group'] == 'deletion':
                        deletion_val = group['value']
                
                timestamps.append(timestamp)
                creations.append(creation_val)
                modifications.append(modification_val)
                deletions.append(deletion_val)
        
        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': timestamps,
            'creation': creations,
            'modification': modifications,
            'deletion': deletions
        })
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Add total column
        df['total'] = df['creation'] + df['modification'] + df['deletion']
        
        return df
        
    except Exception as e:
        print(f"Error extracting time series data: {e}")
        return pd.DataFrame()

def plot_cell_activity(cell_id, cidade_nome):
    """Create visualizations for a specific cell."""
    print(f"Visualizing cell {cell_id} in {cidade_nome}...")
    
    # Create city directory if it doesn't exist
    cidade_dir = os.path.join(VISUALIZATIONS_DIR, cidade_nome)
    os.makedirs(cidade_dir, exist_ok=True)
    
    # Path to the top cells GeoJSON
    geojson_path = os.path.join(SAVE_DIRECTORY, f"top_{TOP_CELLS_PER_CITY}_{cidade_nome}.geojson")
    
    try:
        # Load the cell data
        cells_gdf = gpd.read_file(geojson_path)
        cell = cells_gdf[cells_gdf["id"] == cell_id]
        
        if cell.empty:
            print(f"⚠️ Cell {cell_id} not found in {cidade_nome}")
            return
        
        # Get total activity from the GeoJSON if available
        total_activity = cell["total_activity"].values[0] if "total_activity" in cell.columns else "N/A"
        
        # Create visualizations
        
        # 1. Basic total activity visualization
        plt.figure(figsize=(10, 6))
        plt.bar(['Total Activity'], [total_activity], color='royalblue')
        plt.title(f"Cell {cell_id} - {cidade_nome}: Total Activity", fontsize=14)
        plt.ylabel("Number of Contributions")
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(os.path.join(cidade_dir, f"cell_{cell_id}_total.png"), dpi=300)
        plt.close()
        
        # 2. Time series visualization (monthly)
        # Query for monthly data from 2018-11 to 2021-05
        response = query_ohsome_timeseries(
            cell.to_crs(epsg=4326).to_json(), 
            "2018-11-01/2021-05-01/P1M"
        )
        
        timeseries_df = extract_timeseries_data(response)
        
        if not timeseries_df.empty:
            # Generate time series plot
            plt.figure(figsize=(12, 8))
            
            # Plot each contribution type
            plt.plot(timeseries_df['timestamp'], timeseries_df['creation'], 
                     marker='o', linestyle='-', label='Creation', color='green')
            plt.plot(timeseries_df['timestamp'], timeseries_df['modification'], 
                     marker='s', linestyle='-', label='Modification', color='blue')
            plt.plot(timeseries_df['timestamp'], timeseries_df['deletion'], 
                     marker='^', linestyle='-', label='Deletion', color='red')
            plt.plot(timeseries_df['timestamp'], timeseries_df['total'], 
                     marker='D', linestyle='-', label='Total', color='purple', linewidth=2)
            
            plt.title(f"Monthly OSM Activity in Cell {cell_id} - {cidade_nome}", fontsize=14)
            plt.xlabel("Month")
            plt.ylabel("Number of Contributions")
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save the plot
            plt.savefig(os.path.join(cidade_dir, f"cell_{cell_id}_monthly.png"), dpi=300)
            plt.close()
            
            # Save the time series data
            timeseries_df.to_csv(os.path.join(cidade_dir, f"cell_{cell_id}_timeseries.csv"), index=False)
        
        # 3. Contribution type breakdown (pie chart)
        if not timeseries_df.empty:
            # Calculate totals by contribution type
            totals = {
                'Creation': timeseries_df['creation'].sum(),
                'Modification': timeseries_df['modification'].sum(),
                'Deletion': timeseries_df['deletion'].sum()
            }
            
            # Create pie chart
            plt.figure(figsize=(10, 8))
            plt.pie(
                totals.values(),
                labels=totals.keys(),
                autopct='%1.1f%%',
                startangle=90,
                colors=['green', 'blue', 'red']
            )
            plt.title(f"Contribution Type Distribution in Cell {cell_id} - {cidade_nome}", fontsize=14)
            plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            plt.tight_layout()
            plt.savefig(os.path.join(cidade_dir, f"cell_{cell_id}_types.png"), dpi=300)
            plt.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing cell {cell_id} in {cidade_nome}: {str(e)}")
        return False

def visualize_city_summary(cidade_nome):
    """Create a summary visualization for a city's top cells."""
    print(f"Creating summary visualization for {cidade_nome}...")
    
    # Path to the top cells GeoJSON
    geojson_path = os.path.join(SAVE_DIRECTORY, f"top_{TOP_CELLS_PER_CITY}_{cidade_nome}.geojson")
    
    try:
        # Load the cell data
        cells_gdf = gpd.read_file(geojson_path)
        
        if "total_activity" not in cells_gdf.columns:
            print(f"⚠️ No activity data found for {cidade_nome}")
            return
        
        # Sort by total activity
        cells_gdf = cells_gdf.sort_values(by="total_activity", ascending=False)
        
        # Create city directory if it doesn't exist
        cidade_dir = os.path.join(VISUALIZATIONS_DIR, cidade_nome)
        os.makedirs(cidade_dir, exist_ok=True)
        
        # Create bar chart of top cells
        plt.figure(figsize=(12, 8))
        bars = plt.bar(
            cells_gdf["id"].astype(str), 
            cells_gdf["total_activity"],
            color=sns.color_palette("viridis", len(cells_gdf))
        )
        
        # Add values on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width()/2.,
                height + 5,
                f'{int(height):,}',
                ha='center', va='bottom', rotation=0, fontsize=9
            )
        
        plt.title(f"Top {len(cells_gdf)} Most Active Cells in {cidade_nome}", fontsize=16)
        plt.xlabel("Cell ID", fontsize=12)
        plt.ylabel("Total Contributions", fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Save the chart
        plt.savefig(os.path.join(cidade_dir, f"{cidade_nome}_top_cells.png"), dpi=300)
        plt.close()
        
        # Create a map visualization using GeoPandas
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        
        # Plot base grid with low alpha
        cells_gdf.plot(
            ax=ax,
            color='lightgrey',
            edgecolor='grey',
            alpha=0.3
        )
        
        # Plot cells colored by activity
        cells_gdf.plot(
            column='total_activity',
            ax=ax,
            legend=True,
            cmap='viridis',
            legend_kwds={'label': "Total Contributions"},
            alpha=0.7
        )
        
        # Add cell IDs as labels
        for idx, row in cells_gdf.iterrows():
            plt.annotate(
                text=str(row['id']),
                xy=(row.geometry.centroid.x, row.geometry.centroid.y),
                ha='center',
                color='white',
                fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", fc="black", ec="none", alpha=0.7)
            )
        
        plt.title(f"Map of Top {len(cells_gdf)} Active Cells in {cidade_nome}", fontsize=16)
        plt.axis('off')
        plt.tight_layout()
        
        # Save the map
        plt.savefig(os.path.join(cidade_dir, f"{cidade_nome}_cells_map.png"), dpi=300)
        plt.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating summary for {cidade_nome}: {str(e)}")
        return False

def create_cities_comparison():
    """Create a comparison visualization of all cities."""
    print("Creating cities comparison visualization...")
    
    try:
        # Collect data for all cities
        city_data = []
        
        for cidade_nome in CIDADES:
            geojson_path = os.path.join(SAVE_DIRECTORY, f"top_{TOP_CELLS_PER_CITY}_{cidade_nome}.geojson")
            
            if not os.path.exists(geojson_path):
                print(f"⚠️ No data found for {cidade_nome}")
                continue
                
            # Load the cell data
            cells_gdf = gpd.read_file(geojson_path)
            
            if "total_activity" not in cells_gdf.columns:
                print(f"⚠️ No activity data found for {cidade_nome}")
                continue
            
            # Calculate total and average activity
            total_activity = cells_gdf["total_activity"].sum()
            avg_activity = cells_gdf["total_activity"].mean()
            max_activity = cells_gdf["total_activity"].max()
            
            city_data.append({
                "city": cidade_nome,
                "total_activity": total_activity,
                "avg_activity": avg_activity,
                "max_activity": max_activity
            })
        
        if not city_data:
            print("❌ No city data available for comparison")
            return
            
        # Create DataFrame
        cities_df = pd.DataFrame(city_data)
        
        # Sort by total activity
        cities_df = cities_df.sort_values(by="total_activity", ascending=False)
        
        # Create bar chart for total activity
        plt.figure(figsize=(14, 8))
        bars = plt.bar(
            cities_df["city"], 
            cities_df["total_activity"],
            color=sns.color_palette("viridis", len(cities_df))
        )
        
        # Add values on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width()/2.,
                height + 5,
                f'{int(height):,}',
                ha='center', va='bottom', rotation=0
            )
        
        plt.title("Total OSM Activity by City (Top Cells)", fontsize=16)
        plt.xlabel("City", fontsize=12)
        plt.ylabel("Total Contributions", fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Save the chart
        plt.savefig(os.path.join(VISUALIZATIONS_DIR, "cities_total_activity.png"), dpi=300)
        plt.close()
        
        # Create bar chart for max cell activity
        plt.figure(figsize=(14, 8))
        bars = plt.bar(
            cities_df["city"], 
            cities_df["max_activity"],
            color=sns.color_palette("mako", len(cities_df))
        )
        
        # Add values on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width()/2.,
                height + 5,
                f'{int(height):,}',
                ha='center', va='bottom', rotation=0
            )
        
        plt.title("Maximum Cell Activity by City", fontsize=16)
        plt.xlabel("City", fontsize=12)
        plt.ylabel("Contributions in Most Active Cell", fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Save the chart
        plt.savefig(os.path.join(VISUALIZATIONS_DIR, "cities_max_activity.png"), dpi=300)
        plt.close()
        
        # Save comparison data
        cities_df.to_csv(os.path.join(VISUALIZATIONS_DIR, "cities_comparison.csv"), index=False)
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating cities comparison: {str(e)}")
        return False

def main():
    """Main execution function."""
    print("Starting visualization process...")
    
    # Process all cities
    for cidade_nome in CIDADES:
        print(f"\nProcessing {cidade_nome}...")
        
        # Path to top cells file
        geojson_path = os.path.join(SAVE_DIRECTORY, f"top_{TOP_CELLS_PER_CITY}_{cidade_nome}.geojson")
        
        if not os.path.exists(geojson_path):
            print(f"❌ File not found: {geojson_path}")
            continue
            
        # Create city summary visualization
        visualize_city_summary(cidade_nome)
        
        # Load top cells
        try:
            cells_gdf = gpd.read_file(geojson_path)
            
            # Process each cell concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                cell_ids = cells_gdf["id"].tolist()
                futures = [executor.submit(plot_cell_activity, cell_id, cidade_nome) for cell_id in cell_ids]
                
                # Process results with progress bar
                for future in tqdm(concurrent.futures.as_completed(futures), 
                                  total=len(futures), 
                                  desc=f"{cidade_nome} cells"):
                    # Results are processed in the plot_cell_activity function
                    pass
                    
            print(f"✅ Completed visualization for {cidade_nome}")
            
        except Exception as e:
            print(f"❌ Error processing {cidade_nome}: {str(e)}")
    
    # Create cities comparison
    create_cities_comparison()
    
    print("\nVisualization process completed!")

if __name__ == "__main__":
    main()
