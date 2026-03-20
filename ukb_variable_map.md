# UK Biobank Variable Map

This file defines the richer primary dataset path for the ACM-oriented clock.

## Primary Path

- dataset: `UK Biobank`
- role: richer primary path for the first serious 8-domain clock

## Why It Is Primary

Compared with the public NHANES fallback, UK Biobank improves the clock path by making these domains more directly available in one ecosystem:

- real `ApoB`
- real spirometry (`FEV1` / `FVC`)
- `CRP`
- `HbA1c`
- `Cystatin C`
- systolic blood pressure
- waist circumference and, in a subset, visceral adipose tissue
- age at recruitment

## Preferred UKB Inputs

| Clock input | Preferred UKB source | Fallback |
| --- | --- | --- |
| chronological age | `age_at_recruitment` / `f.21022.0.0` | a compatible exported age column |
| fitness | exported cardiorespiratory fitness / estimated CRF / VO2max-like variable | project-specific derived fitness column |
| central adiposity | MRI VAT / `f.22407.2.0` | waist-to-height ratio, then waist circumference |
| glycemia | `HbA1c` | none |
| atherogenic burden | `ApoB` / `f.30640.0.0` | non-HDL cholesterol |
| systolic blood pressure | `f.4080.*` or named systolic BP columns | average of available systolic readings |
| kidney function | `Cystatin C` / `f.30720.0.0` | none |
| inflammation | `CRP` / `f.30710.0.0` | named CRP column |
| lung function | `FEV1` | `FVC` equivalent |

## Loader Strategy

The UKB harmonizer is built to accept:

- exact field-style columns such as `f.30640.0.0`
- descriptive export columns such as `apolipoprotein_b`
- project-specific pre-cleaned columns such as `fitness`, `vo2max`, or `cystatin_c`

This is intentional because UK Biobank exports often vary across projects and preprocessing workflows.

The restricted-data path now also includes:

- `ukb_export_manifest.json` as a machine-readable field checklist
- `prepare_ukb_harmonized.py --report ...` for a JSON QA summary with matched headers, drop reasons, and proxy usage
- `run_tabular_outcome_validation.py` for generic scored-cohort outcome validation once a real event table is available

## Current Recommendation

Use UK Biobank as the main path when you want:

- the highest-quality full-panel clock
- direct ApoB and spirometry
- a materially better ACM-oriented training and validation environment

Use NHANES only when public reproducibility matters more than clean full-panel overlap.
