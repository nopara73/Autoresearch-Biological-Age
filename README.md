# Prototype Verification Harness

This workspace now contains a minimal runnable prototype of the structural-surrogate framework described in `structural-surrogates-acm-autoresearch-framework.md`.

The prototype does not estimate true all-cause mortality. It evaluates whether explicit surrogate formulas behave like credible mortality-risk proxies under structural tests.

## Strongest Public NHANES Validation

The strongest public result in this workspace comes from `NHANES 2009-2010` with linked mortality follow-up through `2019`.

- out-of-fold discrimination is real rather than trivial: `75.9%` for `surrogate_score` and `75.4%` for `bio_age`
- risk stratification is directionally clean: out-of-fold mortality rises across bio-age quartiles from `0.0095` in Q1 to `0.1458` in Q4

These results do not establish clinical validity, but they do suggest that the clock captures nontrivial mortality-related signal in a public cohort.

### Rough ACM Comparison

| Clock | Reported ACM performance | Cohort / framing |
| --- | --- | --- |
| `PhenoAge` | about `88%` | NHANES, 10-year mortality AUC |
| `Bortz` blood-biomarker BA | about `74%` to `76%` | UK Biobank, survival-model c-index |
| `This clock` | about `75%` to `76%` | NHANES 2009-2010, out-of-fold c-stat |

These percentages are intended as a rough orientation only. They come from different cohorts and closely related but not identical discrimination metrics.

## Current Mathematical Formula

The current biological-age clock is an eight-domain monotone logistic model. Let

- `F` denote fitness,
- `W` denote waist-to-height ratio,
- `H` denote HbA1c,
- `A` denote ApoB,
- `S` denote systolic blood pressure,
- `K` denote the kidney-function measure used by the harmonized cohort,
- `C` denote C-reactive protein, and
- `L` denote lung function measured by `FEV1`.

Define the standardized physiologic deviations from the reference state by

$$
\begin{aligned}
f &= \frac{45 - F}{10}, &
w &= \frac{W - 0.48}{0.08}, &
h &= \frac{H - 5.3}{0.5}, &
a &= \frac{A - 110}{30}, \\
s &= \frac{S - 115}{15}, &
k &= \frac{K - 0.85}{0.25}, &
c &= \frac{C - 1.0}{1.5}, &
l &= \frac{3.5 - L}{0.6}.
\end{aligned}
$$

The clock's linear predictor is then

$$
z = -4.3 + 0.9f + 0.7w + 0.8h + 0.5a + 0.45s + 0.8k + 0.35c + 0.75l + 0.12wh + 0.10ks + 0.08cl.
$$

The raw surrogate score is the bounded logistic transform

$$
R = \frac{20}{1 + e^{-z}},
$$

so that $R \in (0, 20)$.

Biological age is not represented by a further fixed closed-form expression in the current implementation. Instead, after computing \(R\), the pipeline fits a monotone isotonic calibration map \(g\) from surrogate score to chronological age in the reference cohort and defines biological age as

$$
BA = g(R).
$$

Age acceleration is then defined as the residual from the cohort-level linear regression of biological age on chronological age. If chronological age is denoted by \(CA\) and the fitted regression is \(\alpha + \beta CA\), then

$$
\mathrm{AgeAcceleration} = BA - (\alpha + \beta CA).
$$

Accordingly, the complete mathematical pipeline is: biomarkers to standardized deviations; standardized deviations to the logistic surrogate score `R`; `R` to calibrated biological age `BA`; and `BA` to residualized age acceleration.

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

## Current Clock Formula

The main clock currently used in this repo is the default logistic expanded-panel formula in `clock_formulas.py`.

It first converts each biomarker into a standardized offset from a healthy reference:

- `fitness_offset = (45 - fitness) / 10`
- `waist_offset = (waist_to_height_ratio - 0.48) / 0.08`
- `hba1c_offset = (hba1c - 5.3) / 0.5`
- `apob_offset = (apob - 110) / 30`
- `sbp_offset = (systolic_bp - 115) / 15`
- `kidney_offset = (kidney_function - 0.85) / 0.25`
- `crp_offset = (crp - 1.0) / 1.5`
- `lung_offset = (3.5 - fev1) / 0.6`

It then combines them as:

```text
z =
  -4.3
  + 0.9  * fitness_offset
  + 0.7  * waist_offset
  + 0.8  * hba1c_offset
  + 0.5  * apob_offset
  + 0.45 * sbp_offset
  + 0.8  * kidney_offset
  + 0.35 * crp_offset
  + 0.75 * lung_offset
  + 0.12 * waist_offset * hba1c_offset
  + 0.10 * kidney_offset * sbp_offset
  + 0.08 * crp_offset * lung_offset
```

The raw clock score is then:

```text
surrogate_score = 20 / (1 + exp(-z))
```

Finally, `surrogate_score` is mapped to `bio_age` using a monotone isotonic calibration fit on the reference cohort. In other words, `bio_age` is not a single closed-form equation in the current implementation; it is the calibrated age corresponding to the computed `surrogate_score`.

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
