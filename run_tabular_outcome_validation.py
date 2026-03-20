from __future__ import annotations

import argparse

from mortality_validation import join_scored_with_tabular_outcomes, outcome_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a scored clock cohort against a generic tabular outcome file.")
    parser.add_argument("--scored", required=True, help="Path to scored clock CSV.")
    parser.add_argument("--outcomes", required=True, help="Path to tabular outcome CSV.")
    parser.add_argument("--id-col", required=True, help="Outcome-table participant ID column.")
    parser.add_argument("--event-col", required=True, help="Outcome-table binary event column.")
    parser.add_argument("--followup-col", help="Optional follow-up duration column.")
    parser.add_argument("--bootstrap", type=int, default=0, help="Bootstrap iterations for c-stat confidence intervals.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    joined = join_scored_with_tabular_outcomes(
        scored_path=args.scored,
        outcomes_path=args.outcomes,
        id_col=args.id_col,
        event_col=args.event_col,
        followup_col=args.followup_col,
    )
    summary = outcome_summary(joined, bootstrap_iterations=args.bootstrap)

    print(f"Joined participants: {summary['participants']}")
    print(f"Events: {summary['events']}")
    print(f"Event rate: {summary['event_rate']:.4f}")
    print(f"C-stat surrogate_score: {summary['c_stat_surrogate']:.4f}")
    if summary["c_stat_surrogate_ci"]:
        print(f"  95% CI: {summary['c_stat_surrogate_ci'][0]:.4f} to {summary['c_stat_surrogate_ci'][1]:.4f}")
    print(f"C-stat bio_age: {summary['c_stat_bio_age']:.4f}")
    if summary["c_stat_bio_age_ci"]:
        print(f"  95% CI: {summary['c_stat_bio_age_ci'][0]:.4f} to {summary['c_stat_bio_age_ci'][1]:.4f}")
    print(f"C-stat age_acceleration: {summary['c_stat_age_accel']:.4f}")
    if summary["c_stat_age_accel_ci"]:
        print(f"  95% CI: {summary['c_stat_age_accel_ci'][0]:.4f} to {summary['c_stat_age_accel_ci'][1]:.4f}")

    print("\nBio age quartiles")
    for bucket in summary["bio_age_quartiles"]:
        print(
            f"  Q{bucket['bucket']}: n={bucket['n']}, "
            f"mean={bucket['mean_value']:.2f}, event_rate={bucket['event_rate']:.4f}"
        )

    print("\nAge acceleration quartiles")
    for bucket in summary["age_accel_quartiles"]:
        print(
            f"  Q{bucket['bucket']}: n={bucket['n']}, "
            f"mean={bucket['mean_value']:.2f}, event_rate={bucket['event_rate']:.4f}"
        )


if __name__ == "__main__":
    main()
