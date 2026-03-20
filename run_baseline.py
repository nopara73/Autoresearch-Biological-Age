from __future__ import annotations

from formulas import named_formulas
from verification import VerificationConfig, VerificationReport, evaluate_formula


def format_component(label: str, score: float, penalty: float, worst_violation: float) -> str:
    return (
        f"  {label:<13} score={score:>10.4f} "
        f"penalty={penalty:>10.4f} "
        f"worst={worst_violation:>10.4f}"
    )


def print_worst_cases(report: VerificationReport) -> None:
    monotonicity_case = report.monotonicity.details
    if monotonicity_case:
        print(
            "  worst_mono    "
            f"{monotonicity_case['variable']} "
            f"derivative={monotonicity_case['derivative']:.4f}"
        )

    pair_case = report.pairs.details.get("worst_case", {})
    if pair_case:
        print(
            "  worst_pair    "
            f"{pair_case['label']} "
            f"healthy={pair_case['healthy_risk']:.4f} "
            f"worse={pair_case['worse_risk']:.4f}"
        )

    smoothness_case = report.smoothness.details
    if smoothness_case:
        print(
            "  worst_smooth  "
            f"{smoothness_case['variable']} "
            f"slope={smoothness_case['slope']:.4f} "
            f"limit={smoothness_case['limit']:.4f}"
        )


def main() -> None:
    config = VerificationConfig()
    reports: list[tuple[str, VerificationReport]] = []

    print("Structural surrogate baseline comparison")
    print("=" * 40)
    print(f"sample_size={config.sample_size} random_pair_count={config.random_pair_count} seed={config.seed}")
    print()

    for name, formula in named_formulas().items():
        report = evaluate_formula(formula, config)
        reports.append((name, report))

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
    print(f"Best structural score: {best_name} ({best_report.total_score:.4f})")


if __name__ == "__main__":
    main()
