import os
import pandas as pd
import geopandas as gpd
from typing import Optional, Tuple
from .config import DATA_DIR, SOUTH_SIDE_BBOX

class DataLoader:
    
    @staticmethod
    def load_acs_data(year: int) -> Optional[pd.DataFrame]:
        path = os.path.join(DATA_DIR, f"acs_{year}_cook_blockgroups.csv")
        if not os.path.exists(path):
            print(f"Error: ACS data file not found at {path}")
            return None
        
        df = pd.read_csv(path)
        if 'GEOID' in df.columns:
            df['GEOID'] = df['GEOID'].astype(str)
        return df

    @staticmethod
    def load_shapefile() -> Optional[gpd.GeoDataFrame]:
        path = os.path.join(DATA_DIR, "tl_2023_17_bg", "tl_2023_17_bg.shp")
        if not os.path.exists(path):
            path = os.path.join(DATA_DIR, "tl_2023_17_bg.shp")
            if not os.path.exists(path):
                print(f"Error: Shapefile not found at {path}")
                return None
        
        gdf = gpd.read_file(path)
        gdf = gdf[gdf['COUNTYFP'] == '031']
        return gdf

    @staticmethod
    def load_community_areas() -> Optional[gpd.GeoDataFrame]:
        candidates = [
            os.path.join(DATA_DIR, "cca_shp", "Boundaries - Community Areas (current).geojson"),
            os.path.join(DATA_DIR, "cca_shp", "Boundaries - Community Areas (current).shp"),
            os.path.join(DATA_DIR, "Boundaries - Community Areas (current).geojson"),
            os.path.join(DATA_DIR, "Boundaries - Community Areas (current).shp")
        ]
        
        for path in candidates:
            if os.path.exists(path):
                try:
                    gdf = gpd.read_file(path)
                    return gdf
                except Exception as e:
                    print(f"Error loading CA shapefile at {path}: {e}")
        
        print("Warning: Community Areas shapefile not found. Visualization will lack boundaries.")
        return None

    @classmethod
    def load_merged_data(cls, year: int) -> Optional[gpd.GeoDataFrame]:
        df = cls.load_acs_data(year)
        gdf = cls.load_shapefile()
        
        if df is None or gdf is None:
            return None
            
        gdf['GEOID'] = gdf['GEOID'].astype(str)
        
        south_gdf = gdf[gdf.intersects(SOUTH_SIDE_BBOX)].copy()
        
        if 'ALAND' in south_gdf.columns:
            south_gdf = south_gdf[south_gdf['ALAND'] > 0]
            
        merged = pd.merge(south_gdf, df, on='GEOID', how='inner')
        print(f"[{year}] Loaded {len(merged)} block groups after filtering.")
        
        return merged
