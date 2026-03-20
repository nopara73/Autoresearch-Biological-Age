from __future__ import annotations

import argparse

from calibration import calibrate_biological_age, calibrate_biological_age_oof, synthetic_demo_participants, write_scored_csv
from clock_formulas import named_clock_formulas
from harmonized_dataset import load_harmonized_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Calibrate an expanded-panel surrogate score into bio_age and age_acceleration.")
    parser.add_argument("--input", help="Path to a harmonized CSV created by prepare_nhanes_harmonized.py.")
    parser.add_argument("--output", help="Optional output CSV path for scored participants.")
    parser.add_argument("--formula", default="Clock_logistic_default", choices=sorted(named_clock_formulas().keys()))
    parser.add_argument("--synthetic-demo", type=int, help="Use synthetic demo participants instead of a real harmonized dataset.")
    parser.add_argument("--oof-folds", type=int, default=0, help="Use out-of-fold calibration with the given number of folds.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for out-of-fold splits.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.synthetic_demo is not None:
        participants = synthetic_demo_participants(args.synthetic_demo)
    elif args.input:
        participants = load_harmonized_csv(args.input)
    else:
        parser.error("Provide either --input or --synthetic-demo.")

    formula = named_clock_formulas()[args.formula]
    if args.oof_folds and args.oof_folds > 1:
        scored = calibrate_biological_age_oof(participants, formula, n_folds=args.oof_folds, seed=args.seed)
        mode = f"oof_{args.oof_folds}_fold"
    else:
        _, scored = calibrate_biological_age(participants, formula)
        mode = "in_sample"

    print(f"Participants: {len(scored)}")
    print(f"Formula: {args.formula}")
    print(f"Calibration mode: {mode}")
    print(
        "Mean age acceleration: "
        f"{sum(row.age_acceleration for row in scored) / max(len(scored), 1):.4f}"
    )
    print(
        "Mean surrogate score: "
        f"{sum(row.surrogate_score for row in scored) / max(len(scored), 1):.4f}"
    )

    if args.output:
        write_scored_csv(scored, args.output)
        print(f"Wrote: {args.output}")


if __name__ == "__main__":
    main()
