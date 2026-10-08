import os
import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("MPLBACKEND", "Agg")

import networkx as nx
import numpy as np
import pandas as pd
import requests

import main
import src.visualization as visualization
from src.config import KNN_K
from src.data_loader import DataLoader
from src.features import FeatureEngineer
from src.network import NetworkAnalyzer

ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def test_rates_handle_zero_denominators(self):
        frame = pd.DataFrame({
            "emp_unemployed": [2, 0],
            "emp_labor_force": [10, 0],
            "commute_public_transit": [3, 0],
            "commute_total": [12, 0],
            "edu_bachelors": [1, 0],
            "edu_total_over_25": [4, 0],
            "total_population": [10, 0],
            "race_white": [2, 0],
            "race_black": [5, 0],
            "race_hispanic": [3, 0],
        })
        result = FeatureEngineer.calculate_rates(frame)
        self.assertEqual(result["pct_unemployed"].tolist(), [0.2, 0])
        self.assertEqual(result["pct_transit"].tolist(), [0.25, 0])
        self.assertEqual(result["pct_bachelors"].tolist(), [0.25, 0])
        self.assertEqual(result["pct_white"].tolist(), [0.2, 0])
        self.assertNotIn("pct_white", frame.columns)

    def test_knn_graph_has_no_self_loops_when_rows_are_identical(self):
        # Zero-population block groups share one imputed feature vector, so
        # their self-similarity ties with each other's.
        rng = np.random.default_rng(0)
        X = np.vstack([rng.uniform(0.1, 1.0, size=(20, 4)), np.tile([1.0, 2.0, 3.0, 4.0], (3, 1))])
        graph, _ = NetworkAnalyzer.build_graph(X, pd.RangeIndex(len(X)))
        self.assertEqual(list(nx.selfloop_edges(graph)), [])
        self.assertTrue(all(degree >= KNN_K for _, degree in graph.degree()))
        for i in range(20, 23):
            self.assertTrue({20, 21, 22} - {i} <= set(graph[i]))

    def test_downloaded_overlay_is_found_by_loader(self):
        response = Mock(content=b'{"type":"FeatureCollection","features":[]}')
        with tempfile.TemporaryDirectory() as directory:
            previous = Path.cwd()
            try:
                os.chdir(directory)
                with patch("requests.get", return_value=response):
                    runpy.run_path(str(ROOT / "download_shp.py"))
                overlay = Path("data/cca_shp/Boundaries - Community Areas (current).geojson")
                self.assertEqual(overlay.read_bytes(), response.content)
                loaded = DataLoader.load_community_areas()
                self.assertIsNotNone(loaded)
                self.assertTrue(loaded.empty)
                response.raise_for_status.assert_called_once_with()
            finally:
                os.chdir(previous)

    def test_download_http_failure_is_reported(self):
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError("HTTP failure")
        with tempfile.TemporaryDirectory() as directory:
            previous = Path.cwd()
            try:
                os.chdir(directory)
                with patch("requests.get", return_value=response):
                    with self.assertRaises(requests.HTTPError):
                        runpy.run_path(str(ROOT / "download_shp.py"))
                self.assertFalse(Path("data/cca_shp/Boundaries - Community Areas (current).geojson").exists())
            finally:
                os.chdir(previous)

    def test_both_years_write_real_results_and_figures(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(main, "OUTPUT_DIR", directory), patch.object(visualization, "OUTPUT_DIR", directory):
                main.main()
            for year, expected_rows in [(2019, 1106), (2022, 1135)]:
                saved = pd.read_csv(Path(directory) / f"results_{year}.csv", dtype={"GEOID": str})
                self.assertEqual(len(saved), expected_rows)
                self.assertTrue(saved["GEOID"].is_unique)
                for column in ["community_louvain", "community_leiden"]:
                    self.assertTrue((saved[column] >= 0).all())
                    self.assertGreater(saved[column].nunique(), 1)
                for prefix in ["map_comparison", "network_graph"]:
                    figure = Path(directory) / f"{prefix}_{year}.png"
                    self.assertGreater(figure.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
