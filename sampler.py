from __future__ import annotations

from dataclasses import dataclass
import random

from formulas import Profile


DOMAIN_BOUNDS: dict[str, tuple[float, float]] = {
    "vo2max": (15.0, 70.0),
    "visceral_fat": (20.0, 250.0),
    "hba1c": (4.5, 9.0),
    "apob": (40.0, 200.0),
}

DEFAULT_RANDOM_SEED = 42


@dataclass(frozen=True)
class OrderedPair:
    """A profile pair where healthy should rank below worse."""

    label: str
    healthy: Profile
    worse: Profile


def clamp_profile(profile: Profile) -> Profile:
    """Clamp a profile back into the plausible domain."""

    return Profile(
        vo2max=min(max(profile.vo2max, DOMAIN_BOUNDS["vo2max"][0]), DOMAIN_BOUNDS["vo2max"][1]),
        visceral_fat=min(
            max(profile.visceral_fat, DOMAIN_BOUNDS["visceral_fat"][0]),
            DOMAIN_BOUNDS["visceral_fat"][1],
        ),
        hba1c=min(max(profile.hba1c, DOMAIN_BOUNDS["hba1c"][0]), DOMAIN_BOUNDS["hba1c"][1]),
        apob=min(max(profile.apob, DOMAIN_BOUNDS["apob"][0]), DOMAIN_BOUNDS["apob"][1]),
    )


def healthy_reference_profile() -> Profile:
    return Profile(vo2max=50.0, visceral_fat=50.0, hba1c=5.0, apob=60.0)


def severe_reference_profile() -> Profile:
    return Profile(vo2max=20.0, visceral_fat=180.0, hba1c=6.4, apob=150.0)


def sample_profile(rng: random.Random) -> Profile:
    """Sample one random profile uniformly inside the plausible domain."""

    return Profile(
        vo2max=rng.uniform(*DOMAIN_BOUNDS["vo2max"]),
        visceral_fat=rng.uniform(*DOMAIN_BOUNDS["visceral_fat"]),
        hba1c=rng.uniform(*DOMAIN_BOUNDS["hba1c"]),
        apob=rng.uniform(*DOMAIN_BOUNDS["apob"]),
    )


def sample_profiles(count: int, seed: int = DEFAULT_RANDOM_SEED) -> list[Profile]:
    rng = random.Random(seed)
    return [sample_profile(rng) for _ in range(count)]


def curated_pairs() -> list[OrderedPair]:
    """Appendix A pairs plus a few extra directional sanity checks."""

    return [
        OrderedPair(
            label="appendix_a_1",
            healthy=Profile(vo2max=50.0, visceral_fat=50.0, hba1c=5.0, apob=60.0),
            worse=Profile(vo2max=20.0, visceral_fat=180.0, hba1c=6.4, apob=150.0),
        ),
        OrderedPair(
            label="appendix_a_2",
            healthy=Profile(vo2max=42.0, visceral_fat=70.0, hba1c=5.2, apob=75.0),
            worse=Profile(vo2max=30.0, visceral_fat=120.0, hba1c=5.8, apob=110.0),
        ),
        OrderedPair(
            label="fitness_only_gap",
            healthy=Profile(vo2max=55.0, visceral_fat=80.0, hba1c=5.4, apob=80.0),
            worse=Profile(vo2max=25.0, visceral_fat=80.0, hba1c=5.4, apob=80.0),
        ),
        OrderedPair(
            label="metabolic_cluster_gap",
            healthy=Profile(vo2max=40.0, visceral_fat=60.0, hba1c=5.0, apob=70.0),
            worse=Profile(vo2max=40.0, visceral_fat=140.0, hba1c=6.3, apob=130.0),
        ),
    ]


def random_dominance_pairs(count: int, seed: int = DEFAULT_RANDOM_SEED) -> list[OrderedPair]:
    """Create synthetic healthier-vs-worse pairs with strict dominance."""

    rng = random.Random(seed)
    pairs: list[OrderedPair] = []
    for index in range(count):
        base = sample_profile(rng)
        worse = Profile(
            vo2max=base.vo2max - rng.uniform(2.0, 10.0),
            visceral_fat=base.visceral_fat + rng.uniform(5.0, 40.0),
            hba1c=base.hba1c + rng.uniform(0.1, 0.8),
            apob=base.apob + rng.uniform(5.0, 35.0),
        )
        pairs.append(
            OrderedPair(
                label=f"dominance_{index}",
                healthy=clamp_profile(base),
                worse=clamp_profile(worse),
            )
        )
    return pairs
