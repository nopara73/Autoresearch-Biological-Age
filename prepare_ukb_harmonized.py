from __future__ import annotations

import argparse

from ukb_loader import prepare_ukb_harmonized


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Harmonize a UK Biobank export into the clock-ready CSV format.")
    parser.add_argument("--input", required=True, help="Path to a UK Biobank export CSV.")
    parser.add_argument("--output", required=True, help="Output path for the harmonized clock CSV.")
    parser.add_argument("--report", help="Optional output path for a JSON harmonization QA report.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    row_count, participant_count = prepare_ukb_harmonized(args.input, args.output, report_path=args.report)
    print(f"Input rows: {row_count}")
    print(f"Harmonized participants: {participant_count}")
    print(f"Wrote: {args.output}")
    if args.report:
        print(f"QA report: {args.report}")


if __name__ == "__main__":
    main()
