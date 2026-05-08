"""Statistical validation helpers for transparent event-study research."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from random import Random
from statistics import mean

Statistic = Callable[[Sequence[float]], float]


def _default_statistic(values: Sequence[float]) -> float:
    return mean(values)


def _percentile(sorted_values: Sequence[float], percentile: float) -> float:
    if not sorted_values:
        raise ValueError("values must not be empty")
    if percentile < 0 or percentile > 1:
        raise ValueError("percentile must be between 0 and 1")

    position = percentile * (len(sorted_values) - 1)
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    weight = position - lower_index
    return sorted_values[lower_index] + ((sorted_values[upper_index] - sorted_values[lower_index]) * weight)


def bootstrap_percentile_interval(
    values: Sequence[float],
    *,
    samples: int = 1000,
    confidence: float = 0.95,
    seed: int | None = None,
    statistic: Statistic = _default_statistic,
) -> tuple[float, float]:
    """Return a bootstrap percentile confidence interval for a statistic."""
    if not values:
        raise ValueError("values must not be empty")
    if samples <= 0:
        raise ValueError("samples must be a positive integer")
    if confidence <= 0 or confidence >= 1:
        raise ValueError("confidence must be between 0 and 1")

    rng = Random(seed)
    sample_size = len(values)
    bootstrap_statistics = sorted(
        statistic([values[rng.randrange(sample_size)] for _ in range(sample_size)])
        for _ in range(samples)
    )
    tail = (1 - confidence) / 2
    return (
        _percentile(bootstrap_statistics, tail),
        _percentile(bootstrap_statistics, 1 - tail),
    )


def random_baseline_distribution(
    values: Sequence[float],
    sample_size: int,
    *,
    samples: int = 1000,
    seed: int | None = None,
    statistic: Statistic = _default_statistic,
) -> list[float]:
    """Sample random baseline statistics without replacement."""
    if not values:
        raise ValueError("values must not be empty")
    if sample_size <= 0:
        raise ValueError("sample_size must be a positive integer")
    if sample_size > len(values):
        raise ValueError("sample_size must not exceed values length")
    if samples <= 0:
        raise ValueError("samples must be a positive integer")

    rng = Random(seed)
    population = list(values)
    return [
        statistic(rng.sample(population, sample_size))
        for _ in range(samples)
    ]


def low_sample_warning(sample_size: int, *, minimum: int = 30) -> str | None:
    """Return a warning message when a sample is too small for strong claims."""
    if sample_size < 0:
        raise ValueError("sample_size must not be negative")
    if minimum <= 0:
        raise ValueError("minimum must be a positive integer")
    if sample_size >= minimum:
        return None
    return f"Low sample size: {sample_size} observations; treat results as exploratory until at least {minimum} are available."
