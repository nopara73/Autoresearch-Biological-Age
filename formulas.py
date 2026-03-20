from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable


@dataclass(frozen=True)
class Profile:
    """Physiologic input vector used by the surrogate formulas."""

    vo2max: float
    visceral_fat: float
    hba1c: float
    apob: float


@dataclass(frozen=True)
class LogisticCoefficients:
    """Coefficients for the monotone logistic family in Section 9."""

    c0: float
    c1: float
    c2: float
    c3: float
    c4: float
    c5: float
    c6: float
    r_max: float = 20.0


Formula = Callable[[Profile], float]


def clamp_percent_risk(raw_fraction: float, cap_fraction: float = 0.20) -> float:
    """Convert a raw annual risk fraction into a capped percent risk."""

    return 100.0 * min(cap_fraction, raw_fraction)


def standardized_deficits(profile: Profile) -> tuple[float, float, float, float]:
    """One-sided standardized deficits from the paper's nominal reference state."""

    d_v = max((35.0 - profile.vo2max) / 10.0, 0.0)
    d_f = max((profile.visceral_fat - 80.0) / 40.0, 0.0)
    d_h = max((profile.hba1c - 5.4) / 0.5, 0.0)
    d_a = max((profile.apob - 80.0) / 30.0, 0.0)
    return d_v, d_f, d_h, d_a


def normalized_margins(profile: Profile) -> tuple[float, float, float, float]:
    """Slack-style normalized reserve margins."""

    return (
        profile.vo2max / 35.0,
        80.0 / profile.visceral_fat,
        5.4 / profile.hba1c,
        80.0 / profile.apob,
    )


def standardized_offsets(profile: Profile) -> tuple[float, float, float, float]:
    """Signed standardized offsets used by the constrained logistic family."""

    z_v = (35.0 - profile.vo2max) / 10.0
    z_f = (profile.visceral_fat - 80.0) / 40.0
    z_h = (profile.hba1c - 5.4) / 0.5
    z_a = (profile.apob - 80.0) / 30.0
    return z_v, z_f, z_h, z_a


def reserve_burden_risk(profile: Profile) -> float:
    """R1: reserve-burden multiplicative estimator."""

    d_v, d_f, d_h, d_a = standardized_deficits(profile)
    hazard_ratio = (
        (1.6 ** d_v)
        * (1.4 ** d_f)
        * (1.5 ** d_h)
        * (1.3 ** d_a)
        * (1.15 ** (d_f * d_h))
    )
    return clamp_percent_risk(0.002 * hazard_ratio)


def dysregulation_distance_risk(profile: Profile) -> float:
    """R2: multivariate dysregulation-distance estimator."""

    d_v, d_f, d_h, d_a = standardized_deficits(profile)
    magnitude = math.sqrt((d_v**2) + (d_f**2) + (d_h**2) + (d_a**2))
    return clamp_percent_risk(0.002 * math.exp((0.8 * magnitude) + (0.3 * magnitude**2)))


def weakest_link_slack_risk(profile: Profile) -> float:
    """R3: weakest-link slack estimator."""

    margins = normalized_margins(profile)
    weakest_margin = max(min(margins), 1e-9)
    return clamp_percent_risk(0.002 / (weakest_margin**2))


def logistic_surrogate(profile: Profile, coefficients: LogisticCoefficients) -> float:
    """Section 9 monotone-constrained logistic surrogate family."""

    z_v, z_f, z_h, z_a = standardized_offsets(profile)
    linear_term = (
        coefficients.c0
        + (coefficients.c1 * z_v)
        + (coefficients.c2 * z_f)
        + (coefficients.c3 * z_h)
        + (coefficients.c4 * z_a)
        + (coefficients.c5 * z_f * z_h)
        + (coefficients.c6 * z_h * z_a)
    )
    sigmoid = 1.0 / (1.0 + math.exp(-linear_term))
    return coefficients.r_max * sigmoid


def make_logistic_formula(coefficients: LogisticCoefficients) -> Formula:
    """Bind coefficients into a callable formula."""

    def formula(profile: Profile) -> float:
        return logistic_surrogate(profile, coefficients)

    return formula


def named_formulas() -> dict[str, Formula]:
    """Built-in formulas that should be compared as competing hypotheses."""

    return {
        "R1_reserve_burden": reserve_burden_risk,
        "R2_dysregulation_distance": dysregulation_distance_risk,
        "R3_weakest_link_slack": weakest_link_slack_risk,
    }
