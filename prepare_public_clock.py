from __future__ import annotations

import argparse

from public_clock_loader import prepare_public_clock_dataset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the strongest currently runnable public NHANES clock cohort.")
    parser.add_argument("--demo", required=True, help="Path to DEMO_F CSV.")
    parser.add_argument("--bmx", required=True, help="Path to BMX_F CSV.")
    parser.add_argument("--blood-pressure", required=True, help="Path to BPX_F CSV.")
    parser.add_argument("--spirometry", required=True, help="Path to SPX_F CSV.")
    parser.add_argument("--glyco", required=True, help="Path to GHB_F CSV.")
    parser.add_argument("--apob", required=True, help="Path to APOB_F CSV.")
    parser.add_argument("--biopro", required=True, help="Path to BIOPRO_F CSV.")
    parser.add_argument("--alb-cr", required=True, help="Path to ALB_CR_F CSV.")
    parser.add_argument("--crp", required=True, help="Path to CRP_F CSV.")
    parser.add_argument("--physical-activity", required=True, help="Path to PAQ_F CSV.")
    parser.add_argument("--output", required=True, help="Output harmonized clock CSV path.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    merged_rows, participants = prepare_public_clock_dataset(
        {
            "DEMO": args.demo,
            "BMX": args.bmx,
            "BPX": args.blood_pressure,
            "SPX": args.spirometry,
            "GHB": args.glyco,
            "APOB": args.apob,
            "BIOPRO": args.biopro,
            "ALBCR": args.alb_cr,
            "CRP": args.crp,
            "PAQ": args.physical_activity,
        },
        args.output,
    )
    print(f"Merged rows: {merged_rows}")
    print(f"Harmonized participants: {participants}")
    print(f"Wrote: {args.output}")


if __name__ == "__main__":
    main()
