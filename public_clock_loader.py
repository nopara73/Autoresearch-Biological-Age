from __future__ import annotations

import math
from typing import Iterable

from clock_features import ClockProfile, clamp_clock_profile
from harmonized_dataset import HarmonizedParticipant, read_csv_rows, write_harmonized_csv


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


def _weekly_activity_minutes(row: dict[str, str]) -> float:
    def block(participates_var: str, days_var: str, minutes_var: str, weight: float = 1.0) -> float:
        participates = _parse_float(row.get(participates_var))
        days = _parse_float(row.get(days_var))
        minutes = _parse_float(row.get(minutes_var))
        if participates in (2.0, 7.0, 9.0) or days is None or minutes is None:
            return 0.0
        return max(days, 0.0) * max(minutes, 0.0) * weight

    return (
        block("PAQ605", "PAQ610", "PAD615", weight=2.0)
        + block("PAQ620", "PAQ625", "PAD630", weight=1.0)
        + block("PAQ635", "PAQ640", "PAD645", weight=1.0)
        + block("PAQ650", "PAQ655", "PAD660", weight=2.0)
        + block("PAQ665", "PAQ670", "PAD675", weight=1.0)
    )


def _fitness_proxy(weekly_activity_minutes: float, resting_pulse: float | None) -> tuple[float | None, str]:
    if resting_pulse is None:
        return None, "missing"
    activity_term = 6.0 * math.log1p(weekly_activity_minutes / 150.0)
    pulse_term = -0.18 * (resting_pulse - 70.0)
    return 38.0 + activity_term + pulse_term, "activity_plus_resting_pulse"


def _kidney_proxy(age: float, sex_code: float | None, serum_creatinine: float | None, urine_acr_mg_g: float | None) -> tuple[float | None, str]:
    if serum_creatinine is None or sex_code not in (1.0, 2.0):
        return None, "missing"

    female = sex_code == 2.0
    kappa = 0.7 if female else 0.9
    alpha = -0.241 if female else -0.302
    ratio = serum_creatinine / kappa
    egfr = (
        142.0
        * (min(ratio, 1.0) ** alpha)
        * (max(ratio, 1.0) ** -1.200)
        * (0.9938**age)
        * (1.012 if female else 1.0)
    )

    gfr_deficit = max((90.0 - egfr) / 15.0, 0.0)
    acr_deficit = 0.0
    if urine_acr_mg_g is not None:
        acr_deficit = max(math.log1p(urine_acr_mg_g) / math.log(10.0) - 1.0, 0.0)

    kidney_equivalent = 0.85 + (0.10 * gfr_deficit) + (0.08 * acr_deficit)
    label = "eGFR_plus_ACR" if urine_acr_mg_g is not None else "eGFR_only"
    return kidney_equivalent, label


def _central_adiposity_proxy(waist_cm: float, height_cm: float | None) -> tuple[float, str]:
    if height_cm is not None and height_cm > 0:
        return waist_cm / height_cm, "waist_to_height_ratio"
    burden_units = (waist_cm - 85.0) / 15.0
    return 0.48 + (0.08 * burden_units), "waist_circumference_equivalent"


def _lung_proxy(fev1_ml: float | None, fvc_ml: float | None) -> tuple[float | None, str]:
    if fev1_ml is not None:
        return fev1_ml / 1000.0, "FEV1"
    if fvc_ml is not None:
        burden_units = (4500.0 - fvc_ml) / 900.0
        return 3.5 - (0.6 * burden_units), "FVC_equivalent"
    return None, "missing"


def harmonize_public_clock_row(row: dict[str, str]) -> HarmonizedParticipant | None:
    seqn = row.get("SEQN")
    age = _parse_float(row.get("RIDAGEYR"))
    sex_code = _parse_float(row.get("RIAGENDR"))
    waist_cm = _parse_float(row.get("BMXWAIST"))
    height_cm = _parse_float(row.get("BMXHT"))
    glycemia = _parse_float(row.get("LBXGH"))
    apob = _parse_float(row.get("LBXAPB"))
    systolic = _mean_available(
        [
            _parse_float(row.get("BPXSY1")),
            _parse_float(row.get("BPXSY2")),
            _parse_float(row.get("BPXSY3")),
            _parse_float(row.get("BPXSY4")),
        ]
    )
    resting_pulse = _mean_available([_parse_float(row.get("BPXPLS")), _parse_float(row.get("BPXPULS"))])
    weekly_activity = _weekly_activity_minutes(row)
    fitness, fitness_proxy = _fitness_proxy(weekly_activity, resting_pulse)
    kidney, kidney_proxy = _kidney_proxy(
        age=age if age is not None else 0.0,
        sex_code=sex_code,
        serum_creatinine=_parse_float(row.get("LBXSCR")),
        urine_acr_mg_g=_parse_float(row.get("URDACT")),
    )
    inflammation = _parse_float(row.get("LBXCRP"))
    fev1 = _parse_float(row.get("SPXNFEV1"))
    fvc = _parse_float(row.get("SPXNFVC"))

    if seqn is None or age is None or age < 20.0 or waist_cm is None or glycemia is None or apob is None or systolic is None or fitness is None or kidney is None or inflammation is None:
        return None

    central_adiposity, central_proxy = _central_adiposity_proxy(waist_cm, height_cm)
    lung_function, lung_proxy = _lung_proxy(fev1, fvc)
    if lung_function is None:
        return None

    profile = clamp_clock_profile(
        ClockProfile(
            fitness=fitness,
            central_adiposity=central_adiposity,
            glycemia=glycemia,
            atherogenic_burden=apob,
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
        central_adiposity_proxy=f"{central_proxy}|{fitness_proxy}|{kidney_proxy}",
        atherogenic_proxy="ApoB_direct",
        lung_proxy=lung_proxy,
    )


def harmonize_public_clock_rows(rows: list[dict[str, str]]) -> list[HarmonizedParticipant]:
    participants: list[HarmonizedParticipant] = []
    for row in rows:
        participant = harmonize_public_clock_row(row)
        if participant is not None:
            participants.append(participant)
    return participants


def prepare_public_clock_dataset(component_paths: dict[str, str], output_path: str) -> tuple[int, int]:
    merged_rows = merge_component_rows(component_paths)
    participants = harmonize_public_clock_rows(merged_rows)
    write_harmonized_csv(participants, output_path)
    return len(merged_rows), len(participants)
