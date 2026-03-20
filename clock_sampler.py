from __future__ import annotations

from dataclasses import dataclass
import random

from clock_features import CLOCK_FIELDS, CLOCK_FIELD_SPECS, ClockProfile, clamp_clock_profile, healthy_clock_profile


DEFAULT_RANDOM_SEED = 42


@dataclass(frozen=True)
class OrderedClockPair:
    label: str
    healthy: ClockProfile
    worse: ClockProfile


def sample_clock_profile(rng: random.Random) -> ClockProfile:
    values = {
        field_name: rng.uniform(spec.lower, spec.upper)
        for field_name, spec in CLOCK_FIELD_SPECS.items()
    }
    return ClockProfile(**values)


def sample_clock_profiles(count: int, seed: int = DEFAULT_RANDOM_SEED) -> list[ClockProfile]:
    rng = random.Random(seed)
    return [sample_clock_profile(rng) for _ in range(count)]


def curated_clock_pairs() -> list[OrderedClockPair]:
    return [
        OrderedClockPair(
            label="healthy_vs_severe_full",
            healthy=healthy_clock_profile(),
            worse=ClockProfile(
                fitness=22.0,
                central_adiposity=0.72,
                glycemia=6.5,
                atherogenic_burden=185.0,
                hemodynamic_stress=155.0,
                kidney_function=1.7,
                inflammation=6.0,
                lung_function=1.9,
            ),
        ),
        OrderedClockPair(
            label="kidney_only_gap",
            healthy=ClockProfile(50.0, 0.48, 5.2, 110.0, 115.0, 0.8, 1.0, 4.0),
            worse=ClockProfile(50.0, 0.48, 5.2, 110.0, 115.0, 1.8, 1.0, 4.0),
        ),
        OrderedClockPair(
            label="lung_only_gap",
            healthy=ClockProfile(48.0, 0.50, 5.3, 120.0, 118.0, 0.9, 1.2, 4.2),
            worse=ClockProfile(48.0, 0.50, 5.3, 120.0, 118.0, 0.9, 1.2, 2.1),
        ),
        OrderedClockPair(
            label="inflammation_only_gap",
            healthy=ClockProfile(48.0, 0.50, 5.3, 120.0, 118.0, 0.9, 0.8, 3.9),
            worse=ClockProfile(48.0, 0.50, 5.3, 120.0, 118.0, 0.9, 8.0, 3.9),
        ),
    ]


def random_clock_dominance_pairs(count: int, seed: int = DEFAULT_RANDOM_SEED) -> list[OrderedClockPair]:
    rng = random.Random(seed)
    pairs: list[OrderedClockPair] = []
    for index in range(count):
        base = sample_clock_profile(rng)
        worse_values: dict[str, float] = {}
        for field_name in CLOCK_FIELDS:
            spec = CLOCK_FIELD_SPECS[field_name]
            value = getattr(base, field_name)
            if spec.direction == "higher_is_healthier":
                worse_values[field_name] = value - rng.uniform(0.05 * spec.scale, 0.8 * spec.scale)
            else:
                worse_values[field_name] = value + rng.uniform(0.05 * spec.scale, 0.8 * spec.scale)
        pairs.append(
            OrderedClockPair(
                label=f"clock_dominance_{index}",
                healthy=clamp_clock_profile(base),
                worse=clamp_clock_profile(ClockProfile(**worse_values)),
            )
        )
    return pairs
