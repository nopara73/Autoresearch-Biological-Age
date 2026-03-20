from __future__ import annotations

import json
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


def _normalized_key(key: str) -> str:
    return key.lower().replace("-", "_").replace(" ", "_")


def _first_alias(row: dict[str, str], aliases: tuple[str, ...], token_groups: tuple[tuple[str, ...], ...] = ()) -> float | None:
    normalized = {_normalized_key(key): key for key in row.keys()}
    for alias in aliases:
        key = normalized.get(_normalized_key(alias))
        if key:
            value = _parse_float(row.get(key))
            if value is not None:
                return value

    for group in token_groups:
        for raw_key in row.keys():
            lowered = _normalized_key(raw_key)
            if all(token in lowered for token in group):
                value = _parse_float(row.get(raw_key))
                if value is not None:
                    return value
    return None


def _first_text_alias(row: dict[str, str], aliases: tuple[str, ...], token_groups: tuple[tuple[str, ...], ...] = ()) -> str | None:
    normalized = {_normalized_key(key): key for key in row.keys()}
    for alias in aliases:
        key = normalized.get(_normalized_key(alias))
        if key:
            value = str(row.get(key, "")).strip()
            if value:
                return value

    for group in token_groups:
        for raw_key in row.keys():
            lowered = _normalized_key(raw_key)
            if all(token in lowered for token in group):
                value = str(row.get(raw_key, "")).strip()
                if value:
                    return value
    return None


def _all_aliases(row: dict[str, str], aliases: tuple[str, ...], token_groups: tuple[tuple[str, ...], ...] = ()) -> list[float]:
    values: list[float] = []
    used_keys: set[str] = set()
    normalized = {_normalized_key(key): key for key in row.keys()}

    for alias in aliases:
        key = normalized.get(_normalized_key(alias))
        if key and key not in used_keys:
            value = _parse_float(row.get(key))
            if value is not None:
                values.append(value)
                used_keys.add(key)

    for group in token_groups:
        for raw_key in row.keys():
            lowered = _normalized_key(raw_key)
            if raw_key in used_keys:
                continue
            if all(token in lowered for token in group):
                value = _parse_float(row.get(raw_key))
                if value is not None:
                    values.append(value)
                    used_keys.add(raw_key)
    return values


def _equivalent_central_adiposity(visceral_adipose_tissue: float | None, waist_cm: float | None, height_cm: float | None) -> tuple[float | None, str]:
    if visceral_adipose_tissue is not None:
        burden_units = (visceral_adipose_tissue - 3.5) / 1.5
        return 0.48 + (0.08 * burden_units), "visceral_adipose_tissue_equivalent"
    if waist_cm is not None and height_cm is not None and height_cm > 0:
        return waist_cm / height_cm, "waist_to_height_ratio"
    if waist_cm is not None:
        burden_units = (waist_cm - 85.0) / 15.0
        return 0.48 + (0.08 * burden_units), "waist_circumference_equivalent"
    return None, "missing"


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
    return None, "missing"


def _extract_ukb_values(row: dict[str, str]) -> dict[str, object]:
    seqn = _first_text_alias(
        row,
        aliases=("eid", "participant_id"),
        token_groups=(("eid",), ("participant", "id")),
    ) or ""
    age = _first_alias(
        row,
        aliases=("f.21022.0.0", "age_at_recruitment", "age"),
        token_groups=(("age", "recruitment"),),
    )
    fitness = _first_alias(
        row,
        aliases=("cardiorespiratory_fitness", "estimated_crf", "vo2max", "vo2_max"),
        token_groups=(("cardiorespiratory", "fitness"), ("estimated", "crf"), ("vo2", "max")),
    )
    visceral_adipose_tissue = _first_alias(
        row,
        aliases=("f.22407.2.0", "visceral_adipose_tissue", "vat"),
        token_groups=(("visceral", "adipose"),),
    )
    waist_cm = _first_alias(
        row,
        aliases=("f.48.0.0", "waist_circumference", "waist"),
        token_groups=(("waist", "circumference"),),
    )
    height_cm = _first_alias(
        row,
        aliases=("standing_height", "height"),
        token_groups=(("standing", "height"), ("height", "cm")),
    )
    glycemia = _first_alias(
        row,
        aliases=("f.30750.0.0", "hba1c", "glycated_haemoglobin"),
        token_groups=(("glycated", "haemoglobin"), ("hba1c",)),
    )
    apob = _first_alias(
        row,
        aliases=("f.30640.0.0", "apob", "apolipoprotein_b"),
        token_groups=(("apolipoprotein", "b"),),
    )
    total_cholesterol = _first_alias(
        row,
        aliases=("total_cholesterol",),
        token_groups=(("total", "cholesterol"),),
    )
    hdl_cholesterol = _first_alias(
        row,
        aliases=("hdl_cholesterol",),
        token_groups=(("hdl", "cholesterol"),),
    )
    systolic = _mean_available(
        _all_aliases(
            row,
            aliases=("f.4080.0.0", "f.4080.1.0", "systolic_blood_pressure"),
            token_groups=(("systolic", "blood", "pressure"),),
        )
    )
    kidney = _first_alias(
        row,
        aliases=("f.30720.0.0", "cystatin_c"),
        token_groups=(("cystatin", "c"),),
    )
    inflammation = _first_alias(
        row,
        aliases=("f.30710.0.0", "crp", "c_reactive_protein"),
        token_groups=(("c", "reactive", "protein"), ("crp",)),
    )
    fev1 = _first_alias(
        row,
        aliases=("fev1", "forced_expiratory_volume_in_1_second"),
        token_groups=(("forced", "expiratory", "volume"), ("fev1",)),
    )
    fvc = _first_alias(
        row,
        aliases=("fvc", "forced_vital_capacity"),
        token_groups=(("forced", "vital", "capacity"), ("fvc",)),
    )
    return {
        "seqn": seqn,
        "age": age,
        "fitness": fitness,
        "visceral_adipose_tissue": visceral_adipose_tissue,
        "waist_cm": waist_cm,
        "height_cm": height_cm,
        "glycemia": glycemia,
        "apob": apob,
        "total_cholesterol": total_cholesterol,
        "hdl_cholesterol": hdl_cholesterol,
        "systolic": systolic,
        "kidney": kidney,
        "inflammation": inflammation,
        "fev1": fev1,
        "fvc": fvc,
    }


def harmonize_ukb_row_with_reason(row: dict[str, str]) -> tuple[HarmonizedParticipant | None, str]:
    values = _extract_ukb_values(row)
    seqn = str(values["seqn"])
    age = values["age"]
    fitness = values["fitness"]
    glycemia = values["glycemia"]
    systolic = values["systolic"]
    kidney = values["kidney"]
    inflammation = values["inflammation"]

    if not seqn or age is None or fitness is None or glycemia is None or systolic is None or kidney is None or inflammation is None:
        if not seqn:
            return None, "missing_participant_id"
        if age is None:
            return None, "missing_age"
        if fitness is None:
            return None, "missing_fitness"
        if glycemia is None:
            return None, "missing_glycemia"
        if systolic is None:
            return None, "missing_blood_pressure"
        if kidney is None:
            return None, "missing_kidney"
        return None, "missing_inflammation"

    central_adiposity, central_proxy = _equivalent_central_adiposity(
        values["visceral_adipose_tissue"], values["waist_cm"], values["height_cm"]
    )
    atherogenic_burden, atherogenic_proxy = _equivalent_atherogenic_burden(
        values["apob"], values["total_cholesterol"], values["hdl_cholesterol"]
    )
    lung_function, lung_proxy = _equivalent_lung_function(values["fev1"], values["fvc"])

    if central_adiposity is None or atherogenic_burden is None or lung_function is None:
        if central_adiposity is None:
            return None, "missing_central_adiposity"
        if atherogenic_burden is None:
            return None, "missing_atherogenic_burden"
        return None, "missing_lung_function"

    profile = clamp_clock_profile(
        ClockProfile(
            fitness=float(fitness),
            central_adiposity=central_adiposity,
            glycemia=float(glycemia),
            atherogenic_burden=atherogenic_burden,
            hemodynamic_stress=float(systolic),
            kidney_function=float(kidney),
            inflammation=float(inflammation),
            lung_function=lung_function,
        )
    )
    return (
        HarmonizedParticipant(
        seqn=seqn,
        chronological_age=float(age),
        profile=profile,
        central_adiposity_proxy=central_proxy,
        atherogenic_proxy=atherogenic_proxy,
        lung_proxy=lung_proxy,
        ),
        "ok",
    )


def harmonize_ukb_row(row: dict[str, str]) -> HarmonizedParticipant | None:
    participant, _ = harmonize_ukb_row_with_reason(row)
    return participant


def harmonize_ukb_rows(rows: list[dict[str, str]]) -> list[HarmonizedParticipant]:
    participants: list[HarmonizedParticipant] = []
    for row in rows:
        participant = harmonize_ukb_row(row)
        if participant is not None:
            participants.append(participant)
    return participants


def _header_matches(headers: list[str], aliases: tuple[str, ...], token_groups: tuple[tuple[str, ...], ...] = ()) -> list[str]:
    normalized = {_normalized_key(header): header for header in headers}
    matches: list[str] = []
    for alias in aliases:
        key = normalized.get(_normalized_key(alias))
        if key and key not in matches:
            matches.append(key)
    for raw_key in headers:
        lowered = _normalized_key(raw_key)
        if raw_key in matches:
            continue
        for group in token_groups:
            if all(token in lowered for token in group):
                matches.append(raw_key)
                break
    return matches


def generate_ukb_harmonization_report(rows: list[dict[str, str]], participants: list[HarmonizedParticipant], drop_reasons: dict[str, int]) -> dict[str, object]:
    headers = list(rows[0].keys()) if rows else []
    field_matches = {
        "participant_id": _header_matches(headers, ("eid", "participant_id"), (("participant", "id"),)),
        "age": _header_matches(headers, ("f.21022.0.0", "age_at_recruitment", "age"), (("age", "recruitment"),)),
        "fitness": _header_matches(headers, ("cardiorespiratory_fitness", "estimated_crf", "vo2max", "vo2_max"), (("cardiorespiratory", "fitness"), ("estimated", "crf"), ("vo2", "max"))),
        "central_adiposity": _header_matches(headers, ("f.22407.2.0", "visceral_adipose_tissue", "vat", "f.48.0.0", "waist_circumference", "waist"), (("visceral", "adipose"), ("waist", "circumference"))),
        "glycemia": _header_matches(headers, ("f.30750.0.0", "hba1c", "glycated_haemoglobin"), (("glycated", "haemoglobin"),)),
        "atherogenic_burden": _header_matches(headers, ("f.30640.0.0", "apob", "apolipoprotein_b", "total_cholesterol", "hdl_cholesterol"), (("apolipoprotein", "b"), ("total", "cholesterol"), ("hdl", "cholesterol"))),
        "hemodynamic_stress": _header_matches(headers, ("f.4080.0.0", "f.4080.1.0", "systolic_blood_pressure"), (("systolic", "blood", "pressure"),)),
        "kidney": _header_matches(headers, ("f.30720.0.0", "cystatin_c"), (("cystatin", "c"),)),
        "inflammation": _header_matches(headers, ("f.30710.0.0", "crp", "c_reactive_protein"), (("c", "reactive", "protein"), ("crp",))),
        "lung": _header_matches(headers, ("fev1", "forced_expiratory_volume_in_1_second", "fvc", "forced_vital_capacity"), (("forced", "expiratory", "volume"), ("forced", "vital", "capacity"))),
    }
    proxy_counts: dict[str, dict[str, int]] = {"central_adiposity": {}, "atherogenic_burden": {}, "lung_function": {}}
    for participant in participants:
        proxy_counts["central_adiposity"][participant.central_adiposity_proxy] = proxy_counts["central_adiposity"].get(participant.central_adiposity_proxy, 0) + 1
        proxy_counts["atherogenic_burden"][participant.atherogenic_proxy] = proxy_counts["atherogenic_burden"].get(participant.atherogenic_proxy, 0) + 1
        proxy_counts["lung_function"][participant.lung_proxy] = proxy_counts["lung_function"].get(participant.lung_proxy, 0) + 1
    return {
        "input_rows": len(rows),
        "harmonized_participants": len(participants),
        "drop_reasons": drop_reasons,
        "matched_headers": field_matches,
        "proxy_counts": proxy_counts,
    }


def prepare_ukb_harmonized(input_path: str, output_path: str, report_path: str | None = None) -> tuple[int, int]:
    rows = read_csv_rows(input_path)
    participants: list[HarmonizedParticipant] = []
    drop_reasons: dict[str, int] = {}
    for row in rows:
        participant, reason = harmonize_ukb_row_with_reason(row)
        if participant is not None:
            participants.append(participant)
        else:
            drop_reasons[reason] = drop_reasons.get(reason, 0) + 1
    write_harmonized_csv(participants, output_path)
    if report_path:
        report = generate_ukb_harmonization_report(rows, participants, drop_reasons)
        with open(report_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
    return len(rows), len(participants)
