# Dataset Variable Map

This file freezes the first implementation-ready dataset path for the ACM-oriented clock.

## Chosen Path

- dataset: `NHANES 1999-2002 + linked mortality`
- reason: strongest overlap with the locked v1 panel while remaining publicly reproducible

## Locked Inputs

| Clock input | Preferred measurement | Chosen NHANES mapping | Proxy status |
| --- | --- | --- | --- |
| chronological age | age in years | `RIDAGEYR` | direct |
| fitness | `VO2max` | `CVDVOMAX` | direct |
| central adiposity | visceral fat | `BMXWAIST / BMXHT`, else `BMXWAIST` | proxy |
| glycemia | `HbA1c` | `LBXGH` | direct |
| atherogenic burden | `ApoB` | `LBXTC - LBXHDD` | proxy |
| systolic blood pressure | systolic BP | mean of `BPXSY1`, `BPXSY2`, `BPXSY3`, `BPXSY4` | direct |
| kidney function | `Cystatin C` | `SSCYPC` | direct |
| inflammation | `CRP` | `LBXCRP` | direct |
| lung function | `FEV1` | harmonized `SPXFEV1` | direct after cycle harmonization |

## Harmonization Rules

Apply these transformations before any clock modeling:

1. `systolic_bp = mean(non-missing BPXSY1..BPXSY4)`
2. `central_adiposity = BMXWAIST / BMXHT` when both are available
3. `central_adiposity = BMXWAIST` if height is missing
4. `non_hdl = LBXTC - LBXHDD`
5. `fitness = CVDVOMAX`
6. `kidney_function = SSCYPC`
7. `inflammation = LBXCRP`
8. `lung_function = SPXFEV1` after cycle-specific spirometry file harmonization

## Missing-Data Policy

Use a strict first-pass inclusion rule for v1:

- require age, fitness, glycemia, blood pressure, kidney function, inflammation, and one of the two central-adiposity encodings
- require either direct `FEV1` or explicitly mark the row as lung-domain missing
- require the lipid proxy inputs `LBXTC` and `LBXHDD`

Rows missing any required field should be excluded from the first calibration build rather than imputed.

## Why This Map Is Acceptable

This path preserves all intended physiologic domains:

- reserve: `CVDVOMAX`, `FEV1`
- metabolic burden: `LBXGH`, waist-based adiposity
- cardiovascular burden: systolic BP, `non-HDL`
- organ resilience: `SSCYPC`
- inflammation: `LBXCRP`

The only locked ideal variable that is not used directly is `ApoB`, and its replacement is the approved proxy `non-HDL cholesterol`.
