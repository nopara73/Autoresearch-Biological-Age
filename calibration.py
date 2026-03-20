from __future__ import annotations

import csv
from dataclasses import dataclass
import random

from clock_formulas import ClockFormula, default_logistic_clock_risk
from clock_sampler import sample_clock_profiles
from harmonized_dataset import HarmonizedParticipant


@dataclass(frozen=True)
class ScoredParticipant:
    seqn: str
    chronological_age: float
    surrogate_score: float
    bio_age: float
    age_acceleration: float

    def to_row(self) -> dict[str, str]:
        return {
            "SEQN": self.seqn,
            "chronological_age": f"{self.chronological_age:.6f}",
            "surrogate_score": f"{self.surrogate_score:.6f}",
            "bio_age": f"{self.bio_age:.6f}",
            "age_acceleration": f"{self.age_acceleration:.6f}",
        }


class IsotonicCalibrator:
    def __init__(self) -> None:
        self.thresholds: list[float] = []
        self.values: list[float] = []

    def fit(self, scores: list[float], ages: list[float]) -> "IsotonicCalibrator":
        if len(scores) != len(ages):
            raise ValueError("Scores and ages must have the same length.")
        if not scores:
            raise ValueError("Cannot fit calibrator on an empty dataset.")

        pairs = sorted(zip(scores, ages), key=lambda item: item[0])
        blocks: list[dict[str, float]] = []
        for score, age in pairs:
            blocks.append({"start": score, "end": score, "weight": 1.0, "mean": age})
            while len(blocks) >= 2 and blocks[-2]["mean"] > blocks[-1]["mean"]:
                right = blocks.pop()
                left = blocks.pop()
                weight = left["weight"] + right["weight"]
                mean = ((left["mean"] * left["weight"]) + (right["mean"] * right["weight"])) / weight
                blocks.append(
                    {
                        "start": left["start"],
                        "end": right["end"],
                        "weight": weight,
                        "mean": mean,
                    }
                )

        self.thresholds = [block["end"] for block in blocks]
        self.values = [block["mean"] for block in blocks]
        return self

    def predict_one(self, score: float) -> float:
        if not self.thresholds:
            raise ValueError("Calibrator must be fit before prediction.")
        for threshold, value in zip(self.thresholds, self.values):
            if score <= threshold:
                return value
        return self.values[-1]

    def predict(self, scores: list[float]) -> list[float]:
        return [self.predict_one(score) for score in scores]


def score_participants(participants: list[HarmonizedParticipant], formula: ClockFormula) -> list[float]:
    return [formula(participant.profile) for participant in participants]


def _linear_fit(x_values: list[float], y_values: list[float]) -> tuple[float, float]:
    mean_x = sum(x_values) / len(x_values)
    mean_y = sum(y_values) / len(y_values)
    denominator = sum((x - mean_x) ** 2 for x in x_values)
    if denominator == 0.0:
        return mean_y, 0.0
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values)) / denominator
    intercept = mean_y - (slope * mean_x)
    return intercept, slope


def _score_to_scored_participants(
    participants: list[HarmonizedParticipant],
    scores: list[float],
    bio_ages: list[float],
    fit_ages: list[float],
    fit_bio_ages: list[float],
) -> list[ScoredParticipant]:
    intercept, slope = _linear_fit(fit_ages, fit_bio_ages)
    return [
        ScoredParticipant(
            seqn=participant.seqn,
            chronological_age=participant.chronological_age,
            surrogate_score=score,
            bio_age=bio_age,
            age_acceleration=bio_age - (intercept + (slope * participant.chronological_age)),
        )
        for participant, score, bio_age in zip(participants, scores, bio_ages)
    ]


def calibrate_biological_age(
    participants: list[HarmonizedParticipant],
    formula: ClockFormula = default_logistic_clock_risk,
) -> tuple[IsotonicCalibrator, list[ScoredParticipant]]:
    scores = score_participants(participants, formula)
    ages = [participant.chronological_age for participant in participants]
    calibrator = IsotonicCalibrator().fit(scores, ages)
    bio_ages = calibrator.predict(scores)
    scored = _score_to_scored_participants(participants, scores, bio_ages, ages, bio_ages)
    return calibrator, scored


def calibrate_biological_age_oof(
    participants: list[HarmonizedParticipant],
    formula: ClockFormula = default_logistic_clock_risk,
    n_folds: int = 5,
    seed: int = 42,
) -> list[ScoredParticipant]:
    if n_folds < 2:
        raise ValueError("n_folds must be at least 2 for out-of-fold calibration.")
    if len(participants) < n_folds:
        raise ValueError("Not enough participants for the requested number of folds.")

    indexed = list(enumerate(participants))
    rng = random.Random(seed)
    rng.shuffle(indexed)

    folds: list[list[tuple[int, HarmonizedParticipant]]] = [[] for _ in range(n_folds)]
    for position, item in enumerate(indexed):
        folds[position % n_folds].append(item)

    scored_by_index: dict[int, ScoredParticipant] = {}
    for fold_index in range(n_folds):
        holdout = folds[fold_index]
        train = [item for idx, fold in enumerate(folds) if idx != fold_index for item in fold]
        train_participants = [participant for _, participant in train]
        holdout_participants = [participant for _, participant in holdout]

        train_scores = score_participants(train_participants, formula)
        train_ages = [participant.chronological_age for participant in train_participants]
        calibrator = IsotonicCalibrator().fit(train_scores, train_ages)

        holdout_scores = score_participants(holdout_participants, formula)
        holdout_bio_ages = calibrator.predict(holdout_scores)
        scored_holdout = _score_to_scored_participants(
            participants=holdout_participants,
            scores=holdout_scores,
            bio_ages=holdout_bio_ages,
            fit_ages=train_ages,
            fit_bio_ages=calibrator.predict(train_scores),
        )

        for (original_index, _), scored in zip(holdout, scored_holdout):
            scored_by_index[original_index] = scored

    return [scored_by_index[index] for index in range(len(participants))]


def write_scored_csv(rows: list[ScoredParticipant], output_path: str) -> None:
    if not rows:
        raise ValueError("No scored rows available to write.")
    with open(output_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].to_row().keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_row())


def synthetic_demo_participants(count: int, seed: int = 42) -> list[HarmonizedParticipant]:
    rng = random.Random(seed)
    profiles = sample_clock_profiles(count, seed=seed)
    participants: list[HarmonizedParticipant] = []
    for index, profile in enumerate(profiles):
        score = default_logistic_clock_risk(profile)
        age = max(20.0, min(85.0, 30.0 + (2.2 * score) + rng.gauss(0.0, 6.0)))
        participants.append(
            HarmonizedParticipant(
                seqn=str(10_000 + index),
                chronological_age=age,
                profile=profile,
                central_adiposity_proxy="synthetic",
                atherogenic_proxy="synthetic",
                lung_proxy="synthetic",
            )
        )
    return participants
