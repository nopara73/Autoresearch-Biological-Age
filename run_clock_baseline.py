from __future__ import annotations

from clock_formulas import named_clock_formulas
from clock_verification import ClockVerificationConfig, ClockVerificationReport, evaluate_clock_formula


def format_component(label: str, score: float, penalty: float, worst_violation: float) -> str:
    return (
        f"  {label:<13} score={score:>10.4f} "
        f"penalty={penalty:>10.4f} "
        f"worst={worst_violation:>10.4f}"
    )


def print_worst_cases(report: ClockVerificationReport) -> None:
    mono_case = report.monotonicity.details
    if mono_case:
        print(f"  worst_mono    {mono_case['field']} derivative={mono_case['derivative']:.4f}")

    pair_case = report.pairs.details.get("worst_case", {})
    if pair_case:
        print(
            "  worst_pair    "
            f"{pair_case['label']} healthy={pair_case['healthy_risk']:.4f} worse={pair_case['worse_risk']:.4f}"
        )

    smooth_case = report.smoothness.details
    if smooth_case:
        print(f"  worst_smooth  {smooth_case['field']} slope={smooth_case['slope']:.4f} limit={smooth_case['limit']:.4f}")


def main() -> None:
    config = ClockVerificationConfig()
    reports: list[tuple[str, ClockVerificationReport]] = []

    print("Expanded ACM clock baseline comparison")
    print("=" * 38)
    print(f"sample_size={config.sample_size} random_pair_count={config.random_pair_count} seed={config.seed}")
    print()

    for name, formula in named_clock_formulas().items():
        reports.append((name, evaluate_clock_formula(formula, config)))

    reports.sort(key=lambda item: item[1].total_score, reverse=True)

    for name, report in reports:
        print(name)
        print(f"  total_score   {report.total_score:>10.4f}")
        print(format_component("monotonicity", report.monotonicity.score, report.monotonicity.penalty, report.monotonicity.worst_violation))
        print(format_component("pairs", report.pairs.score, report.pairs.penalty, report.pairs.worst_violation))
        print(format_component("smoothness", report.smoothness.score, report.smoothness.penalty, report.smoothness.worst_violation))
        print(format_component("bounds", report.bounds.score, report.bounds.penalty, report.bounds.worst_violation))
        print(format_component("consistency", report.consistency.score, report.consistency.penalty, report.consistency.worst_violation))
        print(f"  pair_failures {report.pairs.details['failures']}/{report.pairs.details['tested_pairs']}")
        print(
            "  reference_risk "
            f"{report.consistency.details['reference_risk']:.4f} "
            f"severe_risk {report.consistency.details['severe_risk']:.4f}"
        )
        print_worst_cases(report)
        print()

    best_name, best_report = reports[0]
    print(f"Best expanded-panel structural score: {best_name} ({best_report.total_score:.4f})")


if __name__ == "__main__":
    main()
