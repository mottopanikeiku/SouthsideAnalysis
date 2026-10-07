import json
import unittest
from pathlib import Path

import pandas as pd
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

ROOT = Path(__file__).resolve().parents[1]


class SavedResultTests(unittest.TestCase):
    def test_comparison_and_map_match_saved_partitions(self):
        comparison = json.loads((ROOT / 'results/before_after/comparison.json').read_text())
        site = json.loads((ROOT / 'site/data.json').read_text())
        self.assertEqual(set(site['years']), {'2019', '2022'})
        self.assertTrue(all(value > 0 for value in site['viewBox'][2:]))
        for year, summary in comparison['years'].items():
            with self.subTest(year=year):
                before = pd.read_csv(ROOT / f'results/before_after/pre_fix_{year}.csv', dtype={'GEOID': str})
                after = pd.read_csv(ROOT / f'output/results_{year}.csv', dtype={'GEOID': str})
                self.assertEqual(before['GEOID'].tolist(), after['GEOID'].tolist())
                self.assertEqual(len(after), summary['block_groups'])
                self.assertFalse((after.drop(columns=['GEOID']) < 0).any().any())
                mapped = site['years'][year]
                self.assertEqual([feature['geoid'] for feature in mapped['features']], after['GEOID'].tolist())
                self.assertTrue(all(feature['path'].startswith('M') and feature['path'].endswith('Z') for feature in mapped['features']))
                for algorithm, metrics in summary['algorithms'].items():
                    column = f'community_{algorithm}'
                    a, b = before[column], after[column]
                    self.assertEqual(metrics['communities_before'], a.nunique())
                    self.assertEqual(metrics['communities_after'], b.nunique())
                    self.assertAlmostEqual(metrics['adjusted_rand_index'], adjusted_rand_score(a, b), places=12)
                    self.assertAlmostEqual(metrics['normalized_mutual_information'], normalized_mutual_info_score(a, b, average_method='arithmetic'), places=12)
                    self.assertEqual(mapped[algorithm]['count'], b.nunique())
                    self.assertEqual(mapped[algorithm]['modularity'], metrics['modularity_after'])
                    self.assertEqual([feature[algorithm] for feature in mapped['features']], b.tolist())


if __name__ == '__main__':
    unittest.main()
