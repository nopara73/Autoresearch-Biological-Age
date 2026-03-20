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

## How To Run

From the workspace root:

```bash
python run_baseline.py
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
