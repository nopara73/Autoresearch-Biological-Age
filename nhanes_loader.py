from __future__ import annotations

from typing import Iterable

from clock_features import ClockProfile, clamp_clock_profile
from harmonized_dataset import HarmonizedParticipant, load_harmonized_csv, read_csv_rows, write_harmonized_csv


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
    if fvc is not None:
        burden_units = (4.5 - fvc) / 0.9
        return 3.5 - (0.6 * burden_units), "FVC_equivalent"
    # The public NHANES slice chosen for cystatin C and direct fitness does not
    # expose a matching spirometry component here, so use a neutral placeholder
    # rather than silently inventing signal from another domain.
    return 3.5, "neutral_placeholder"


def harmonize_nhanes_row(row: dict[str, str]) -> HarmonizedParticipant | None:
    seqn = row.get("SEQN")
    age = _parse_float(row.get("RIDAGEYR"))
    fitness = _parse_float(row.get("CVDVOMAX"))
    waist_cm = _parse_float(row.get("BMXWAIST"))
    height_cm = _parse_float(row.get("BMXHT"))
    glycemia = _parse_float(row.get("LBXGH"))
    total_cholesterol = _parse_float(row.get("LBXTC")) or _parse_float(row.get("LB2TC"))
    hdl_cholesterol = (
        _parse_float(row.get("LBXHDD"))
        or _parse_float(row.get("LBDHDD"))
        or _parse_float(row.get("LB2HDL"))
    )
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
    inflammation = (
        _parse_float(row.get("LBXCRP"))
        or _parse_float(row.get("LBXHSCRP"))
        or _parse_float(row.get("LB2CRP"))
    )
    fev1 = _parse_float(row.get("SPXFEV1")) or _parse_float(row.get("FEV1"))
    fvc = _parse_float(row.get("SPXFVC")) or _parse_float(row.get("FVC"))

    if seqn is None or age is None or fitness is None or waist_cm is None or glycemia is None or systolic is None or kidney is None or inflammation is None:
        return None

    central_adiposity, central_proxy = _equivalent_central_adiposity(waist_cm, height_cm)
    atherogenic_burden, atherogenic_proxy = _equivalent_atherogenic_burden(apob, total_cholesterol, hdl_cholesterol)
    lung_function, lung_proxy = _equivalent_lung_function(fev1, fvc)

    if atherogenic_burden is None:
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


