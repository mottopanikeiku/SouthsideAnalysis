import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA
from typing import Tuple, List
from .config import PCA_VARIANCE, CLUSTERING_FEATURES, ACS_VAR_MAP

class FeatureEngineer:
    
    @staticmethod
    def calculate_rates(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        # Every selected ACS estimate is a nonnegative count, median or age.
        # Negative Census annotation codes are missing, not measured values.
        estimate_columns = [column for column in ACS_VAR_MAP.values() if column in df.columns]
        df[estimate_columns] = df[estimate_columns].mask(df[estimate_columns] < 0)

        rates = [
            ('emp_unemployed', 'emp_labor_force', 'pct_unemployed'),
            ('commute_public_transit', 'commute_total', 'pct_transit'),
            ('edu_bachelors', 'edu_total_over_25', 'pct_bachelors'),
            ('race_white', 'total_population', 'pct_white'),
            ('race_black', 'total_population', 'pct_black'),
            ('race_hispanic', 'total_population', 'pct_hispanic'),
        ]
        for numerator, denominator, rate in rates:
            if numerator in df.columns and denominator in df.columns:
                known = df[numerator].notna() & df[denominator].notna()
                df[rate] = np.nan
                positive = known & (df[denominator] > 0)
                df.loc[positive, rate] = df.loc[positive, numerator] / df.loc[positive, denominator]
                # Retain the original zero-denominator convention, but never
                # turn a missing denominator into an observed zero rate.
                df.loc[known & (df[denominator] == 0), rate] = 0.0
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
