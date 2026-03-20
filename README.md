# Prototype Verification Harness

This workspace now contains a minimal runnable prototype of the structural-surrogate framework described in `structural-surrogates-acm-autoresearch-framework.md`.

The prototype does not estimate true all-cause mortality. It evaluates whether explicit surrogate formulas behave like credible mortality-risk proxies under structural tests.

## Files

- `formulas.py`: implements the paper's three candidate formulas and the Section 9 logistic family.
- `sampler.py`: defines the plausible biomarker domain, curated profile pairs, and random dominance pairs.
- `verification.py`: scores formulas for monotonicity, pair ordering, smoothness, bounds, and consistency.
- `run_baseline.py`: compares the built-in formulas and prints a structural score report.
- `clock_variable_spec.py`: locks the first multi-system ACM-oriented panel, proxy rules, and dataset mappings.
- `ukb_variable_map.md`: defines the richer UK Biobank-first mapping and expected export inputs.
- `dataset_feasibility_audit.md`: compares `NHANES` and `UK Biobank` for the first biological-age build.
- `dataset_variable_map.md`: freezes the first implementation-ready public dataset path and raw column transforms.
- `prototype_generalization_plan.md`: defines how to evolve the current 4-variable prototype into the expanded panel.
- `age_calibration_plan.md`: defines how the surrogate score will be mapped to `bio_age` and `age_acceleration`.
- `clock_features.py`: defines the harmonized 8-domain clock profile and field metadata.
- `clock_formulas.py`: implements expanded-panel surrogate formula families.
- `clock_sampler.py`: creates synthetic expanded-panel profiles and dominance pairs.
- `clock_verification.py`: evaluates expanded-panel formulas under structural validity rules.
- `run_clock_baseline.py`: compares the expanded-panel formulas on synthetic profiles.
- `nhanes_loader.py`: merges and harmonizes raw NHANES component CSVs into the clock input space.
- `ukb_loader.py`: harmonizes UK Biobank exports into the same clock-ready format.
- `convert_xpt_to_csv.py`: converts downloaded NHANES SAS XPT files into CSVs for the harmonizer.
- `prepare_nhanes_harmonized.py`: CLI to build a harmonized NHANES CSV.
- `prepare_ukb_harmonized.py`: CLI to build a harmonized UK Biobank CSV.
- `ukb_export_manifest.json`: machine-readable checklist of required and preferred UK Biobank export fields.
- `calibration.py`: fits a monotone score-to-age calibration and emits `bio_age` and `age_acceleration`.
- `run_clock_calibration.py`: CLI to calibrate a harmonized dataset or a synthetic demo, with optional out-of-fold scoring.
- `real_nhanes_run_summary.md`: records the first real public-data run and its cohort limitations.
- `public_clock_loader.py`: builds the stronger modern public NHANES clock cohort with real spirometry and direct ApoB/CRP.
- `prepare_public_clock.py`: CLI for the stronger public clock path.
- `real_public_clock_summary.md`: records the strongest runnable public-only clock built in this workspace.
- `mortality_validation.py`: joins scored public clock outputs to NHANES linked mortality and computes validation summaries.
- `run_public_mortality_validation.py`: CLI for mortality validation of the public clock.
- `run_tabular_outcome_validation.py`: CLI for validating a scored cohort against a generic tabular outcome file.

## How To Run

From the workspace root:

```bash
python run_baseline.py
```

To run the expanded 8-domain structural baseline:

```bash
python run_clock_baseline.py
```

To test the age-calibration pipeline without real data:

```bash
python run_clock_calibration.py --synthetic-demo 200
```

To test the same calibration flow out-of-sample:

```bash
python run_clock_calibration.py --synthetic-demo 200 --oof-folds 5
```

To prepare a UK Biobank-derived harmonized CSV:

```bash
python prepare_ukb_harmonized.py --input ukb_export.csv --output data/harmonized/ukb_clock.csv --report data/outputs/ukb_clock_report.json
```

Then calibrate it:

```bash
python run_clock_calibration.py --input data/harmonized/ukb_clock.csv --output data/outputs/ukb_clock_scored.csv
```

If you also have a restricted cohort outcome table:

```bash
python run_tabular_outcome_validation.py --scored data/outputs/ukb_clock_scored.csv --outcomes ukb_outcomes.csv --id-col eid --event-col event_flag --followup-col followup_months --bootstrap 200
```

To prepare a real NHANES-derived harmonized CSV:

```bash
python convert_xpt_to_csv.py data/raw/DEMO_B.xpt data/raw/BMX_B.xpt data/raw/BPX_B.xpt data/raw/CVX_B.xpt data/raw/L10_B.xpt data/raw/L11_2_B.xpt data/raw/L13_2_B.xpt data/raw/SSCYST_B.xpt --output-dir data/converted
```

```bash
python prepare_nhanes_harmonized.py --demo data/converted/DEMO_B.csv --cvx data/converted/CVX_B.csv --bmx data/converted/BMX_B.csv --glyco data/converted/L10_B.csv --lipids data/converted/L13_2_B.csv --blood-pressure data/converted/BPX_B.csv --cystatin data/converted/SSCYST_B.csv --crp data/converted/L11_2_B.csv --output data/harmonized/nhanes_clock_2001_2002.csv
```

Then calibrate it:

```bash
python run_clock_calibration.py --input data/harmonized/nhanes_clock_2001_2002.csv --output data/outputs/nhanes_clock_scored_2001_2002.csv
```

To build the strongest currently runnable public-only clock:

```bash
python prepare_public_clock.py --demo data/converted/DEMO_F.csv --bmx data/converted/BMX_F.csv --blood-pressure data/converted/BPX_F.csv --spirometry data/converted/SPX_F.csv --glyco data/converted/GHB_F.csv --apob data/converted/APOB_F.csv --biopro data/converted/BIOPRO_F.csv --alb-cr data/converted/ALB_CR_F.csv --crp data/converted/CRP_F.csv --physical-activity data/converted/PAQ_F.csv --output data/harmonized/public_clock_2009_2010_v2.csv
```

```bash
python run_clock_calibration.py --input data/harmonized/public_clock_2009_2010_v2.csv --output data/outputs/public_clock_2009_2010_v2_scored.csv --oof-folds 5
```

```bash
python run_public_mortality_validation.py --scored data/outputs/public_clock_2009_2010_v2_scored.csv --mortality data/raw/NHANES_2009_2010_MORT_2019_PUBLIC.dat --bootstrap 200
```

## Rigorous Public Validation

The stronger public evaluation path now supports:

- out-of-fold `bio_age` and `age_acceleration` generation through `run_clock_calibration.py --oof-folds`
- bootstrap confidence intervals for c-statistics through `run_public_mortality_validation.py --bootstrap`
- the older in-sample path still exists, but it is no longer the best choice for reporting mortality-facing results

Recommended order:

1. build the public harmonized cohort
2. score it with `run_clock_calibration.py --oof-folds 5`
3. validate that scored file with `run_public_mortality_validation.py --bootstrap 200`

## What The Report Means

Each formula gets a total structural score:

- higher is better
- scores are the sum of negative penalties
- a score closer to `0` means fewer structural violations

Each component captures a different requirement from the paper:

- `monotonicity`: lower `VO2max` should not reduce risk, and higher `visceral fat`, `HbA1c`, or `ApoB` should not reduce risk
- `pairs`: clearly healthier profiles should rank below clearly worse profiles
- `smoothness`: small changes in biomarkers should not create implausibly large jumps
- `bounds`: output should stay within the configured annual risk range
- `consistency`: the healthy reference profile should stay near the configured anchor and below a severe reference profile

The baseline script also prints:

- `pair_failures`: how many ordered profile comparisons failed
- `reference_risk`: score for the healthy reference profile
- `severe_risk`: score for the severe reference profile
- `worst_mono`, `worst_pair`, `worst_smooth`: the largest observed violations for quick debugging

## Default Assumptions

The current prototype uses deterministic defaults so results are reproducible:

- random seed `42`
- `500` sampled profiles
- `204` ordered pairs total (`4` curated and `200` synthetic dominance pairs)
- annual risk bounds of `0` to `30` percent
- healthy reference anchor of `0.2` percent annual risk

These values are configurable in `VerificationConfig` inside `verification.py`.

## Current Interpretation

This is a first-stage research scaffold, not a validated epidemiology tool. The output tells you which formulas best satisfy the chosen structural rules, not which one best predicts real mortality.

The smoothness settings are intentionally explicit and conservative, so some formulas may incur large penalties even if they are directionally plausible. That is expected at this stage and should be treated as a tuning target for later iterations.

## Suggested Next Step

Use the harness as the objective function for structured search over the constrained logistic family from Section 9 of the paper:

1. keep the current three formulas as baselines
2. generate candidate logistic coefficients with nonnegative monotone terms
3. optimize them against the total structural score
4. compare the best optimized candidate against `R1`, `R2`, and `R3`

Only after that should you consider adding LLM-guided proposal loops or any external calibration step.

## Expanded Workflow

The new 8-domain clock path works like this:

1. choose the locked panel from `clock_variable_spec.py`
2. harmonize either a UK Biobank export or the NHANES fallback components
3. transform them into harmonized inputs:
   - fitness
   - central adiposity
   - glycemia
   - atherogenic burden
   - hemodynamic stress
   - kidney function
   - inflammation
   - lung function
4. score participants with one expanded-panel surrogate formula
5. calibrate score to chronological age
6. export:
   - `surrogate_score`
   - `bio_age`
   - `age_acceleration`

## Primary Dataset Path

The richer primary implementation target is:

- `UK Biobank`

with these notable advantages in code and design:

- direct `ApoB`
- real lung function via `FEV1` or `FVC`
- direct `Cystatin C`
- direct `CRP`
- direct `HbA1c`
- systolic blood pressure and waist-based adiposity with optional VAT in subsets

The UKB harmonizer accepts:

- exact field-style columns such as `f.30640.0.0`
- descriptive exports such as `apolipoprotein_b`
- project-specific cleaned columns such as `cardiorespiratory_fitness` or `cystatin_c`

## Public Fallback Path

The public reproducible fallback remains:

- `NHANES 1999-2002 + linked mortality`

with these notable proxy rules in code:

- `ApoB` -> non-HDL cholesterol when direct ApoB is unavailable
- `visceral fat` -> waist-to-height ratio, with an equivalent waist-based fallback
- `FEV1` -> FVC-equivalent if only FVC is available

## Important Caveat

The UK Biobank-first path is implemented and verified on a mock export, but it has not been run on a real UKB cohort in this workspace because no actual UKB export file is present here.

The restricted-data path is now more production-ready than before because it also supports:

- a JSON QA report from `prepare_ukb_harmonized.py --report`
- a machine-readable export checklist in `ukb_export_manifest.json`
- generic tabular outcome validation through `run_tabular_outcome_validation.py`

The expanded NHANES 2001-2002 fallback path has been exercised end-to-end on real public data, but the resulting cohort is small and uses a documented neutral placeholder for the lung domain because a matching spirometry component was not available in the downloaded file set used for that run.

The strongest public-only clock in this workspace is now the improved `NHANES 2009-2010` build in `real_public_clock_summary.md`. It is materially better than the older fallback because it uses direct `FEV1`, direct `ApoB`, direct `CRP`, direct `HbA1c`, a stronger kidney proxy from eGFR plus albuminuria, and public linked-mortality validation through 2019. It still relies on a public fitness proxy and waist-based adiposity instead of the ideal locked measurements.
