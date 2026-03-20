from __future__ import annotations

import argparse

from mortality_validation import join_scored_with_mortality, mortality_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a scored public clock cohort against NHANES linked mortality.")
    parser.add_argument("--scored", required=True, help="Path to scored clock CSV.")
    parser.add_argument("--mortality", required=True, help="Path to NHANES public linked mortality DAT file.")
    parser.add_argument("--bootstrap", type=int, default=0, help="Bootstrap iterations for c-stat confidence intervals.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    joined = join_scored_with_mortality(args.scored, args.mortality)
    summary = mortality_summary(joined, bootstrap_iterations=args.bootstrap)

    print(f"Participants linked: {summary['participants']}")
    print(f"Deaths observed: {summary['deaths']}")
    print(f"Mortality rate: {summary['mortality_rate']:.4f}")
    print(f"C-stat surrogate_score: {summary['c_stat_surrogate']:.4f}")
    if summary["c_stat_surrogate_ci"]:
        print(f"  95% CI: {summary['c_stat_surrogate_ci'][0]:.4f} to {summary['c_stat_surrogate_ci'][1]:.4f}")
    print(f"C-stat bio_age: {summary['c_stat_bio_age']:.4f}")
    if summary["c_stat_bio_age_ci"]:
        print(f"  95% CI: {summary['c_stat_bio_age_ci'][0]:.4f} to {summary['c_stat_bio_age_ci'][1]:.4f}")
    print(f"C-stat age_acceleration: {summary['c_stat_age_accel']:.4f}")
    if summary["c_stat_age_accel_ci"]:
        print(f"  95% CI: {summary['c_stat_age_accel_ci'][0]:.4f} to {summary['c_stat_age_accel_ci'][1]:.4f}")

    print("Bio-age quartile mortality:")
    for row in summary["bio_age_quartiles"]:
        print(
            f"  Q{int(row['bucket'])}: n={int(row['n'])} "
            f"mean={row['mean_value']:.2f} mortality={row['mortality_rate']:.4f}"
        )

    print("Age-acceleration quartile mortality:")
    for row in summary["age_accel_quartiles"]:
        print(
            f"  Q{int(row['bucket'])}: n={int(row['n'])} "
            f"mean={row['mean_value']:.2f} mortality={row['mortality_rate']:.4f}"
        )


if __name__ == "__main__":
    main()
