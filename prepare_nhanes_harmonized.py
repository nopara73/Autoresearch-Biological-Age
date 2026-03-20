from __future__ import annotations

import argparse

from nhanes_loader import harmonize_nhanes_rows, merge_component_rows, write_harmonized_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merge raw NHANES component CSVs and emit a harmonized clock-ready CSV.")
    parser.add_argument("--demo", required=True, help="Path to DEMO component CSV.")
    parser.add_argument("--cvx", required=True, help="Path to cardiovascular fitness CSV.")
    parser.add_argument("--bmx", required=True, help="Path to body measures CSV.")
    parser.add_argument("--glyco", required=True, help="Path to glycohemoglobin CSV.")
    parser.add_argument("--lipids", required=True, help="Path to lipid CSV.")
    parser.add_argument("--blood-pressure", required=True, help="Path to blood pressure CSV.")
    parser.add_argument("--cystatin", required=True, help="Path to cystatin C CSV.")
    parser.add_argument("--crp", required=True, help="Path to CRP CSV.")
    parser.add_argument("--spirometry", required=True, help="Path to spirometry CSV.")
    parser.add_argument("--output", required=True, help="Output path for harmonized CSV.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    merged_rows = merge_component_rows(
        {
            "DEMO": args.demo,
            "CVX": args.cvx,
            "BMX": args.bmx,
            "GHB": args.glyco,
            "LIPIDS": args.lipids,
            "BPX": args.blood_pressure,
            "SSCYST": args.cystatin,
            "CRP": args.crp,
            "SPX": args.spirometry,
        }
    )
    participants = harmonize_nhanes_rows(merged_rows)
    write_harmonized_csv(participants, args.output)

    print(f"Merged rows: {len(merged_rows)}")
    print(f"Harmonized participants: {len(participants)}")
    print(f"Wrote: {args.output}")


if __name__ == "__main__":
    main()
