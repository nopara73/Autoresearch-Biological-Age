from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from formulas import Formula, Profile
from sampler import (
    OrderedPair,
    DOMAIN_BOUNDS,
    curated_pairs,
    healthy_reference_profile,
    random_dominance_pairs,
    sample_profiles,
    severe_reference_profile,
)


@dataclass(frozen=True)
class ScoreWeights:
    monotonicity: float = 1.0
    pairs: float = 1.0
    smoothness: float = 1.0
    bounds: float = 1.0
    consistency: float = 1.0


@dataclass(frozen=True)
class VerificationConfig:
    sample_size: int = 500
    random_pair_count: int = 200
    seed: int = 42
    pair_epsilon: float = 1e-6
    risk_bounds: tuple[float, float] = (0.0, 30.0)
    reference_profile: Profile = field(default_factory=healthy_reference_profile)
    reference_anchor: float = 0.2
    severe_profile: Profile = field(default_factory=severe_reference_profile)
    smoothness_steps: dict[str, float] = field(
        default_factory=lambda: {
            "vo2max": 0.25,
            "visceral_fat": 1.0,
            "hba1c": 0.02,
            "apob": 1.0,
        }
    )
    smoothness_limits: dict[str, float] = field(
        default_factory=lambda: {
            "vo2max": 0.25,
            "visceral_fat": 0.20,
            "hba1c": 4.0,
            "apob": 0.20,
        }
    )
    weights: ScoreWeights = field(default_factory=ScoreWeights)


@dataclass(frozen=True)
class ComponentResult:
    score: float
    penalty: float
    worst_violation: float
    details: dict[str, Any]


@dataclass(frozen=True)
class VerificationReport:
    total_score: float
    monotonicity: ComponentResult
    pairs: ComponentResult
    smoothness: ComponentResult
    bounds: ComponentResult
    consistency: ComponentResult


def _replace(profile: Profile, variable: str, value: float) -> Profile:
    kwargs = {
        "vo2max": profile.vo2max,
        "visceral_fat": profile.visceral_fat,
        "hba1c": profile.hba1c,
        "apob": profile.apob,
    }
    lower, upper = DOMAIN_BOUNDS[variable]
    kwargs[variable] = min(max(value, lower), upper)
    return Profile(**kwargs)


def _partial_derivative(formula: Formula, profile: Profile, variable: str, step: float) -> float:
    lower, upper = DOMAIN_BOUNDS[variable]
    center = getattr(profile, variable)
    left_value = max(center - step, lower)
    right_value = min(center + step, upper)
    if right_value == left_value:
        return 0.0
    left = formula(_replace(profile, variable, left_value))
    right = formula(_replace(profile, variable, right_value))
    return (right - left) / (right_value - left_value)


def score_monotonicity(formula: Formula, profiles: list[Profile], config: VerificationConfig) -> ComponentResult:
    penalty = 0.0
    worst_violation = 0.0
    worst_case: dict[str, Any] = {}
    direction_map = {
        "vo2max": -1.0,
        "visceral_fat": 1.0,
        "hba1c": 1.0,
        "apob": 1.0,
    }
    for profile in profiles:
        for variable, expected_direction in direction_map.items():
            derivative = _partial_derivative(formula, profile, variable, config.smoothness_steps[variable])
            if expected_direction < 0.0:
                violation = max(derivative, 0.0)
            else:
                violation = max(-derivative, 0.0)
            penalty += violation
            if violation > worst_violation:
                worst_violation = violation
                worst_case = {
                    "variable": variable,
                    "derivative": derivative,
                    "profile": profile,
                }
    score = -(config.weights.monotonicity * penalty)
    return ComponentResult(score=score, penalty=penalty, worst_violation=worst_violation, details=worst_case)


def score_pairs(formula: Formula, pairs: list[OrderedPair], config: VerificationConfig) -> ComponentResult:
    penalty = 0.0
    worst_violation = 0.0
    worst_case: dict[str, Any] = {}
    failures = 0
    for pair in pairs:
        healthy_risk = formula(pair.healthy)
        worse_risk = formula(pair.worse)
        violation = max(healthy_risk - worse_risk + config.pair_epsilon, 0.0)
        penalty += violation
        if violation > 0.0:
            failures += 1
        if violation > worst_violation:
            worst_violation = violation
            worst_case = {
                "label": pair.label,
                "healthy_risk": healthy_risk,
                "worse_risk": worse_risk,
            }
    score = -(config.weights.pairs * penalty)
    return ComponentResult(
        score=score,
        penalty=penalty,
        worst_violation=worst_violation,
        details={"failures": failures, "worst_case": worst_case, "tested_pairs": len(pairs)},
    )


def score_smoothness(formula: Formula, profiles: list[Profile], config: VerificationConfig) -> ComponentResult:
    penalty = 0.0
    worst_violation = 0.0
    worst_case: dict[str, Any] = {}
    for profile in profiles:
        baseline = formula(profile)
        for variable, step in config.smoothness_steps.items():
            shifted_profile = _replace(profile, variable, getattr(profile, variable) + step)
            shifted = formula(shifted_profile)
            slope = abs(shifted - baseline) / max(abs(getattr(shifted_profile, variable) - getattr(profile, variable)), 1e-9)
            limit = config.smoothness_limits[variable]
            violation = max(slope - limit, 0.0)
            penalty += violation
            if violation > worst_violation:
                worst_violation = violation
                worst_case = {
                    "variable": variable,
                    "slope": slope,
                    "limit": limit,
                    "profile": profile,
                }
    score = -(config.weights.smoothness * penalty)
    return ComponentResult(score=score, penalty=penalty, worst_violation=worst_violation, details=worst_case)


def score_bounds(formula: Formula, profiles: list[Profile], config: VerificationConfig) -> ComponentResult:
    penalty = 0.0
    worst_violation = 0.0
    worst_case: dict[str, Any] = {}
    lower, upper = config.risk_bounds
    for profile in profiles:
        risk = formula(profile)
        violation = 0.0
        if risk < lower:
            violation = lower - risk
        elif risk > upper:
            violation = risk - upper
        penalty += violation
        if violation > worst_violation:
            worst_violation = violation
            worst_case = {
                "risk": risk,
                "bounds": config.risk_bounds,
                "profile": profile,
            }
    score = -(config.weights.bounds * penalty)
    return ComponentResult(score=score, penalty=penalty, worst_violation=worst_violation, details=worst_case)


def score_consistency(formula: Formula, config: VerificationConfig) -> ComponentResult:
    reference_risk = formula(config.reference_profile)
    severe_risk = formula(config.severe_profile)
    anchor_violation = abs(reference_risk - config.reference_anchor)
    ordering_violation = max(reference_risk - severe_risk + config.pair_epsilon, 0.0)
    penalty = anchor_violation + ordering_violation
    worst_violation = max(anchor_violation, ordering_violation)
    score = -(config.weights.consistency * penalty)
    return ComponentResult(
        score=score,
        penalty=penalty,
        worst_violation=worst_violation,
        details={
            "reference_risk": reference_risk,
            "reference_anchor": config.reference_anchor,
            "severe_risk": severe_risk,
            "ordering_violation": ordering_violation,
        },
    )


def evaluate_formula(formula: Formula, config: VerificationConfig | None = None) -> VerificationReport:
    """Evaluate one formula against the structural validity criteria."""

    config = config or VerificationConfig()
    profiles = sample_profiles(config.sample_size, seed=config.seed)
    all_pairs = curated_pairs() + random_dominance_pairs(config.random_pair_count, seed=config.seed + 1)

    monotonicity = score_monotonicity(formula, profiles, config)
    pairs = score_pairs(formula, all_pairs, config)
    smoothness = score_smoothness(formula, profiles, config)
    bounds = score_bounds(formula, profiles, config)
    consistency = score_consistency(formula, config)

    total_score = (
        monotonicity.score
        + pairs.score
        + smoothness.score
        + bounds.score
        + consistency.score
    )
    return VerificationReport(
        total_score=total_score,
        monotonicity=monotonicity,
        pairs=pairs,
        smoothness=smoothness,
        bounds=bounds,
        consistency=consistency,
    )
