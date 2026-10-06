# SouthsideAnalysis

SouthsideAnalysis is a small exploratory analysis of Census block-group demographics around Chicago's South Side using the published Louvain and Leiden community-detection algorithms.

**Question:** Do demographic similarities produce useful groupings of block groups, and how do the two algorithms partition the same graph?

[Feature engineering](src/features.py) derives demographic rates, imputes missing values, standardizes features, and applies PCA. [Network analysis](src/network.py) builds a cosine-similarity nearest-neighbor graph and finds communities; [main.py](main.py) joins the Census tables to geographic boundaries and writes maps and CSVs.

**Result:** The saved runs produce partitions, not validated neighborhood boundaries. Their modularity scores are high, but input and algorithm limitations below prevent interpreting them as evidence of meaningful communities.

## Saved results

| ACS release | Joined block groups | Louvain groups | Leiden groups | Louvain modularity | Leiden modularity |
| --- | ---: | ---: | ---: | ---: | ---: |
| [2019](output/results_2019.csv) | 1,106 | 14 | 14 | 0.832 | 0.837 |
| [2022](output/results_2022.csv) | 1,135 | 13 | 14 | 0.823 | 0.827 |

Counts come from the linked CSV rows and unique community labels. Modularity values are the rounded labels in the saved [2019](output/map_comparison_2019.png) and [2022](output/map_comparison_2022.png) comparison maps. These are historical outputs: the original dependency versions and Leiden random seed were not recorded, so reruns need not reproduce the labels or scores exactly. The additional `*_advanced.csv` files and older `map_*.png` images are preserved, but their generating code is not available.

## Reproduce

Run from the repository root with [uv](https://docs.astral.sh/uv/). The committed tables and shapefile suffice; no API key, GPU, model download, or paid service is needed. Use a local CPU machine; the smoke test runs on the owner's Ryzen AI 5 PRO 340 laptop within the project runner's memory cap. Compute cost is $0; no runtime benchmark is claimed.

```sh
nice -n 19 uv sync --locked
/home/alp/Projects/profile-program/bin/pp-run heavy uv run --locked python -m unittest discover -s tests -v
/home/alp/Projects/profile-program/bin/pp-run heavy uv run --locked python main.py
```

The `pp-run` path is specific to the owner's shared workstation; elsewhere run the Python commands under `nice -n 19`. The test runs both years in a temporary output directory. The final command overwrites the normal results and comparison/network images under `output/`; preserve historical files before running it if needed. Optional official Chicago community-area outlines are not bundled. `download_shp.py` downloads them to the path the loader recognizes; outlines are only a plotting overlay.

## Limitations

- Census negative missing-value codes remain numeric inputs; the saved [2022 CSV](output/results_2022.csv) contains them. Median imputation therefore does not handle all missing estimates, and the partitions may be distorted.
- The [loader](src/data_loader.py) joins older ACS releases to the committed newer TIGER boundaries by identifier without a geographic crosswalk; comparisons across years are not a controlled longitudinal analysis.
- The [configured bounding box](src/config.py) is an approximation, not an official South Side boundary. Graph edges represent demographic similarity, not geographic adjacency.
- Louvain uses edge weights, while the current Leiden call does not pass them. Their modularity scores therefore refer to different objectives; Leiden is also unseeded.
- There is no neighborhood validation, uncertainty analysis, or acquisition script for the committed ACS extracts. The unused additional ACS table is not part of the pipeline.

## Prior work and data

- [Louvain: Blondel et al.](https://arxiv.org/abs/0803.0476) and [Leiden: Traag et al.](https://doi.org/10.1038/s41598-019-41695-z), called through NetworkX and leidenalg/igraph rather than implemented here.
- [American Community Survey five-year estimates](https://www.census.gov/data/developers/data-sets/acs-5year.html): the committed CSVs contain aggregate geographic labels and demographic estimates, not individual records. Original extraction logs are absent; source attribution does not establish an independently verified copy of every value.
- [Census TIGER/Line boundaries](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html), with the original [Census metadata](data/tl_2023_17_bg/tl_2023_17_bg.shp.iso.xml) retained.
- [Chicago community-area boundaries](https://data.cityofchicago.org/Community-Economic-Development/Boundaries-Community-Areas-current-/cauq-8yn6), optionally downloaded by the helper.

Written with AI coding assistance.
