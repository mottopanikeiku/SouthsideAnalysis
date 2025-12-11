import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA
from typing import Tuple, List
from .config import PCA_VARIANCE, CLUSTERING_FEATURES

class FeatureEngineer:
    
    @staticmethod
    def calculate_rates(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        if 'emp_unemployed' in df.columns and 'emp_labor_force' in df.columns:
            df['pct_unemployed'] = df.apply(
                lambda x: x['emp_unemployed'] / x['emp_labor_force'] if x['emp_labor_force'] > 0 else 0, axis=1
            )

        if 'commute_public_transit' in df.columns and 'commute_total' in df.columns:
            df['pct_transit'] = df.apply(
                lambda x: x['commute_public_transit'] / x['commute_total'] if x['commute_total'] > 0 else 0, axis=1
            )

        if 'edu_bachelors' in df.columns and 'edu_total_over_25' in df.columns:
            df['pct_bachelors'] = df.apply(
                lambda x: x['edu_bachelors'] / x['edu_total_over_25'] if x['edu_total_over_25'] > 0 else 0, axis=1
            )
            
        pop_col = 'total_population'
        if pop_col in df.columns:
            for race_col, suffix in [('race_white', 'white'), ('race_black', 'black'), ('race_hispanic', 'hispanic')]:
                if race_col in df.columns:
                    df[f'pct_{suffix}'] = df.apply(
                        lambda x: x[race_col] / x[pop_col] if x[pop_col] > 0 else 0, axis=1
                    )
                    
        return df

    @staticmethod
    def prepare_features(df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        valid_features = [f for f in CLUSTERING_FEATURES if f in df.columns and df[f].notna().sum() > 0]
        
        if not valid_features:
            raise ValueError("No valid features found for clustering.")
            
        print(f"Using features: {valid_features}")
        X = df[valid_features].values
        
        imputer = SimpleImputer(strategy='median')
        X_imp = imputer.fit_transform(X)
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_imp)
        
        pca = PCA(n_components=PCA_VARIANCE)
        X_pca = pca.fit_transform(X_scaled)
        print(f"PCA reduced dimensions to {pca.n_components_} components (retaining {PCA_VARIANCE*100}% variance).")
        
        return X_pca, valid_features
