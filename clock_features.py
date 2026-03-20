from __future__ import annotations

from dataclasses import asdict, dataclass, replace


@dataclass(frozen=True)
class ClockFieldSpec:
    name: str
    lower: float
    upper: float
    reference: float
    scale: float
    direction: str
    smoothness_step: float
    smoothness_limit: float


@dataclass(frozen=True)
class ClockProfile:
    fitness: float
    central_adiposity: float
    glycemia: float
    atherogenic_burden: float
    hemodynamic_stress: float
    kidney_function: float
    inflammation: float
    lung_function: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


CLOCK_FIELD_SPECS: dict[str, ClockFieldSpec] = {
    "fitness": ClockFieldSpec(
        name="fitness",
        lower=15.0,
        upper=70.0,
        reference=45.0,
        scale=10.0,
        direction="higher_is_healthier",
        smoothness_step=0.5,
        smoothness_limit=0.25,
    ),
    "central_adiposity": ClockFieldSpec(
        name="central_adiposity",
        lower=0.35,
        upper=0.95,
        reference=0.48,
        scale=0.08,
        direction="lower_is_healthier",
        smoothness_step=0.01,
        smoothness_limit=12.0,
    ),
    "glycemia": ClockFieldSpec(
        name="glycemia",
        lower=4.5,
        upper=9.0,
        reference=5.3,
        scale=0.5,
        direction="lower_is_healthier",
        smoothness_step=0.02,
        smoothness_limit=4.0,
    ),
    "atherogenic_burden": ClockFieldSpec(
        name="atherogenic_burden",
        lower=60.0,
        upper=260.0,
        reference=110.0,
        scale=30.0,
        direction="lower_is_healthier",
        smoothness_step=1.0,
        smoothness_limit=0.25,
    ),
    "hemodynamic_stress": ClockFieldSpec(
        name="hemodynamic_stress",
        lower=90.0,
        upper=200.0,
        reference=115.0,
        scale=15.0,
        direction="lower_is_healthier",
        smoothness_step=1.0,
        smoothness_limit=0.25,
    ),
    "kidney_function": ClockFieldSpec(
        name="kidney_function",
        lower=0.4,
        upper=3.5,
        reference=0.85,
        scale=0.25,
        direction="lower_is_healthier",
        smoothness_step=0.02,
        smoothness_limit=2.0,
    ),
    "inflammation": ClockFieldSpec(
        name="inflammation",
        lower=0.1,
        upper=20.0,
        reference=1.0,
        scale=1.5,
        direction="lower_is_healthier",
        smoothness_step=0.1,
        smoothness_limit=1.5,
    ),
    "lung_function": ClockFieldSpec(
        name="lung_function",
        lower=1.0,
        upper=6.0,
        reference=3.5,
        scale=0.6,
        direction="higher_is_healthier",
        smoothness_step=0.05,
        smoothness_limit=1.0,
    ),
}

CLOCK_FIELDS: tuple[str, ...] = tuple(CLOCK_FIELD_SPECS.keys())


def clamp_clock_profile(profile: ClockProfile) -> ClockProfile:
    values = {}
    for field_name, spec in CLOCK_FIELD_SPECS.items():
        raw_value = getattr(profile, field_name)
        values[field_name] = min(max(raw_value, spec.lower), spec.upper)
    return ClockProfile(**values)


def replace_clock_value(profile: ClockProfile, field_name: str, value: float) -> ClockProfile:
    spec = CLOCK_FIELD_SPECS[field_name]
    clamped = min(max(value, spec.lower), spec.upper)
    return replace(profile, **{field_name: clamped})


def healthy_clock_profile() -> ClockProfile:
    return ClockProfile(
        fitness=50.0,
        central_adiposity=0.46,
        glycemia=5.0,
        atherogenic_burden=100.0,
        hemodynamic_stress=112.0,
        kidney_function=0.82,
        inflammation=0.8,
        lung_function=4.0,
    )


def severe_clock_profile() -> ClockProfile:
    return ClockProfile(
        fitness=22.0,
        central_adiposity=0.72,
        glycemia=6.5,
        atherogenic_burden=185.0,
        hemodynamic_stress=155.0,
        kidney_function=1.7,
        inflammation=6.0,
        lung_function=1.9,
    )


def signed_standardized_offset(profile: ClockProfile, field_name: str) -> float:
    spec = CLOCK_FIELD_SPECS[field_name]
    value = getattr(profile, field_name)
    if spec.direction == "higher_is_healthier":
        return (spec.reference - value) / spec.scale
    return (value - spec.reference) / spec.scale


def standardized_offsets(profile: ClockProfile) -> dict[str, float]:
    return {field_name: signed_standardized_offset(profile, field_name) for field_name in CLOCK_FIELDS}


def one_sided_deficits(profile: ClockProfile) -> dict[str, float]:
    return {field_name: max(offset, 0.0) for field_name, offset in standardized_offsets(profile).items()}


def normalized_margins(profile: ClockProfile) -> dict[str, float]:
    margins: dict[str, float] = {}
    for field_name, spec in CLOCK_FIELD_SPECS.items():
        value = getattr(profile, field_name)
        if spec.direction == "higher_is_healthier":
            margins[field_name] = value / spec.reference
        else:
            margins[field_name] = spec.reference / max(value, 1e-9)
    return margins
