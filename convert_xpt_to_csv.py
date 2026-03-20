from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert one or more NHANES SAS XPT files to CSV.")
    parser.add_argument("inputs", nargs="+", help="Input XPT files.")
    parser.add_argument("--output-dir", required=True, help="Directory where CSV files will be written.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for input_path in args.inputs:
        source = Path(input_path)
        frame = pd.read_sas(source, format="xport")
        destination = output_dir / f"{source.stem}.csv"
        frame.to_csv(destination, index=False)
        print(f"Converted {source} -> {destination} ({len(frame)} rows)")


if __name__ == "__main__":
    main()
