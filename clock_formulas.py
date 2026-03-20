from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable

from clock_features import ClockProfile, CLOCK_FIELDS, one_sided_deficits, normalized_margins, standardized_offsets


ClockFormula = Callable[[ClockProfile], float]


@dataclass(frozen=True)
class ClockLogisticCoefficients:
    intercept: float
    fitness: float
    central_adiposity: float
    glycemia: float
    atherogenic_burden: float
    hemodynamic_stress: float
    kidney_function: float
    inflammation: float
    lung_function: float
    adiposity_glycemia: float = 0.0
    kidney_pressure: float = 0.0
    inflammation_lung: float = 0.0
    r_max: float = 20.0


def clamp_percent_risk(raw_fraction: float, cap_fraction: float = 0.20) -> float:
    return 100.0 * min(cap_fraction, raw_fraction)


def reserve_burden_clock_risk(profile: ClockProfile) -> float:
    deficits = one_sided_deficits(profile)
    hazard_ratio = (
        (1.55 ** deficits["fitness"])
        * (1.30 ** deficits["central_adiposity"])
        * (1.45 ** deficits["glycemia"])
        * (1.30 ** deficits["atherogenic_burden"])
        * (1.22 ** deficits["hemodynamic_stress"])
        * (1.38 ** deficits["kidney_function"])
        * (1.18 ** deficits["inflammation"])
        * (1.42 ** deficits["lung_function"])
        * (1.12 ** (deficits["central_adiposity"] * deficits["glycemia"]))
        * (1.10 ** (deficits["kidney_function"] * deficits["hemodynamic_stress"]))
        * (1.10 ** (deficits["inflammation"] * deficits["lung_function"]))
    )
    return clamp_percent_risk(0.002 * hazard_ratio)


def dysregulation_distance_clock_risk(profile: ClockProfile) -> float:
    deficits = one_sided_deficits(profile)
    magnitude = math.sqrt(sum(value**2 for value in deficits.values()))
    return clamp_percent_risk(0.002 * math.exp((0.65 * magnitude) + (0.18 * magnitude**2)))


def weakest_link_clock_risk(profile: ClockProfile) -> float:
    margins = normalized_margins(profile)
    weakest_margin = max(min(margins.values()), 1e-9)
    return clamp_percent_risk(0.002 / (weakest_margin**2))


def logistic_clock_risk(profile: ClockProfile, coefficients: ClockLogisticCoefficients) -> float:
    offsets = standardized_offsets(profile)
    linear_term = (
        coefficients.intercept
        + (coefficients.fitness * offsets["fitness"])
        + (coefficients.central_adiposity * offsets["central_adiposity"])
        + (coefficients.glycemia * offsets["glycemia"])
        + (coefficients.atherogenic_burden * offsets["atherogenic_burden"])
        + (coefficients.hemodynamic_stress * offsets["hemodynamic_stress"])
        + (coefficients.kidney_function * offsets["kidney_function"])
        + (coefficients.inflammation * offsets["inflammation"])
        + (coefficients.lung_function * offsets["lung_function"])
        + (coefficients.adiposity_glycemia * offsets["central_adiposity"] * offsets["glycemia"])
        + (coefficients.kidney_pressure * offsets["kidney_function"] * offsets["hemodynamic_stress"])
        + (coefficients.inflammation_lung * offsets["inflammation"] * offsets["lung_function"])
    )
    sigmoid = 1.0 / (1.0 + math.exp(-linear_term))
    return coefficients.r_max * sigmoid


def make_logistic_clock_formula(coefficients: ClockLogisticCoefficients) -> ClockFormula:
    def formula(profile: ClockProfile) -> float:
        return logistic_clock_risk(profile, coefficients)

    return formula


def default_logistic_coefficients() -> ClockLogisticCoefficients:
    return ClockLogisticCoefficients(
        intercept=-4.3,
        fitness=0.9,
        central_adiposity=0.7,
        glycemia=0.8,
        atherogenic_burden=0.5,
        hemodynamic_stress=0.45,
        kidney_function=0.8,
        inflammation=0.35,
        lung_function=0.75,
        adiposity_glycemia=0.12,
        kidney_pressure=0.10,
        inflammation_lung=0.08,
    )


def default_logistic_clock_risk(profile: ClockProfile) -> float:
    return logistic_clock_risk(profile, default_logistic_coefficients())


def named_clock_formulas() -> dict[str, ClockFormula]:
    return {
        "Clock_R1_reserve_burden": reserve_burden_clock_risk,
        "Clock_R2_dysregulation_distance": dysregulation_distance_clock_risk,
        "Clock_R3_weakest_link": weakest_link_clock_risk,
        "Clock_logistic_default": default_logistic_clock_risk,
    }
