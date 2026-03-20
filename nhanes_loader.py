from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from clock_features import ClockProfile, clamp_clock_profile


@dataclass(frozen=True)
class HarmonizedParticipant:
    seqn: str
    chronological_age: float
    profile: ClockProfile
    central_adiposity_proxy: str
    atherogenic_proxy: str
    lung_proxy: str

    def to_row(self) -> dict[str, str]:
        profile_dict = self.profile.to_dict()
        row = {
            "SEQN": self.seqn,
            "chronological_age": f"{self.chronological_age:.6f}",
            "central_adiposity_proxy": self.central_adiposity_proxy,
            "atherogenic_proxy": self.atherogenic_proxy,
            "lung_proxy": self.lung_proxy,
        }
        for key, value in profile_dict.items():
            row[key] = f"{value:.6f}"
        return row


def _parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    stripped = str(value).strip()
    if stripped == "":
        return None
    try:
        return float(stripped)
    except ValueError:
        return None


def _mean_available(values: Iterable[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return sum(present) / len(present)


def read_csv_rows(path: str) -> list[dict[str, str]]:
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def merge_component_rows(component_paths: dict[str, str]) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for component_name, path in component_paths.items():
        rows = read_csv_rows(path)
        for row in rows:
            seqn = row.get("SEQN")
            if not seqn:
                continue
            merged.setdefault(seqn, {"SEQN": seqn})
            for key, value in row.items():
                if key == "SEQN":
                    continue
                merged[seqn][f"{component_name}__{key}"] = value
                merged[seqn][key] = value
    return list(merged.values())


def _equivalent_central_adiposity(waist_cm: float, height_cm: float | None) -> tuple[float, str]:
    if height_cm is not None and height_cm > 0:
        return waist_cm / height_cm, "waist_to_height_ratio"
    burden_units = (waist_cm - 85.0) / 15.0
    return 0.48 + (0.08 * burden_units), "waist_circumference_equivalent"


def _equivalent_atherogenic_burden(apob: float | None, total_cholesterol: float | None, hdl_cholesterol: float | None) -> tuple[float | None, str]:
    if apob is not None:
        burden_units = (apob - 90.0) / 25.0
        return 110.0 + (30.0 * burden_units), "apoB_equivalent"
    if total_cholesterol is None or hdl_cholesterol is None:
        return None, "missing"
    return total_cholesterol - hdl_cholesterol, "non_HDL_cholesterol"


def _equivalent_lung_function(fev1: float | None, fvc: float | None) -> tuple[float | None, str]:
    if fev1 is not None:
        return fev1, "FEV1"
    if fvc is None:
        return None, "missing"
    burden_units = (4.5 - fvc) / 0.9
    return 3.5 - (0.6 * burden_units), "FVC_equivalent"


def harmonize_nhanes_row(row: dict[str, str]) -> HarmonizedParticipant | None:
    seqn = row.get("SEQN")
    age = _parse_float(row.get("RIDAGEYR"))
    fitness = _parse_float(row.get("CVDVOMAX"))
    waist_cm = _parse_float(row.get("BMXWAIST"))
    height_cm = _parse_float(row.get("BMXHT"))
    glycemia = _parse_float(row.get("LBXGH"))
    total_cholesterol = _parse_float(row.get("LBXTC"))
    hdl_cholesterol = _parse_float(row.get("LBXHDD"))
    apob = _parse_float(row.get("LBXAPB"))
    systolic = _mean_available(
        [
            _parse_float(row.get("BPXSY1")),
            _parse_float(row.get("BPXSY2")),
            _parse_float(row.get("BPXSY3")),
            _parse_float(row.get("BPXSY4")),
        ]
    )
    kidney = _parse_float(row.get("SSCYPC"))
    inflammation = _parse_float(row.get("LBXCRP")) or _parse_float(row.get("LBXHSCRP"))
    fev1 = _parse_float(row.get("SPXFEV1")) or _parse_float(row.get("FEV1"))
    fvc = _parse_float(row.get("SPXFVC")) or _parse_float(row.get("FVC"))

    if seqn is None or age is None or fitness is None or waist_cm is None or glycemia is None or systolic is None or kidney is None or inflammation is None:
        return None

    central_adiposity, central_proxy = _equivalent_central_adiposity(waist_cm, height_cm)
    atherogenic_burden, atherogenic_proxy = _equivalent_atherogenic_burden(apob, total_cholesterol, hdl_cholesterol)
    lung_function, lung_proxy = _equivalent_lung_function(fev1, fvc)

    if atherogenic_burden is None or lung_function is None:
        return None

    profile = clamp_clock_profile(
        ClockProfile(
            fitness=fitness,
            central_adiposity=central_adiposity,
            glycemia=glycemia,
            atherogenic_burden=atherogenic_burden,
            hemodynamic_stress=systolic,
            kidney_function=kidney,
            inflammation=inflammation,
            lung_function=lung_function,
        )
    )
    return HarmonizedParticipant(
        seqn=seqn,
        chronological_age=age,
        profile=profile,
        central_adiposity_proxy=central_proxy,
        atherogenic_proxy=atherogenic_proxy,
        lung_proxy=lung_proxy,
    )


def harmonize_nhanes_rows(rows: list[dict[str, str]]) -> list[HarmonizedParticipant]:
    participants: list[HarmonizedParticipant] = []
    for row in rows:
        participant = harmonize_nhanes_row(row)
        if participant is not None:
            participants.append(participant)
    return participants


def write_harmonized_csv(participants: list[HarmonizedParticipant], output_path: str) -> None:
    if not participants:
        raise ValueError("No harmonized participants available to write.")

    fieldnames = list(participants[0].to_row().keys())
    with open(output_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for participant in participants:
            writer.writerow(participant.to_row())


def load_harmonized_csv(path: str) -> list[HarmonizedParticipant]:
    rows = read_csv_rows(path)
    participants: list[HarmonizedParticipant] = []
    for row in rows:
        participants.append(
            HarmonizedParticipant(
                seqn=row["SEQN"],
                chronological_age=float(row["chronological_age"]),
                profile=ClockProfile(
                    fitness=float(row["fitness"]),
                    central_adiposity=float(row["central_adiposity"]),
                    glycemia=float(row["glycemia"]),
                    atherogenic_burden=float(row["atherogenic_burden"]),
                    hemodynamic_stress=float(row["hemodynamic_stress"]),
                    kidney_function=float(row["kidney_function"]),
                    inflammation=float(row["inflammation"]),
                    lung_function=float(row["lung_function"]),
                ),
                central_adiposity_proxy=row.get("central_adiposity_proxy", "unknown"),
                atherogenic_proxy=row.get("atherogenic_proxy", "unknown"),
                lung_proxy=row.get("lung_proxy", "unknown"),
            )
        )
    return participants
