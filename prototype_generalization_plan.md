# Prototype Generalization Plan

This file defines how to evolve the current 4-variable proof of concept into the locked multi-system ACM-oriented clock without breaking the existing baseline harness.

Current prototype files:

- `formulas.py`
- `sampler.py`
- `verification.py`
- `run_baseline.py`

## Current Limitation

The current code hard-codes four inputs:

- `vo2max`
- `visceral_fat`
- `hba1c`
- `apob`

That is enough for the paper prototype but not enough for the locked v1 panel.

## Required Expansion

The next code revision should support these harmonized inputs:

- `fitness`
- `central_adiposity`
- `glycemia`
- `atherogenic_burden`
- `hemodynamic_stress`
- `kidney_function`
- `inflammation`
- `lung_function`

Chronological age should be handled separately for calibration, not as a direct risk input during structural search.

## File-Level Change Plan

### `formulas.py`

Replace the fixed `Profile` assumption with a generic clock profile structure.

Needed changes:

1. Introduce a `ClockProfile` dataclass containing the eight harmonized inputs.
2. Keep the existing 4-variable formulas for backward compatibility.
3. Add generalized formula families that operate on named transformed inputs rather than hard-coded `vo2max`, `visceral_fat`, `hba1c`, and `apob`.
4. Separate:
   - raw input harmonization
   - standardized offsets / deficits
   - formula family definitions

Recommended formula families for the expanded panel:

- additive or multiplicative reserve-burden
- dysregulation distance over all dimensions
- weakest-link slack across all dimensions
- constrained logistic surrogate with nonnegative burden terms

### `sampler.py`

Move from four-variable domain sampling to panel-driven sampling.

Needed changes:

1. Replace `DOMAIN_BOUNDS` with a variable-spec driven bounds table.
2. Generate synthetic profiles across all eight harmonized variables.
3. Expand curated pairs so each domain has targeted comparisons:
   - lung-only worsening
   - inflammation-only worsening
   - kidney-only worsening
   - multi-domain worsening

### `verification.py`

Refactor the verifier to operate on variable metadata rather than hard-coded field names.

Needed changes:

1. Replace the hard-coded derivative direction map with a per-variable direction map.
2. Make smoothness steps and limits configurable per harmonized variable.
3. Make reference and severe profiles panel-based rather than fixed 4-field objects.
4. Preserve the same structural components:
   - monotonicity
   - ordered pairs
   - smoothness
   - bounds
   - consistency

### `run_baseline.py`

Extend the runner to compare:

- the current 4-variable formulas
- expanded panel formula families
- any future searched candidates

It should also print the active panel definition and proxy policy so reports remain auditable.

## Migration Order

Implement the next coding pass in this order:

1. add a harmonized `ClockProfile`
2. add panel-driven bounds and direction metadata
3. port the verifier to panel-driven logic
4. re-express formula families in the harmonized input space
5. add dataset ingestion and harmonization from the chosen NHANES mapping
6. only then fit or search a new surrogate on the expanded panel

## Success Condition

The prototype is ready for calibration when a single runner can:

- ingest harmonized NHANES rows
- compute an expanded-panel surrogate score
- evaluate its structural validity
- export one scalar surrogate score per participant
