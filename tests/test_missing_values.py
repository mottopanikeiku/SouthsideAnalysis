import unittest

import numpy as np
import pandas as pd

from src.config import ACS_VAR_MAP
from src.features import FeatureEngineer


class MissingValueTests(unittest.TestCase):
    def test_negative_acs_estimates_are_missing_without_changing_other_columns(self):
        sentinels = (
            -222222222,
            -333333333,
            -555555555,
            -666666666,
            -888888888,
            -999999999,
        )
        for sentinel in sentinels:
            with self.subTest(sentinel=sentinel):
                frame = pd.DataFrame(
                    {column: [sentinel, -1, 0, 25, np.nan]
                     for column in ACS_VAR_MAP.values()},
                    index=["sentinel", "negative", "zero", "valid", "missing"],
                )
                frame["longitude"] = [-87.7, -87.6, -87.5, -87.4, np.nan]
                frame["signed_offset"] = [sentinel, -1, 0, 1, np.nan]
                original = frame.copy(deep=True)

                result = FeatureEngineer.calculate_rates(frame)

                for column in ACS_VAR_MAP.values():
                    with self.subTest(column=column):
                        self.assertTrue(pd.isna(result.loc["sentinel", column]))
                        self.assertTrue(pd.isna(result.loc["negative", column]))
                        self.assertEqual(result.loc["zero", column], 0)
                        self.assertEqual(result.loc["valid", column], 25)
                        self.assertTrue(pd.isna(result.loc["missing", column]))
                pd.testing.assert_series_equal(result["longitude"], original["longitude"])
                pd.testing.assert_series_equal(result["signed_offset"], original["signed_offset"])
                pd.testing.assert_frame_equal(frame, original)

    def test_rates_preserve_missing_inputs_and_legitimate_zero_denominators(self):
        rate_columns = (
            ("emp_unemployed", "emp_labor_force", "pct_unemployed"),
            ("commute_public_transit", "commute_total", "pct_transit"),
            ("edu_bachelors", "edu_total_over_25", "pct_bachelors"),
            ("race_white", "total_population", "pct_white"),
            ("race_black", "total_population", "pct_black"),
            ("race_hispanic", "total_population", "pct_hispanic"),
        )
        index = [
            "valid",
            "negative_numerator",
            "negative_denominator",
            "both_negative",
            "zero_denominator",
            "zero_numerator",
            "negative_numerator_zero_denominator",
            "missing_numerator",
            "missing_denominator",
            "missing_numerator_zero_denominator",
            "zero_numerator_negative_denominator",
        ]
        numerators = [2, -666666666, 2, -888888888, 2, 0, -999999999,
                      np.nan, 2, np.nan, 0]
        denominators = [8, 8, -999999999, -666666666, 0, 8, 0,
                        8, np.nan, 0, -888888888]
        expected = [0.25, np.nan, np.nan, np.nan, 0, 0, np.nan,
                    np.nan, np.nan, np.nan, np.nan]

        for numerator, denominator, rate in rate_columns:
            with self.subTest(rate=rate):
                frame = pd.DataFrame(
                    {numerator: numerators, denominator: denominators}, index=index
                )
                original = frame.copy(deep=True)

                result = FeatureEngineer.calculate_rates(frame)

                np.testing.assert_allclose(result[rate].to_numpy(), expected, equal_nan=True)
                pd.testing.assert_frame_equal(frame, original)

    def test_missing_rates_are_median_imputed_before_finite_pca(self):
        frame = pd.DataFrame({
            "median_household_income": [100, -666666666, 300, 500, 1100],
            "median_housing_value": [1000, 2000, -888888888, 4000, 9000],
            "median_age": [-666666666, -888888888, -999999999, np.nan, -1],
            "emp_unemployed": [1, -999999999, 3, 8, 0],
            "emp_labor_force": [10, 20, -666666666, 20, 0],
            "commute_public_transit": [1, 2, 3, 4, 5],
            "commute_total": [10, 10, 10, 10, 10],
        })
        rates = FeatureEngineer.calculate_rates(frame)
        self.assertTrue(pd.isna(rates.loc[1, "median_household_income"]))
        self.assertTrue(pd.isna(rates.loc[2, "median_housing_value"]))
        self.assertTrue(rates.loc[[1, 2], "pct_unemployed"].isna().all())
        self.assertTrue(rates["median_age"].isna().all())
        original_rates = rates.copy(deep=True)

        projected, feature_names = FeatureEngineer.prepare_features(rates)

        self.assertEqual(feature_names, [
            "median_household_income", "median_housing_value",
            "pct_unemployed", "pct_transit",
        ])
        self.assertEqual(projected.shape[0], len(frame))
        self.assertGreater(projected.shape[1], 0)
        self.assertTrue(np.issubdtype(projected.dtype, np.number))
        self.assertTrue(np.isfinite(projected).all())
        pd.testing.assert_frame_equal(rates, original_rates)

        completed = rates.copy(deep=True)
        completed.loc[1, "median_household_income"] = 400
        completed.loc[2, "median_housing_value"] = 3000
        completed.loc[[1, 2], "pct_unemployed"] = 0.1
        expected_projection, expected_names = FeatureEngineer.prepare_features(completed)

        self.assertEqual(feature_names, expected_names)
        np.testing.assert_allclose(projected, expected_projection, rtol=1e-10, atol=1e-10)


if __name__ == "__main__":
    unittest.main()
