# Age Calibration Plan

This file defines how the structurally valid surrogate score should be mapped to biological age and age acceleration.

## Principle

The structural surrogate is not itself a biological age clock.

It becomes a clock only after calibration against a real age-linked dataset.

For the first version, use chronological age as the calibration anchor and keep the surrogate score as the biologically interpretable latent quantity.

## Inputs

For each participant in the chosen dataset, produce:

- `surrogate_score`
- `chronological_age`

Optional later validation fields:

- mortality follow-up
- event indicators
- disease burden

## Recommended First Calibration

Use a monotone mapping from surrogate score to age:

1. compute the harmonized panel inputs
2. compute one surrogate score per participant
3. fit a monotone calibration function `bio_age = f(surrogate_score)`
4. define `age_acceleration = bio_age - chronological_age`

## Preferred Mapping Method

For v1, use monotone regression rather than a free-form nonlinear model.

Recommended order:

1. isotonic regression if enough sample size is available
2. monotone spline or quantile mapping if isotonic is too step-like
3. simple linear mapping only as a baseline comparison

Why:

- the score should map to age in one direction only
- monotone calibration preserves the score ordering learned by the structural surrogate
- it reduces the risk of overfitting a small or proxy-heavy dataset

## Healthy-Reference Option

If the dataset is large enough, fit the calibration on a healthier reference subset first, then project onto the full population.

Example healthy-reference filters:

- no known cardiovascular disease
- no diagnosed diabetes
- non-extreme inflammation
- non-extreme kidney dysfunction

This produces an age-equivalent scale closer to "expected biologic age under comparatively healthy aging" rather than a direct average-population age lookup.

## Output Definitions

The first clock outputs should be:

- `surrogate_score`: structurally selected ACM-like latent score
- `bio_age`: chronological-age-equivalent value from the calibration function
- `age_acceleration`: `bio_age - chronological_age`

Interpretation:

- positive `age_acceleration` means biologically older than chronological peers
- negative `age_acceleration` means biologically younger than chronological peers

## Minimum Validation Checks

Before trusting the first clock, check:

1. `bio_age` rises monotonically with chronological age
2. worse physiologic profiles receive older `bio_age`
3. `age_acceleration` is associated with worse follow-up outcomes if mortality linkage is available
4. the mapping is stable across sex and broad age bands

## Recommended Implementation Sequence

1. compute expanded-panel surrogate scores on the chosen dataset
2. fit a monotone age calibration
3. export `bio_age` and `age_acceleration`
4. run age-stratified sanity plots
5. if linked mortality is available, confirm that higher `age_acceleration` predicts higher risk

## Guardrail

Do not use chronological age inside the structural surrogate formula itself.

Chronological age is only the calibration target for turning a surrogate score into an age-like output. Keeping age out of the surrogate formula preserves the project goal of deriving biology from physiology first, then mapping it to an age scale afterward.
