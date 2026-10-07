import os
import pandas as pd
from src.config import ACS_YEARS, OUTPUT_DIR
from src.data_loader import DataLoader
from src.features import FeatureEngineer
from src.network import NetworkAnalyzer
from src.visualization import Visualizer

def run_pipeline(year: int):
    print(f"\n{'='*30}\nStarting Pipeline for {year}\n{'='*30}")
    
    gdf = DataLoader.load_merged_data(year)
    ca_gdf = DataLoader.load_community_areas()
    
    if gdf is None:
        print(f"Skipping {year} due to missing data.")
        return

    if ca_gdf is not None and gdf.crs is not None:
        if ca_gdf.crs != gdf.crs:
            ca_gdf = ca_gdf.to_crs(gdf.crs)

    gdf = FeatureEngineer.calculate_rates(gdf)
    X_pca, valid_features = FeatureEngineer.prepare_features(gdf)
    
    print("Constructing Network Graph...")
    G, _ = NetworkAnalyzer.build_graph(X_pca, gdf.index, metric='cosine')
    
    print("Detecting Communities...")
    louvain_map, leiden_map, mod_louvain, mod_leiden = NetworkAnalyzer.detect_communities(G)
    print(f"Modularity -> Louvain: {mod_louvain:.4f} | Leiden: {mod_leiden:.4f}")
    
    weak_boundaries = NetworkAnalyzer.find_weak_boundaries(G, leiden_map)
    print(f"Identified {len(weak_boundaries)} weak boundary segments.")
    
    gdf['community_louvain'] = [louvain_map.get(i, -1) for i in range(len(gdf))]
    gdf['community_leiden'] = [leiden_map.get(i, -1) for i in range(len(gdf))]
    
    results_path = os.path.join(OUTPUT_DIR, f"results_{year}.csv")
    save_cols = ['GEOID', 'community_louvain', 'community_leiden'] + valid_features
    gdf[save_cols].to_csv(results_path, index=False)
    print(f"Saved tabular results to {results_path}")
    
    print("Generating visualizations...")
    
    pos = {i: (gdf.geometry.iloc[i].centroid.x, gdf.geometry.iloc[i].centroid.y) for i in range(len(gdf))}
    
    Visualizer.plot_community_maps(gdf, year, mod_louvain, mod_leiden, ca_gdf=ca_gdf)
    Visualizer.plot_network_graph(G, leiden_map, year, algorithm="Leiden", pos=pos)
    return gdf, G, {"louvain": mod_louvain, "leiden": mod_leiden}

def main():
    for year in ACS_YEARS:
        run_pipeline(year)
    print("\nPipeline Completed Successfully.")

if __name__ == "__main__":
    main()
