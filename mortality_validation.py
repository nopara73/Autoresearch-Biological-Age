from __future__ import annotations

import csv
from dataclasses import dataclass
from math import floor
import random


@dataclass(frozen=True)
class MortalityRecord:
    seqn: str
    eligstat: int
    mortstat: int
    ucod_leading: int | None
    permth_int: int | None
    permth_exm: int | None


@dataclass(frozen=True)
class JoinedMortalityRecord:
    seqn: str
    chronological_age: float
    surrogate_score: float
    bio_age: float
    age_acceleration: float
    mortstat: int
    permth_exm: int | None


@dataclass(frozen=True)
class JoinedOutcomeRecord:
    seqn: str
    chronological_age: float
    surrogate_score: float
    bio_age: float
    age_acceleration: float
    event: int
    followup: float | None


def _parse_int_field(text: str) -> int | None:
    stripped = text.strip()
    if stripped in ("", "."):
        return None
    return int(stripped)


def parse_public_mortality_dat(path: str) -> list[MortalityRecord]:
    records: list[MortalityRecord] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            seqn = line[0:6].strip()
            eligstat = _parse_int_field(line[14:15]) or 0
            mortstat = _parse_int_field(line[15:16]) or 0
            ucod_text = _parse_int_field(line[16:19])
            permth_int_text = _parse_int_field(line[42:45])
            permth_exm_text = _parse_int_field(line[45:48])
            records.append(
                MortalityRecord(
                    seqn=seqn,
                    eligstat=eligstat,
                    mortstat=mortstat,
                    ucod_leading=ucod_text,
                    permth_int=permth_int_text,
                    permth_exm=permth_exm_text,
                )
            )
    return records


def load_scored_clock(path: str) -> list[dict[str, str]]:
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _safe_int(value: str | None) -> int | None:
    if value is None:
        return None
    stripped = str(value).strip()
    if stripped in ("", "."):
        return None
    return int(float(stripped))


def _safe_float(value: str | None) -> float | None:
    if value is None:
        return None
    stripped = str(value).strip()
    if stripped in ("", "."):
        return None
    return float(stripped)


def join_scored_with_mortality(scored_path: str, mortality_path: str) -> list[JoinedMortalityRecord]:
    scored_rows = load_scored_clock(scored_path)
    mortality_rows = {record.seqn: record for record in parse_public_mortality_dat(mortality_path)}
    joined: list[JoinedMortalityRecord] = []
    for row in scored_rows:
        record = mortality_rows.get(str(int(float(row["SEQN"]))))
        if record is None or record.eligstat == 0:
            continue
        joined.append(
            JoinedMortalityRecord(
                seqn=row["SEQN"],
                chronological_age=float(row["chronological_age"]),
                surrogate_score=float(row["surrogate_score"]),
                bio_age=float(row["bio_age"]),
                age_acceleration=float(row["age_acceleration"]),
                mortstat=record.mortstat,
                permth_exm=record.permth_exm,
            )
        )
    return joined


def join_scored_with_tabular_outcomes(
    scored_path: str,
    outcomes_path: str,
    id_col: str,
    event_col: str,
    followup_col: str | None = None,
) -> list[JoinedOutcomeRecord]:
    scored_rows = load_scored_clock(scored_path)
    with open(outcomes_path, "r", encoding="utf-8-sig", newline="") as handle:
        outcome_rows = list(csv.DictReader(handle))

    outcome_map = {str(row[id_col]).strip(): row for row in outcome_rows if row.get(id_col) not in (None, "")}
    joined: list[JoinedOutcomeRecord] = []
    for row in scored_rows:
        seqn = row["SEQN"].strip()
        outcome = outcome_map.get(seqn)
        if outcome is None:
            continue
        event = _safe_int(outcome.get(event_col))
        if event is None:
            continue
        joined.append(
            JoinedOutcomeRecord(
                seqn=seqn,
                chronological_age=float(row["chronological_age"]),
                surrogate_score=float(row["surrogate_score"]),
                bio_age=float(row["bio_age"]),
                age_acceleration=float(row["age_acceleration"]),
                event=event,
                followup=_safe_float(outcome.get(followup_col)) if followup_col else None,
            )
        )
    return joined


def c_statistic(pairs: list[tuple[float, int]]) -> float:
    positives = [score for score, label in pairs if label == 1]
    negatives = [score for score, label in pairs if label == 0]
    if not positives or not negatives:
        return float("nan")
    concordant = 0.0
    total = 0
    for positive in positives:
        for negative in negatives:
            total += 1
            if positive > negative:
                concordant += 1.0
            elif positive == negative:
                concordant += 0.5
    return concordant / total


def bootstrap_c_statistic(
    pairs: list[tuple[float, int]],
    iterations: int = 200,
    seed: int = 42,
) -> tuple[float, float] | None:
    if iterations <= 0:
        return None
    rng = random.Random(seed)
    statistics: list[float] = []
    if not pairs:
        return None
    for _ in range(iterations):
        sample = [pairs[rng.randrange(len(pairs))] for _ in range(len(pairs))]
        stat = c_statistic(sample)
        if stat == stat:
            statistics.append(stat)
    if not statistics:
        return None
    statistics.sort()
    lower = statistics[int(0.025 * (len(statistics) - 1))]
    upper = statistics[int(0.975 * (len(statistics) - 1))]
    return lower, upper


def quantile_mortality(records: list[JoinedMortalityRecord], attribute: str, buckets: int = 4) -> list[dict[str, float]]:
    ordered = sorted(records, key=lambda item: getattr(item, attribute))
    if not ordered:
        return []
    bucket_size = max(1, floor(len(ordered) / buckets))
    results: list[dict[str, float]] = []
    for index in range(buckets):
        start = index * bucket_size
        end = len(ordered) if index == buckets - 1 else min((index + 1) * bucket_size, len(ordered))
        chunk = ordered[start:end]
        if not chunk:
            continue
        results.append(
            {
                "bucket": index + 1,
                "n": len(chunk),
                "mean_value": sum(getattr(item, attribute) for item in chunk) / len(chunk),
                "mortality_rate": sum(item.mortstat for item in chunk) / len(chunk),
            }
        )
    return results


def quantile_event_rate(records: list[JoinedOutcomeRecord], attribute: str, buckets: int = 4) -> list[dict[str, float]]:
    ordered = sorted(records, key=lambda item: getattr(item, attribute))
    if not ordered:
        return []
    bucket_size = max(1, floor(len(ordered) / buckets))
    results: list[dict[str, float]] = []
    for index in range(buckets):
        start = index * bucket_size
        end = len(ordered) if index == buckets - 1 else min((index + 1) * bucket_size, len(ordered))
        chunk = ordered[start:end]
        if not chunk:
            continue
        results.append(
            {
                "bucket": index + 1,
                "n": len(chunk),
                "mean_value": sum(getattr(item, attribute) for item in chunk) / len(chunk),
                "event_rate": sum(item.event for item in chunk) / len(chunk),
            }
        )
    return results


def mortality_summary(records: list[JoinedMortalityRecord], bootstrap_iterations: int = 0, seed: int = 42) -> dict[str, object]:
    mortality_rate = sum(record.mortstat for record in records) / max(len(records), 1)
    surrogate_pairs = [(record.surrogate_score, record.mortstat) for record in records]
    bio_age_pairs = [(record.bio_age, record.mortstat) for record in records]
    age_accel_pairs = [(record.age_acceleration, record.mortstat) for record in records]
    return {
        "participants": len(records),
        "deaths": sum(record.mortstat for record in records),
        "mortality_rate": mortality_rate,
        "c_stat_surrogate": c_statistic(surrogate_pairs),
        "c_stat_surrogate_ci": bootstrap_c_statistic(surrogate_pairs, iterations=bootstrap_iterations, seed=seed),
        "c_stat_bio_age": c_statistic(bio_age_pairs),
        "c_stat_bio_age_ci": bootstrap_c_statistic(bio_age_pairs, iterations=bootstrap_iterations, seed=seed + 1),
        "c_stat_age_accel": c_statistic(age_accel_pairs),
        "c_stat_age_accel_ci": bootstrap_c_statistic(age_accel_pairs, iterations=bootstrap_iterations, seed=seed + 2),
        "bio_age_quartiles": quantile_mortality(records, "bio_age"),
        "age_accel_quartiles": quantile_mortality(records, "age_acceleration"),
    }


def outcome_summary(records: list[JoinedOutcomeRecord], bootstrap_iterations: int = 0, seed: int = 42) -> dict[str, object]:
    event_rate = sum(record.event for record in records) / max(len(records), 1)
    surrogate_pairs = [(record.surrogate_score, record.event) for record in records]
    bio_age_pairs = [(record.bio_age, record.event) for record in records]
    age_accel_pairs = [(record.age_acceleration, record.event) for record in records]
    return {
        "participants": len(records),
        "events": sum(record.event for record in records),
        "event_rate": event_rate,
        "c_stat_surrogate": c_statistic(surrogate_pairs),
        "c_stat_surrogate_ci": bootstrap_c_statistic(surrogate_pairs, iterations=bootstrap_iterations, seed=seed),
        "c_stat_bio_age": c_statistic(bio_age_pairs),
        "c_stat_bio_age_ci": bootstrap_c_statistic(bio_age_pairs, iterations=bootstrap_iterations, seed=seed + 1),
        "c_stat_age_accel": c_statistic(age_accel_pairs),
        "c_stat_age_accel_ci": bootstrap_c_statistic(age_accel_pairs, iterations=bootstrap_iterations, seed=seed + 2),
        "bio_age_quartiles": quantile_event_rate(records, "bio_age"),
        "age_accel_quartiles": quantile_event_rate(records, "age_acceleration"),
    }
