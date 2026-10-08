# SouthsideAnalysis

I group Census block groups around Chicago's South Side by demographic similarity using the published Louvain and Leiden algorithms.

**The correction changed the answer substantially.** After treating negative Census missing-value codes as missing estimates rather than numbers, before/after adjusted Rand indices range from **0.207 to 0.315**. Both algorithms' modularity scores fell. The old high scores were not evidence of better neighborhood boundaries. These numbers come from the [controlled comparison](results/before_after/comparison.json).

**Question:** How much did missing-value handling distort these demographic partitions?

I fixed [feature engineering](src/features.py), reran both years with the same inputs and seeds, and compared partitions in [this script](tools/compare_missing_values.py). The [interactive map](site/) lets me switch years and algorithms, inspect block groups, and zoom without a map service. This is exploratory clustering, not a map of validated neighborhoods.

## Corrected results

I found the code `-666666666` in **209 estimates across 181 block groups in 2019**, and **361 estimates across 313 block groups in 2022**. All affected estimates were income, housing value or age; the committed extracts had no existing blank estimates in the selected columns. Negative values now become missing before rates, median imputation, standardization and PCA. Blank cells in the corrected CSVs remain blank; imputation is applied to the clustering matrix.

| ACS release / algorithm | Groups before → after | Modularity before → after | Adjusted Rand index | NMI |
| --- | ---: | ---: | ---: | ---: |
| 2019 Louvain | 14 → 11 | 0.8322 → 0.7462 | 0.3032 | 0.4660 |
| 2019 Leiden | 14 → 11 | 0.8338 → 0.7548 | 0.3150 | 0.4747 |
| 2022 Louvain | 13 → 11 | 0.8216 → 0.7285 | 0.2110 | 0.3583 |
| 2022 Leiden | 14 → 10 | 0.8255 → 0.7347 | 0.2067 | 0.3877 |

Every table entry and missing-value count comes from [comparison.json](results/before_after/comparison.json). The corrected CSVs contain [1,106 block groups for 2019](output/results_2019.csv) and [1,135 for 2022](output/results_2022.csv). The [pre-fix partitions](results/before_after/) use the old missing-value behavior under the current locked dependencies, not guessed historical labels. I retained the original [outputs](output/historical/) unchanged.

ARI and arithmetic-average normalized mutual information compare partitions of the same year's block groups without assuming that label numbers match. Louvain retains its weighted objective; Leiden retains the original unweighted objective. Each modularity is evaluated on that run's own graph, so neither a cross-algorithm comparison nor the decrease proves improved real-world communities. Both algorithms now use seed 42; the historical Leiden runs had no recorded seed.

## Reproduce

The committed ACS tables and TIGER boundaries suffice. The committed results were generated on a Linux aarch64 CPU with one numerical-library thread, no GPU and **$0 paid compute**. No runtime benchmark is claimed. Dependency versions, Python version, platform and input checksums are recorded in the comparison file.

```sh
nice -n 19 uv sync --locked
nice -n 19 uv run --locked python -m unittest discover -s tests -v
MPLBACKEND=Agg OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 nice -n 19 uv run --locked python -m tools.compare_missing_values
```

The last command regenerates corrected CSVs and figures in `output/`, the before/after comparison in `results/`, and simplified projected map paths in `site/data.json`. `main.py` runs just the corrected pipeline. To view the map locally, serve `site/` with `python -m http.server --directory site 8000` and open `http://localhost:8000`. The Pages workflow publishes the static directory when GitHub Pages is enabled for Actions; it does not change repository settings.

## Limitations

- Older ACS releases are joined to 2023 TIGER boundaries by GEOID without a geographic crosswalk. This is not a controlled longitudinal comparison.
- The bounding box approximates the South Side. Graph edges connect demographic similarities, not adjacent locations; separated areas can share a label.
- Median imputation ignores uncertainty and missingness patterns. I retain the original zero-denominator rate convention to isolate the missing-code correction.
- Community IDs and colors are arbitrary and not aligned across years or algorithms. Map geometry is simplified for display, not for analysis.
- I have not validated these partitions against neighborhoods or rerun many random seeds. The committed ACS extraction logs and original dependency versions are unavailable.
- Louvain reacts to last-digit floating-point differences in edge weights. Multiplying the corrected 2022 PCA features by random factors within about 10⁻¹² of 1 kept every graph edge but changed that Louvain partition (ARI 0.87 against the unperturbed run) in two of three tries. Another machine with the same locked packages can therefore report different 2022 numbers.

## Prior work and data

I call [Louvain (Blondel et al.)](https://arxiv.org/abs/0803.0476) through NetworkX and [Leiden (Traag et al.)](https://doi.org/10.1038/s41598-019-41695-z) through leidenalg/igraph. The data are aggregate [ACS five-year estimates](https://www.census.gov/data/developers/data-sets/acs-5year.html) and [TIGER/Line boundaries](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html), not individual records. Optional [Chicago community-area outlines](https://data.cityofchicago.org/Community-Economic-Development/Boundaries-Community-Areas-current-/cauq-8yn6) can be downloaded with `download_shp.py`; they are only a plotting overlay.

Written with AI coding assistance.
