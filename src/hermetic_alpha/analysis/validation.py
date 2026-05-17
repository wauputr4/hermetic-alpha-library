"""Statistical validation helpers for transparent event-study research."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from math import isfinite
from random import Random
from statistics import mean
from typing import Literal

Statistic = Callable[[Sequence[float]], float]
Alternative = Literal["greater", "less", "two-sided"]


@dataclass(frozen=True)
class PermutationTestResult:
    """Inspectable output from a permutation test."""

    observed_statistic: float
    p_value: float
    alternative: Alternative
    permutations: int
    seed: int | None
    null_distribution: list[float]
    null_mean: float

    def to_dict(self) -> dict[str, float | int | str | list[float] | None]:
        return {
            "observed_statistic": self.observed_statistic,
            "p_value": self.p_value,
            "alternative": self.alternative,
            "permutations": self.permutations,
            "seed": self.seed,
            "null_distribution": list(self.null_distribution),
            "null_mean": self.null_mean,
        }


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
        statistic(rng.choices(values, k=sample_size))
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


def permutation_test(
    observed_values: Sequence[float],
    baseline_values: Sequence[float],
    *,
    permutations: int = 1000,
    seed: int | None = None,
    statistic: Statistic = _default_statistic,
    alternative: Alternative = "two-sided",
) -> PermutationTestResult:
    """Compare observed outcomes against a baseline by random relabeling.

    The returned p-value uses plus-one correction, so it never reports exactly
    zero for a finite permutation run.
    """

    if not observed_values:
        raise ValueError("observed_values must not be empty")
    if not baseline_values:
        raise ValueError("baseline_values must not be empty")
    if permutations <= 0:
        raise ValueError("permutations must be a positive integer")
    if alternative not in ("greater", "less", "two-sided"):
        raise ValueError("alternative must be 'greater', 'less', or 'two-sided'")

    observed = list(observed_values)
    baseline = list(baseline_values)
    observed_size = len(observed)
    population = observed + baseline
    rng = Random(seed)
    observed_statistic = _evaluate_statistic(statistic, observed)
    null_distribution: list[float] = []

    for _ in range(permutations):
        shuffled = list(population)
        rng.shuffle(shuffled)
        null_distribution.append(
            _evaluate_statistic(statistic, shuffled[:observed_size])
        )

    null_mean = mean(null_distribution)
    p_value = _permutation_p_value(
        observed_statistic,
        null_distribution,
        null_mean,
        alternative,
    )
    return PermutationTestResult(
        observed_statistic=observed_statistic,
        p_value=p_value,
        alternative=alternative,
        permutations=permutations,
        seed=seed,
        null_distribution=null_distribution,
        null_mean=null_mean,
    )


def low_sample_warning(sample_size: int, *, minimum: int = 30) -> str | None:
    """Return a warning message when a sample is too small for strong claims."""
    if sample_size < 0:
        raise ValueError("sample_size must not be negative")
    if minimum <= 0:
        raise ValueError("minimum must be a positive integer")
    if sample_size >= minimum:
        return None
    return f"Low sample size: {sample_size} observations; treat results as exploratory until at least {minimum} are available."


def _evaluate_statistic(statistic: Statistic, values: Sequence[float]) -> float:
    try:
        result = float(statistic(values))
    except (TypeError, ValueError) as exc:
        raise ValueError("statistic must return a finite numeric value") from exc
    if not isfinite(result):
        raise ValueError("statistic must return a finite numeric value")
    return result


def _permutation_p_value(
    observed_statistic: float,
    null_distribution: Sequence[float],
    null_mean: float,
    alternative: Alternative,
) -> float:
    if alternative == "greater":
        extreme_count = sum(value >= observed_statistic for value in null_distribution)
    elif alternative == "less":
        extreme_count = sum(value <= observed_statistic for value in null_distribution)
    else:
        observed_distance = abs(observed_statistic - null_mean)
        extreme_count = sum(
            abs(value - null_mean) >= observed_distance
            for value in null_distribution
        )
    return (extreme_count + 1) / (len(null_distribution) + 1)
