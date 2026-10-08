import os
from shapely.geometry import box

DATA_DIR = "data"
OUTPUT_DIR = "output"

for d in [DATA_DIR, OUTPUT_DIR]:
    os.makedirs(d, exist_ok=True)

SOUTH_SIDE_BBOX = box(-87.75, 41.644, -87.52, 41.867)
RANDOM_SEED = 42
PCA_VARIANCE = 0.90
KNN_K = 8
WEAK_BOUNDARY_THRESHOLD = 0.8

ACS_YEARS = [2019, 2022]

ACS_VAR_MAP = {
    'B19013_001E': 'median_household_income',
    'B15003_022E': 'edu_bachelors',
    'B15003_001E': 'edu_total_over_25',
    'B03002_003E': 'race_white',
    'B03002_004E': 'race_black',
    'B03002_012E': 'race_hispanic',
    'B01001_001E': 'total_population',
    'B23025_005E': 'emp_unemployed',
    'B23025_002E': 'emp_labor_force',
    'B08301_001E': 'commute_total',
    'B08301_010E': 'commute_public_transit',
    'B25077_001E': 'median_housing_value',
    'B01002_001E': 'median_age'
}

CLUSTERING_FEATURES = [
    'median_household_income', 
    'median_housing_value', 
    'median_age', 
    'pct_unemployed', 
    'pct_transit', 
    'pct_bachelors', 
    'pct_white', 
    'pct_black', 
    'pct_hispanic'
]
