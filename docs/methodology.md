# Methodology

# Methodology

This document records every non-trivial decision made while building the
Arizona porphyry copper prospectivity model, along with the reasoning behind
each choice and the alternatives rejected. It is written incrementally by
phase; unnumbered sections at the bottom track open questions.

---

## 1. Data sources

| Dataset | Source | Records (AZ subset) | CRS (raw) | Notes |
|---|---|---|---|---|
| Porphyry Cu deposits | USGS MRDS | 52 → 37 unique cells | EPSG:4326 | Filter: `commod{1,2,3}` contains "copper" AND `dep_type` contains "porphyry" AND `state == "Arizona"` |
| Stream sediment geochem | USGS NGD (`ngdbsed-fUS04`) | 15,052 samples | EPSG:4326 | Elements retained: Cu, Mo, As, Pb, Zn, Au. Ag and W dropped for sparse coverage. |
| Regional geology | USGS SGMC v1.1 | 4,102 polygons | Albers Equal Area (ESRI:102039) | Layer `SGMC_Geology` from `.gdb` |
| Structures | USGS SGMC v1.1 | (see notebook 01) | Albers | Layer `SGMC_Structure` |
| Magnetic anomaly | NOAA EMAG2 V3 (upward continued) | 171 × 174 px AZ subset | EPSG:4326 | Range −250 to +562 nT |
| State boundary | Census TIGER 2023 | 1 polygon | EPSG:4269 | Used only to clip grid and raster |

**Analysis CRS.** All spatial operations are performed in **EPSG:32612** (UTM Zone 12N, meters). Arizona spans UTM 12N and 13N; we accept <0.5% distortion in eastern Arizona rather than introducing a third CRS. Data sources are reprojected on load and *not* reprojected back — the `data/processed/` artifacts may be in any of the above CRSs as long as the analysis notebook reprojects on read.

**Grid.** 10 km × 10 km square cells in EPSG:32612, clipped to the Arizona state polygon. 3,064 cells. Cell size is justified by the exploration-target scale of regional porphyry systems (typically 5–20 km across including alteration halos), fixed here to avoid MAUP-driven result changes.

---

## 2. Preprocessing decisions

### 2.1 Geochemistry — censored values

The NGD encodes censored values as negative numbers in the `qvalue` column (e.g., `-5` means "below 5 ppm"). Raw `qvalue` was preserved with sign, and split into three derived columns per element:

- `{el}` — measured value (NaN if censored)
- `{el}_lod` — detection limit (NaN if not censored)
- `{el}_censored` — boolean
- `{el}_imputed` — the model-ready value: measured if present, else LOD/2

**Why LOD/2.** The standard naive imputation for censored geochemical data. Alternatives rejected: (a) dropping censored samples — impossible, 84.7% of Mo is censored; (b) maximum-likelihood estimation — requires per-element distributional assumptions that the LOD campaign structure violates; (c) treating as zero — known to bias distributions downward by ~50% relative to LOD/2 for lognormal data. LOD/2 is the pragmatic middle; we accept its downward bias for Cu and Pb (LODs are low relative to background, so only ~1–3% of samples are affected) and abandon continuous treatment for elements where LODs dominate.

### 2.2 Geochemistry — per-element treatment strategy

Detection limits were inspected per element across the censored subset:

| Element | Distinct LODs | LOD range | % censored (of detected) | Treatment |
|---|---|---|---|---|
| Cu | 2 | 2–5 ppm | 1.1% | **Continuous** — LODs low, background well above |
| Pb | 3 | 4–20 ppm | 3.3% | **Continuous** — same reason |
| Zn | 3 | 200–500 ppm | 64.5% | **Dropped** — LODs above AZ background (~76 ppm) |
| Mo | 8 | 1–10 ppm | 84.7% | **Binary threshold** (`Mo > 5` ppm) |
| As | 12 | 0.6–1000 ppm | 83.9% | **Binary threshold** (`As > 20` ppm) |
| Au | 28 | 0.001–50 ppb | 88.7% | **Binary threshold** (`Au > 10` ppb) |

**Why Zn was dropped.** The lowest Zn LOD (200 ppm) is above the typical Arizona stream-sediment Zn background (~76 ppm). A censored Zn value therefore contains *no information* — the sample could be anywhere from 1 to 199 ppm and we'd never know. The measurement is censored below a value higher than the signal. Nothing to recover; drop the element.

**Why Mo, As, Au became binary.** These elements are censored at 84–89%, and their LODs span an order of magnitude or more across campaigns (Au: 0.001 to 50 ppb). A "Mo = 5 ppm" measurement from 1978 and a "Mo = 5 ppm" from 2005 aren't comparable — the first might be just above LOD, the second might be 5× LOD. Converting to *"is this sample anomalously enriched above threshold T?"* removes the cross-campaign LOD contamination at the cost of losing ordinal information. For pathfinder elements in a *presence-of-anomaly* prospectivity problem, this is the right trade.

**Why Au was not filtered to low-LOD samples.** The tempting move — keep only the 7,649 samples from low-LOD campaigns — was rejected because the map of low-LOD samples shows strong spatial clustering (they're from specific USGS project footprints, not random). Filtering would convert a random spatial bias (messy but honest) into a *spatially structured* bias (specific districts over-represented). Worse than doing nothing.

**Threshold classification rule.** For each element and threshold T:
- Measured and > T → `True`
- Measured and ≤ T → `False`
- Censored and LOD > T → `NA` (we cannot rule out that the true value exceeds T)
- Censored and LOD ≤ T → `False` (definitively below T)

The `NA` class is not a problem to fix; it is the *honest* answer. A sample reported as "<1000 ppm As" with a "20 ppm" anomaly threshold carries no information about whether the true value exceeds 20. Every downstream model must be able to handle NaN in these columns — and if it can't, that's a red flag about the model, not about the data.

### 2.3 Geochemistry — sample density and the streetlamp problem

After spatially joining samples to the 10 km grid:

- 1,545 of 3,064 cells (50.4%) contain ≥1 sample.
- 1,519 cells (49.6%) contain zero samples.
- Among cells with samples, the distribution is heavily right-skewed: median 4, mean 9.7, max 180.

**Deposit cells are 4–5× more densely sampled than non-deposit cells:**

| Metric | Deposit | Non-deposit | Ratio |
|---|---|---|---|
| Mean samples/cell | 20.9 | 4.7 | 4.4× |
| Median samples/cell | 5 | 1 | 5× |
| % cells with 0 samples | 19% | 50% | 0.38× |

This is the **streetlamp problem**: historical geochemical surveys followed known mining districts, not a random spatial sampling design. Two consequences follow:

1. **`n_samples` (per-cell sample count) is NOT a valid feature.** It encodes "was this area historically explored?" which is a proxy for "is a deposit here?" but is useless for prospectivity on unexplored ground. It stays out of the feature matrix.
2. **The presence/absence of geochem in a cell is contaminated by the same bias.** The 50% of cells that are unsampled include a mix of (a) truly barren ground and (b) prospective ground that was never surveyed. Downstream models must be tested for whether they are learning geochemical signatures or survey coverage. The mitigation strategy is documented in §4.

**Sample location duplicates.** 13,371 unique lat/lon pairs across 15,052 samples; 936 locations carry >1 sample, max 81 at a single coordinate. The "samples per cell" figure is therefore *sample-campaign pairs*, not unique locations. This is appropriate for characterizing survey coverage but must be disclosed when interpreting per-cell geochemical summaries.

**Two samples dropped at the NM border.** Lab IDs 7202 and 8007 (`lon ≈ -109.0473`) fell outside the Census-derived Arizona polygon by <5 m. Negligible; excluded from cell assignment.

### 2.4 Outliers

38 Cu measurements exceed 1,000 ppm. Nine sit within 10 km of a known deposit; thirteen more than 25 km away. Kept in the dataset. Outlier removal was rejected because (a) high-Cu samples near deposits are *signal*, not noise; (b) tree-based models are robust to outliers in the target-encoded regime; (c) any threshold-based removal would introduce a sensitivity knob that must then be reported.

---

## 3. Known limitations

1. **Presence-only labeling.** A `deposit = 0` cell means "no *known* deposit in MRDS," not "no deposit." Buried or undrilled porphyry systems exist and are labeled as negatives. The model's performance should be interpreted as *ranking known deposits*, not as predicting the full deposit population.

2. **MRDS quality is uneven.** Deposit coordinates are typically accurate to a few hundred meters, sometimes worse. Deposit types are occasionally misclassified (skarns and polymetallic veins sometimes tagged "porphyry"). We accept this noise; a deposit-label cleaning pass is documented in a later section.

3. **Sampling bias is not fully correctable.** The streetlamp problem (§2.3) is documented, quantified, and mitigated by (i) excluding `n_samples` as a feature and (ii) spatial CV. It is *not* eliminated. A model built on this data will inherit residual bias toward previously-explored ground; this is disclosed and future work should consider stratification by survey area.

4. **Geochemical censoring loses information.** Binary-thresholded Mo, As, and Au cannot distinguish a sample at 5.1 ppm from one at 500 ppm. Ordinal strength of anomaly is lost. For prospectivity (which is fundamentally a *ranking* problem), the loss is acceptable; for deposit-grade modeling it would not be.

5. **UTM 13N districts are distorted.** Eastern Arizona (>−109°W) is computed in UTM 12N, introducing <0.5% linear distortion. This has no effect on 10 km binning at the resolution of Arizona but is disclosed for completeness.

6. **MAUP.** A different grid origin or cell size would produce different per-cell statistics. Grid origin and cell size are fixed and justified here; robustness to grid size is not tested.

---

## 4. Open questions / assumptions to verify

- **Does geochem actually add predictive power beyond geology + geophysics?** The comparison between a "geology+magnetics only" model and a "geology+magnetics+geochem" model, evaluated under leave-one-district-out spatial CV, is the definitive test of whether the residual streetlamp bias in geochem is dominating. If the gain is real under spatial CV, it's geological signal; if it only appears under random CV, it's survey-coverage leakage. **Planned in Phase 4.**

- **Do deposit cells and non-deposit cells differ systematically in the *composition* of geochemistry after conditioning on sample count?** If geochem-composition difference collapses once you control for `n_samples`, then even the geochemical *values* are contaminated by density. Worth a scatter/regression in Phase 3.

- **Are the 37 deposit cells truly mutually independent?** Several are in the Miami-Globe-Superior district within 15 km of each other. If so, they are one signal, not 37. Leave-one-district-out CV should be designed to respect district boundaries — currently only leave-one-cell-out is planned.

- **Do Cu and Pb continuous values correlate with LOD campaign rather than geology?** Assumed not (LODs low relative to background) but not formally tested.

---

## Appendices

*(Sections E–G of Phase 1, and Phase 2 onwards, will be appended as they are completed.)*
