# Dataset Feasibility Audit

This audit compares the two candidate public-data paths for the first ACM-oriented biological age clock:

- `NHANES`
- `UK Biobank`

The locked v1 target panel is:

- fitness: `VO2max` or estimated cardiorespiratory fitness
- central adiposity: `visceral fat` or waist-based proxy
- `HbA1c`
- `ApoB`
- systolic blood pressure
- `Cystatin C`
- `CRP`
- `FEV1`

## Summary Decision

Choose `NHANES 1999-2002 + linked mortality` as the first executable path.

Why:

- it is publicly accessible
- it supports direct cardiorespiratory fitness via `CVDVOMAX`
- it supports `Cystatin C` via `SSCYPC`
- it supports `CRP`, `HbA1c`, waist, blood pressure, and linked mortality
- it can preserve the cardiovascular domain with `non-HDL cholesterol` when direct `ApoB` is unavailable

Keep `UK Biobank` as the higher-coverage backup path because it likely supports more of the ideal panel with fewer proxies, but it has materially higher access friction.

## Coverage Comparison

| Domain | Target variable | NHANES path | UK Biobank path | Decision |
| --- | --- | --- | --- | --- |
| Reserve | `VO2max` | direct via `CVDVOMAX` in early fitness files | fitness available but less straightforward and not as immediately public | `NHANES` advantage |
| Central adiposity | `visceral fat` | use `BMXWAIST` or waist-to-height ratio | waist circumference available | tie |
| Glycemia | `HbA1c` | direct via `LBXGH` | direct | tie |
| Atherogenic burden | `ApoB` | use `non-HDL = total cholesterol - HDL` in chosen slice | direct `ApoB` available | `UK Biobank` advantage |
| Hemodynamic stress | systolic blood pressure | direct via `BPXSY1-4` mean | direct | tie |
| Kidney function | `Cystatin C` | direct via `SSCYPC` in early slice | direct | tie |
| Inflammation | `CRP` | direct `CRP` in early slice | direct high-sensitivity `CRP` | slight `UK Biobank` advantage |
| Lung reserve | `FEV1` | available in spirometry files after cycle harmonization | direct | tie |
| Open reproducibility | public access | strong | weaker due application/access requirements | `NHANES` advantage |

## What Broke The Tie

If the only goal were marker completeness, `UK Biobank` would be the cleaner modeling dataset.

But the current goal is to build the first reproducible implementation path with public data. That shifts the ranking:

1. `NHANES` becomes the best first build target.
2. `UK Biobank` becomes the best later upgrade target.

## Chosen NHANES Strategy

Use `NHANES 1999-2002` as the anchor slice because it gives the best overlap with:

- direct fitness
- `Cystatin C`
- `CRP`
- `HbA1c`
- waist
- systolic blood pressure
- spirometry

For the one domain where the ideal marker is missing:

- replace `ApoB` with `non-HDL cholesterol`

This keeps all major physiologic domains represented while preserving the user-selected preference for `Cystatin C`, `CRP`, and a lung function marker.

## Resulting Recommendation

Adopt a two-tier implementation stance:

1. `NHANES 1999-2002 + linked mortality` is the first build target.
2. `UK Biobank` is the later higher-coverage target if access is available.
