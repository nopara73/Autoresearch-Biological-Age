# Real Public Clock Summary

This file records the strongest currently runnable public-only biological aging clock built in this workspace.

## Chosen Public Path

- cohort: `NHANES 2009-2010`
- reason: this cycle gives direct public coverage for:
  - real spirometry (`SPX_F`)
  - direct `ApoB` (`APOB_F`)
  - direct `CRP` (`CRP_F`)
  - direct `HbA1c` (`GHB_F`)
  - systolic blood pressure (`BPX_F`)
  - waist and height (`BMX_F`)
  - serum creatinine from `BIOPRO_F` as the kidney proxy
  - physical activity plus resting pulse as the fitness proxy

## Output Files

- first harmonized cohort: `data/harmonized/public_clock_2009_2010.csv`
- improved harmonized cohort: `data/harmonized/public_clock_2009_2010_v2.csv`
- first scored output: `data/outputs/public_clock_2009_2010_scored.csv`
- improved scored output: `data/outputs/public_clock_2009_2010_v2_scored.csv`
- out-of-fold scored output: `data/outputs/public_clock_2009_2010_v2_scored_oof5.csv`
- mortality file used for validation: `data/raw/NHANES_2009_2010_MORT_2019_PUBLIC.dat`

## Cohort Summary

- participants: `2103`
- age range: `20` to `79`
- mean age: `46.72`

## Improved Output Summary

- mean surrogate score: `4.1814`
- bio-age range: `22.00` to `61.14`
- mean bio-age: `46.72`
- residualized age-acceleration range: `-20.75` to `22.45`

## Domains Actually Used

- fitness: derived proxy from weekly activity plus resting pulse
- central adiposity: waist-to-height ratio
- glycemia: direct `HbA1c`
- atherogenic burden: direct `ApoB`
- hemodynamic stress: mean systolic blood pressure
- kidney function: creatinine-based eGFR plus urine albumin-creatinine ratio proxy
- inflammation: direct `CRP`
- lung function: direct `FEV1`

## Mortality Validation

The improved scored output was linked to the public NHANES mortality file through 2019.

Observed results:

- linked participants: `2103`
- deaths observed: `143`
- mortality rate: `0.0680`
- c-statistic using `surrogate_score`: `0.7592`
- c-statistic using `bio_age`: `0.7584`
- c-statistic using residualized `age_acceleration`: `0.5844`
- bootstrap-ready 95 percent confidence intervals are now supported by `run_public_mortality_validation.py --bootstrap`

## Out-Of-Fold Public Validation

The stricter public evaluation path was then run with `5`-fold out-of-fold calibration, writing:

- `data/outputs/public_clock_2009_2010_v2_scored_oof5.csv`

Observed out-of-fold results:

- linked participants: `2103`
- deaths observed: `143`
- mortality rate: `0.0680`
- c-statistic using `surrogate_score`: `0.7592`
- 95 percent CI for `surrogate_score`: `0.7221` to `0.7963`
- c-statistic using `bio_age`: `0.7538`
- 95 percent CI for `bio_age`: `0.7138` to `0.7872`
- c-statistic using residualized `age_acceleration`: `0.5785`
- 95 percent CI for `age_acceleration`: `0.5351` to `0.6184`

Out-of-fold bio-age quartile mortality:

- Q1 mean `33.94`: `0.0095`
- Q2 mean `42.56`: `0.0362`
- Q3 mean `51.26`: `0.0800`
- Q4 mean `59.01`: `0.1458`

Out-of-fold residualized age-acceleration quartile mortality:

- Q1 mean `-10.08`: `0.0381`
- Q2 mean `-2.97`: `0.0667`
- Q3 mean `2.85`: `0.0838`
- Q4 mean `10.11`: `0.0833`

Bio-age quartile mortality:

- Q1 mean `34.03`: `0.0095`
- Q2 mean `42.54`: `0.0305`
- Q3 mean `51.32`: `0.0800`
- Q4 mean `58.91`: `0.1515`

Residualized age-acceleration quartile mortality:

- Q1 mean `-9.91`: `0.0343`
- Q2 mean `-2.91`: `0.0724`
- Q3 mean `2.83`: `0.0819`
- Q4 mean `9.94`: `0.0833`

## Important Compromises

This is a real public clock, but not the ideal full-spec clock.

Main compromises:

- fitness is a public proxy, not direct `VO2max`
- kidney function uses a public creatinine-and-albuminuria proxy instead of `Cystatin C`
- central adiposity uses waist-to-height ratio, not visceral fat
- the clock is calibrated to chronological age in this public cohort, even though it is now also validated against public linked mortality

## New Rigorous Workflow Support

The workspace now also supports a stricter public evaluation path:

- out-of-fold scoring with `run_clock_calibration.py --oof-folds`
- bootstrap c-statistic confidence intervals with `run_public_mortality_validation.py --bootstrap`

That means future reported public metrics can be produced with cleaner calibration-validation separation than the original in-sample run recorded above.

## Why This Is The Best Public Version So Far

It is the first path in this project that simultaneously delivers:

- real lung function
- direct ApoB
- direct CRP
- direct HbA1c
- mortality-linked validation
- adult sample size above two thousand

That makes it materially stronger than the earlier tiny NHANES 2001-2002 fallback run.
