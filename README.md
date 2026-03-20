# Prototype Verification Harness

This workspace now contains a minimal runnable prototype of the structural-surrogate framework described in `structural-surrogates-acm-autoresearch-framework.md`.

The prototype does not estimate true all-cause mortality. It evaluates whether explicit surrogate formulas behave like credible mortality-risk proxies under structural tests.

## Files

- `formulas.py`: implements the paper's three candidate formulas and the Section 9 logistic family.
- `sampler.py`: defines the plausible biomarker domain, curated profile pairs, and random dominance pairs.
- `verification.py`: scores formulas for monotonicity, pair ordering, smoothness, bounds, and consistency.
- `run_baseline.py`: compares the built-in formulas and prints a structural score report.
- `clock_variable_spec.py`: locks the first multi-system ACM-oriented panel, proxy rules, and dataset mappings.
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
- `prepare_nhanes_harmonized.py`: CLI to build a harmonized NHANES CSV.
- `calibration.py`: fits a monotone score-to-age calibration and emits `bio_age` and `age_acceleration`.
- `run_clock_calibration.py`: CLI to calibrate a harmonized dataset or a synthetic demo.

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

To prepare a real NHANES-derived harmonized CSV:

```bash
python prepare_nhanes_harmonized.py --demo DEMO.csv --cvx CVX.csv --bmx BMX.csv --glyco GHB.csv --lipids LIPIDS.csv --blood-pressure BPX.csv --cystatin SSCYST.csv --crp CRP.csv --spirometry SPX.csv --output harmonized_clock.csv
```

Then calibrate it:

```bash
python run_clock_calibration.py --input harmonized_clock.csv --output scored_clock.csv
```

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
2. merge raw NHANES component files with `prepare_nhanes_harmonized.py`
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

## Current Public Dataset Path

The first implementation target is:

- `NHANES 1999-2002 + linked mortality`

with these notable proxy rules in code:

- `ApoB` -> non-HDL cholesterol when direct ApoB is unavailable
- `visceral fat` -> waist-to-height ratio, with an equivalent waist-based fallback
- `FEV1` -> FVC-equivalent if only FVC is available

## Important Caveat

The expanded calibration scripts are runnable now, but this workspace does not yet contain the raw NHANES files. Until those are supplied, the real-data path should be considered implemented but not fully exercised end-to-end on the target cohort.
