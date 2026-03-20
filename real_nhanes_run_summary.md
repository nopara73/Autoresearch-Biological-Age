# Real NHANES Run Summary

This file records the first end-to-end public-data run performed in this workspace.

## Source Files Downloaded

The following NHANES 2001-2002 public XPT files were downloaded into `data/raw`:

- `DEMO_B.xpt`
- `BMX_B.xpt`
- `BPX_B.xpt`
- `CVX_B.xpt`
- `L10_B.xpt`
- `L11_2_B.xpt`
- `L13_2_B.xpt`
- `SSCYST_B.xpt`

They were converted to CSV in `data/converted` using `convert_xpt_to_csv.py`.

## Harmonized Cohort Produced

The harmonized public cohort was written to:

- `data/harmonized/nhanes_clock_2001_2002.csv`

Observed cohort summary:

- participants: `62`
- age range: `16` to `49`
- mean age: `26.71`
- central adiposity proxy: `waist_to_height_ratio` for all rows
- atherogenic proxy: `non_HDL_cholesterol` for all rows
- lung proxy: `neutral_placeholder` for all rows

## Why The Cohort Is Small

The intersection is small because the selected kidney marker and several other inputs are stored in NHANES sub-samples:

- `Cystatin C` is only available in a sub-sample
- CRP and lipid measurements in this cycle come from second-exam files
- cardiovascular fitness is limited to its own eligible sample

The overlap of all required domains leaves only a small cohort.

## Real Calibration Output

The scored output was written to:

- `data/outputs/nhanes_clock_scored_2001_2002.csv`

Run summary:

- formula: `Clock_logistic_default`
- participants scored: `62`
- mean surrogate score: `2.8289`
- mean age acceleration: `0.0000`

## Important Caveat

This public NHANES slice did not provide a matching spirometry file in the downloaded component set used for the run, so the loader assigned a documented neutral placeholder for the lung domain.

That means this first real-data run is best interpreted as a **7-domain public approximation** of the intended 8-domain clock, with the lung component held neutral rather than estimated from another variable.
