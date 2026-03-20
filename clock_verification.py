from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from clock_features import CLOCK_FIELDS, CLOCK_FIELD_SPECS, ClockProfile, healthy_clock_profile, replace_clock_value, severe_clock_profile
from clock_formulas import ClockFormula
from clock_sampler import OrderedClockPair, curated_clock_pairs, random_clock_dominance_pairs, sample_clock_profiles


@dataclass(frozen=True)
class ClockScoreWeights:
    monotonicity: float = 1.0
    pairs: float = 1.0
    smoothness: float = 1.0
    bounds: float = 1.0
    consistency: float = 1.0


@dataclass(frozen=True)
class ClockVerificationConfig:
    sample_size: int = 500
    random_pair_count: int = 200
    seed: int = 42
    pair_epsilon: float = 1e-6
    risk_bounds: tuple[float, float] = (0.0, 30.0)
    reference_profile: ClockProfile = field(default_factory=healthy_clock_profile)
    reference_anchor: float = 0.2
    severe_profile: ClockProfile = field(default_factory=severe_clock_profile)
    weights: ClockScoreWeights = field(default_factory=ClockScoreWeights)


@dataclass(frozen=True)
class ClockComponentResult:
    score: float
    penalty: float
    worst_violation: float
    details: dict[str, Any]


@dataclass(frozen=True)
class ClockVerificationReport:
    total_score: float
    monotonicity: ClockComponentResult
    pairs: ClockComponentResult
    smoothness: ClockComponentResult
    bounds: ClockComponentResult
    consistency: ClockComponentResult


def _partial_derivative(formula: ClockFormula, profile: ClockProfile, field_name: str) -> float:
    spec = CLOCK_FIELD_SPECS[field_name]
    center = getattr(profile, field_name)
    left_value = max(center - spec.smoothness_step, spec.lower)
    right_value = min(center + spec.smoothness_step, spec.upper)
    if right_value == left_value:
        return 0.0
    left = formula(replace_clock_value(profile, field_name, left_value))
    right = formula(replace_clock_value(profile, field_name, right_value))
    return (right - left) / (right_value - left_value)


def score_monotonicity(formula: ClockFormula, profiles: list[ClockProfile], config: ClockVerificationConfig) -> ClockComponentResult:
    penalty = 0.0
    worst_violation = 0.0
    worst_case: dict[str, Any] = {}
    for profile in profiles:
        for field_name in CLOCK_FIELDS:
            spec = CLOCK_FIELD_SPECS[field_name]
            derivative = _partial_derivative(formula, profile, field_name)
            if spec.direction == "higher_is_healthier":
                violation = max(derivative, 0.0)
            else:
                violation = max(-derivative, 0.0)
            penalty += violation
            if violation > worst_violation:
                worst_violation = violation
                worst_case = {"field": field_name, "derivative": derivative, "profile": profile}
    score = -(config.weights.monotonicity * penalty)
    return ClockComponentResult(score=score, penalty=penalty, worst_violation=worst_violation, details=worst_case)


def score_pairs(formula: ClockFormula, pairs: list[OrderedClockPair], config: ClockVerificationConfig) -> ClockComponentResult:
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
            worst_case = {"label": pair.label, "healthy_risk": healthy_risk, "worse_risk": worse_risk}
    score = -(config.weights.pairs * penalty)
    return ClockComponentResult(
        score=score,
        penalty=penalty,
        worst_violation=worst_violation,
        details={"failures": failures, "worst_case": worst_case, "tested_pairs": len(pairs)},
    )


def score_smoothness(formula: ClockFormula, profiles: list[ClockProfile], config: ClockVerificationConfig) -> ClockComponentResult:
    penalty = 0.0
    worst_violation = 0.0
    worst_case: dict[str, Any] = {}
    for profile in profiles:
        baseline = formula(profile)
        for field_name in CLOCK_FIELDS:
            spec = CLOCK_FIELD_SPECS[field_name]
            shifted_profile = replace_clock_value(profile, field_name, getattr(profile, field_name) + spec.smoothness_step)
            shifted = formula(shifted_profile)
            delta = abs(getattr(shifted_profile, field_name) - getattr(profile, field_name))
            slope = abs(shifted - baseline) / max(delta, 1e-9)
            violation = max(slope - spec.smoothness_limit, 0.0)
            penalty += violation
            if violation > worst_violation:
                worst_violation = violation
                worst_case = {"field": field_name, "slope": slope, "limit": spec.smoothness_limit, "profile": profile}
    score = -(config.weights.smoothness * penalty)
    return ClockComponentResult(score=score, penalty=penalty, worst_violation=worst_violation, details=worst_case)


def score_bounds(formula: ClockFormula, profiles: list[ClockProfile], config: ClockVerificationConfig) -> ClockComponentResult:
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
            worst_case = {"risk": risk, "profile": profile}
    score = -(config.weights.bounds * penalty)
    return ClockComponentResult(score=score, penalty=penalty, worst_violation=worst_violation, details=worst_case)


def score_consistency(formula: ClockFormula, config: ClockVerificationConfig) -> ClockComponentResult:
    reference_risk = formula(config.reference_profile)
    severe_risk = formula(config.severe_profile)
    anchor_violation = abs(reference_risk - config.reference_anchor)
    ordering_violation = max(reference_risk - severe_risk + config.pair_epsilon, 0.0)
    penalty = anchor_violation + ordering_violation
    worst_violation = max(anchor_violation, ordering_violation)
    score = -(config.weights.consistency * penalty)
    return ClockComponentResult(
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


def evaluate_clock_formula(formula: ClockFormula, config: ClockVerificationConfig | None = None) -> ClockVerificationReport:
    config = config or ClockVerificationConfig()
    profiles = sample_clock_profiles(config.sample_size, seed=config.seed)
    all_pairs = curated_clock_pairs() + random_clock_dominance_pairs(config.random_pair_count, seed=config.seed + 1)

    monotonicity = score_monotonicity(formula, profiles, config)
    pairs = score_pairs(formula, all_pairs, config)
    smoothness = score_smoothness(formula, profiles, config)
    bounds = score_bounds(formula, profiles, config)
    consistency = score_consistency(formula, config)

    total_score = monotonicity.score + pairs.score + smoothness.score + bounds.score + consistency.score
    return ClockVerificationReport(
        total_score=total_score,
        monotonicity=monotonicity,
        pairs=pairs,
        smoothness=smoothness,
        bounds=bounds,
        consistency=consistency,
    )
