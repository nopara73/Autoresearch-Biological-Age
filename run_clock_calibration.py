from __future__ import annotations

import argparse

from calibration import calibrate_biological_age, synthetic_demo_participants, write_scored_csv
from clock_formulas import named_clock_formulas
from nhanes_loader import load_harmonized_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Calibrate an expanded-panel surrogate score into bio_age and age_acceleration.")
    parser.add_argument("--input", help="Path to a harmonized CSV created by prepare_nhanes_harmonized.py.")
    parser.add_argument("--output", help="Optional output CSV path for scored participants.")
    parser.add_argument("--formula", default="Clock_logistic_default", choices=sorted(named_clock_formulas().keys()))
    parser.add_argument("--synthetic-demo", type=int, help="Use synthetic demo participants instead of a real harmonized dataset.")
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
    _, scored = calibrate_biological_age(participants, formula)

    print(f"Participants: {len(scored)}")
    print(f"Formula: {args.formula}")
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
