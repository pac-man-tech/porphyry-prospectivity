# Arizona Porphyry Copper Prospectivity - Phase 0

## Question
Can regional geochemistry, geophysics, and geology predict which 10 km × 10 km 
grid cells in Arizona host known porphyry copper deposits?

## Study Area
Arizona, USA — Laramide porphyry Cu-Mo belt.

## Data Inventory (Phase 0 Complete)

| Dataset | Source | Records | CRS | Notes |
|---|---|---|---|---|
| Porphyry Cu deposits | USGS MRDS | 52 deposits | EPSG:4326 | Filtered: commod contains "copper" AND dep_type contains "porphyry" AND state = "Arizona" |
| Stream sediment geochem | USGS NGD (ngdbsed-fUS04) | 15,052 samples | EPSG:4326 | Elements: Cu, Mo, Ag, As, Pb, Zn, W, Au |
| Regional geology | AZGS DI-08 ver 3 | 4,851 polygons | EPSG:4269 (NAD83) | Polygon geometry, `LABEL` column for map unit |
| Spatial grid | Derived | 3,064 cells | EPSG:32612 (UTM 12N) | 10 km × 10 km, clipped to AZ boundary |

## Target Variable
- 3,064 grid cells total
- 37 cells labeled `1` (contain ≥1 known porphyry Cu deposit)
- 3,027 cells labeled `0` (no known deposit)
- **Class imbalance: 1 : 81.8**
- Note: 52 deposits fall into 37 unique cells due to clustering in 
  porphyry districts (Miami-Globe-Superior, Ray, Morenci, etc.)

## Data Quality Notes
- Cu censored (below detection limit): 3%
- Mo censored: 85% | Ag: 96% | As: 84%
- Pb censored: 5% | Zn: 65% | W: 99% | Au: 89%
- CRS mismatch: geology is NAD83 (EPSG:4269), everything else is WGS84 
  or UTM. Will reproject all layers to EPSG:32612 in Phase 2.

## Known Limitations
- **Presence-only problem**: A `0` label means "no *known* deposit," 
  not "no deposit." Buried deposits exist but aren't in MRDS.
- **Coarse geophysics**: EMAG2 resolution (~3.7 km) is finer than the 
  10 km grid but coarser than ideal.
- **Sample density bias**: Geochem samples cluster near roads and 
  historical mining districts. Model may learn sampling bias.

## Reproduce
1. Clone repo
2. `conda env create -f environment.yml`
3. Run notebooks in order: 00 → 05


Repository structure
See the project root for `notebooks/`, `src/`, `data/`, `reports/`, and `docs/`.

License: See `LICENSE`.
