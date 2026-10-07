"""Rerun the old missing-value behavior and its correction on identical inputs.

Run from the repository root: python -m tools.compare_missing_values
The old outputs are retained separately under output/historical/.
"""
import json
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

from main import run_pipeline
from src.config import ACS_VAR_MAP, ACS_YEARS, KNN_K, PCA_VARIANCE, RANDOM_SEED
from src.data_loader import DataLoader
from src.features import FeatureEngineer
from src.network import NetworkAnalyzer


def original_rates(frame):
    """The pre-fix rate calculation, retained only for this comparison."""
    frame = frame.copy()
    rates = [
        ('emp_unemployed', 'emp_labor_force', 'pct_unemployed'),
        ('commute_public_transit', 'commute_total', 'pct_transit'),
        ('edu_bachelors', 'edu_total_over_25', 'pct_bachelors'),
        ('race_white', 'total_population', 'pct_white'),
        ('race_black', 'total_population', 'pct_black'),
        ('race_hispanic', 'total_population', 'pct_hispanic'),
    ]
    for numerator, denominator, rate in rates:
        if numerator in frame.columns and denominator in frame.columns:
            frame[rate] = frame.apply(
                lambda row: row[numerator] / row[denominator] if row[denominator] > 0 else 0,
                axis=1,
            )
    return frame


def svg_path(geometry, left, top):
    polygons = [geometry] if geometry.geom_type == 'Polygon' else geometry.geoms
    pieces = []
    for polygon in polygons:
        for ring in [polygon.exterior, *polygon.interiors]:
            points = [(x - left, top - y) for x, y in ring.coords]
            pieces.append('M' + 'L'.join(f'{x:.1f},{y:.1f}' for x, y in points) + 'Z')
    return ''.join(pieces)


def main():
    destination = Path('results/before_after')
    destination.mkdir(parents=True, exist_ok=True)
    report = {
        'comparison': 'Same input rows, dependencies, feature settings and seeds; only negative ACS estimate handling changes.',
        'seed': RANDOM_SEED,
        'knn_k': KNN_K,
        'pca_variance': PCA_VARIANCE,
        'objectives': {'louvain': 'weighted modularity', 'leiden': 'unweighted modularity'},
        'limitations': [
            'Historical outputs used an unrecorded Leiden seed and dependencies; the controlled pre-fix run is not an exact reconstruction of those outputs.',
            'Each modularity is evaluated on its own graph; a change is not proof of better neighborhoods.',
            'ACS years are joined to 2023 TIGER boundaries by GEOID without a crosswalk.',
            'Community identifiers and colors are arbitrary and not aligned between years or algorithms.',
            'Zero denominators retain the original zero-rate convention to isolate the missing-code correction.',
        ],
        'versions': {package: version(package) for package in ['numpy', 'pandas', 'scikit-learn', 'networkx', 'igraph', 'leidenalg', 'geopandas']},
        'years': {},
    }
    map_data = {'years': {}}
    map_frames = {}
    for year in ACS_YEARS:
        raw = DataLoader.load_merged_data(year)
        if raw is None:
            raise FileNotFoundError(f'Missing inputs for {year}')
        estimate_columns = [column for column in ACS_VAR_MAP.values() if column in raw.columns]
        negative = raw[estimate_columns] < 0
        before = original_rates(raw)
        before_features, _ = FeatureEngineer.prepare_features(before)
        before_graph, _ = NetworkAnalyzer.build_graph(before_features, before.index)
        louvain, leiden, louvain_mod, leiden_mod = NetworkAnalyzer.detect_communities(before_graph)
        before['community_louvain'] = [louvain[i] for i in range(len(before))]
        before['community_leiden'] = [leiden[i] for i in range(len(before))]
        before[['GEOID', 'community_louvain', 'community_leiden']].to_csv(destination / f'pre_fix_{year}.csv', index=False)
        after, after_graph, after_modularities = run_pipeline(year)
        if before['GEOID'].tolist() != after['GEOID'].tolist():
            raise ValueError('Before/after block groups are not aligned')
        year_report = {
            'block_groups': len(raw),
            'negative_cells': int(negative.to_numpy().sum()),
            'rows_with_negative_estimates': int(negative.any(axis=1).sum()),
            'negative_cells_by_column': {column: int(count) for column, count in negative.sum().items() if count},
            'negative_codes': sorted(float(value) for value in np.unique(raw[estimate_columns].to_numpy()[negative.to_numpy()])),
            'edges_before': before_graph.number_of_edges(),
            'edges_after': after_graph.number_of_edges(),
            'algorithms': {},
        }
        for algorithm, before_modularity in [('louvain', louvain_mod), ('leiden', leiden_mod)]:
            column = f'community_{algorithm}'
            a, b = before[column], after[column]
            year_report['algorithms'][algorithm] = {
                'communities_before': int(a.nunique()),
                'communities_after': int(b.nunique()),
                'modularity_before': float(before_modularity),
                'modularity_after': float(after_modularities[algorithm]),
                'adjusted_rand_index': float(adjusted_rand_score(a, b)),
                'normalized_mutual_information': float(normalized_mutual_info_score(a, b, average_method='arithmetic')),
            }
        report['years'][str(year)] = year_report
        map_frames[str(year)] = after.to_crs('EPSG:26916')
        map_data['years'][str(year)] = {
            algorithm: {'count': year_report['algorithms'][algorithm]['communities_after'], 'modularity': after_modularities[algorithm]}
            for algorithm in ['louvain', 'leiden']
        }
    bounds = np.array([frame.total_bounds for frame in map_frames.values()])
    left, bottom = bounds[:, :2].min(axis=0)
    right, top = bounds[:, 2:].max(axis=0)
    map_data['viewBox'] = [0, 0, float(right - left), float(top - bottom)]
    for year, frame in map_frames.items():
        map_data['years'][year]['features'] = [
            {'geoid': row.GEOID, 'path': svg_path(row.geometry.simplify(10, preserve_topology=True), left, top),
             'louvain': int(row.community_louvain), 'leiden': int(row.community_leiden)}
            for row in frame.itertuples()
        ]
    Path('site').mkdir(exist_ok=True)
    Path('site/data.json').write_text(json.dumps(map_data, separators=(',', ':')) + '\n')
    (destination / 'comparison.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps(report['years'], indent=2))


if __name__ == '__main__':
    main()
