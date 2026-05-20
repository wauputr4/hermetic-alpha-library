"""Statistical validation helpers for transparent event-study research."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from math import isfinite
from random import Random
from statistics import mean
from typing import Any, Literal

Statistic = Callable[[Sequence[float]], float]
Alternative = Literal["greater", "less", "two-sided"]
ReportScalar = str | int | float | bool | date | datetime | None


@dataclass(frozen=True)
class WalkForwardSplit:
    """Inspectable chronological train/test window definition."""

    train: tuple[Any, ...]
    test: tuple[Any, ...]
    train_start_index: int
    train_end_index: int
    test_start_index: int
    test_end_index: int

    def to_dict(self) -> dict[str, int | list[Any]]:
        return {
            "train": list(self.train),
            "test": list(self.test),
            "train_start_index": self.train_start_index,
            "train_end_index": self.train_end_index,
            "test_start_index": self.test_start_index,
            "test_end_index": self.test_end_index,
        }


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


def permutation_test_result_row(result: PermutationTestResult) -> dict[str, float | int | str | None]:
    """Return a flat CSV-compatible summary row for a permutation test result."""
    null_distribution = result.null_distribution
    return {
        "observed_statistic": result.observed_statistic,
        "p_value": result.p_value,
        "alternative": result.alternative,
        "permutations": result.permutations,
        "seed": result.seed,
        "null_mean": result.null_mean,
        "null_distribution_count": len(null_distribution),
        "null_distribution_min": min(null_distribution) if null_distribution else None,
        "null_distribution_max": max(null_distribution) if null_distribution else None,
    }


def random_baseline_distribution_row(
    distribution: Sequence[float],
    *,
    sample_size: int | None = None,
    samples: int | None = None,
    seed: int | None = None,
) -> dict[str, float | int | None]:
    """Return a compact CSV-compatible summary row for random baselines."""

    values = [_evaluate_distribution_value(value) for value in distribution]
    return {
        "distribution_count": len(values),
        "distribution_min": min(values) if values else None,
        "distribution_max": max(values) if values else None,
        "distribution_mean": mean(values) if values else None,
        "sample_size": sample_size,
        "samples": samples,
        "seed": seed,
    }


def random_baseline_distribution_rows(
    distributions: Mapping[str, Sequence[float]] | Sequence[tuple[str, Sequence[float]]],
    *,
    sample_size: int | None = None,
    samples: int | None = None,
    seed: int | None = None,
) -> list[dict[str, float | int | str | None]]:
    """Return ordered flat rows for several random-baseline distributions."""

    rows: list[dict[str, float | int | str | None]] = []
    seen_baseline_ids: set[str] = set()
    for baseline_id, distribution in _iter_named_distributions(distributions):
        if baseline_id in seen_baseline_ids:
            raise ValueError("baseline IDs must be unique")
        seen_baseline_ids.add(baseline_id)
        rows.append({
            "baseline_id": baseline_id,
            **random_baseline_distribution_row(
                distribution,
                sample_size=sample_size,
                samples=samples,
                seed=seed,
            ),
        })
    return rows


def bootstrap_interval_row(
    interval: Sequence[float],
    *,
    samples: int | None = None,
    confidence: float | None = None,
    seed: int | None = None,
    statistic_name: str | None = None,
) -> dict[str, float | int | str | None]:
    """Return a flat CSV-compatible summary row for a bootstrap interval."""

    lower, upper = _coerce_interval_bounds(interval)
    return {
        "interval_lower": lower,
        "interval_upper": upper,
        "samples": samples,
        "confidence": confidence,
        "seed": seed,
        "statistic_name": statistic_name,
    }


def bootstrap_interval_rows(
    intervals: Mapping[str, Sequence[float]] | Sequence[tuple[str, Sequence[float]]],
    *,
    samples: int | None = None,
    confidence: float | None = None,
    seed: int | None = None,
) -> list[dict[str, float | int | str | None]]:
    """Return ordered flat rows for several bootstrap intervals."""

    rows: list[dict[str, float | int | str | None]] = []
    seen_statistic_names: set[str] = set()
    for statistic_name, interval in _iter_named_intervals(intervals):
        if statistic_name in seen_statistic_names:
            raise ValueError("statistic names must be unique")
        seen_statistic_names.add(statistic_name)
        rows.append(
            bootstrap_interval_row(
                interval,
                samples=samples,
                confidence=confidence,
                seed=seed,
                statistic_name=statistic_name,
            )
        )
    return rows


def walk_forward_split_rows(splits: Sequence[WalkForwardSplit]) -> list[dict[str, ReportScalar]]:
    """Return flat CSV-compatible rows for walk-forward split boundaries."""
    return [
        {
            "split_index": split_index,
            "train_start_index": split.train_start_index,
            "train_end_index": split.train_end_index,
            "test_start_index": split.test_start_index,
            "test_end_index": split.test_end_index,
            "train_size": len(split.train),
            "test_size": len(split.test),
            "train_first": _csv_safe_endpoint(split.train[0]) if split.train else None,
            "train_last": _csv_safe_endpoint(split.train[-1]) if split.train else None,
            "test_first": _csv_safe_endpoint(split.test[0]) if split.test else None,
            "test_last": _csv_safe_endpoint(split.test[-1]) if split.test else None,
        }
        for split_index, split in enumerate(splits)
    ]


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


def walk_forward_splits(
    observations: Sequence[Any] | int,
    *,
    train_size: int,
    test_size: int,
    step_size: int | None = None,
) -> list[WalkForwardSplit]:
    """Generate fixed-size chronological train/test windows.

    Passing an integer uses positional indexes ``range(observations)``. Passing
    a sequence returns slices of the supplied observations. Each test window
    starts after its train window, so future observations never appear in the
    corresponding train set.
    """

    ordered = _coerce_ordered_observations(observations)
    if train_size <= 0:
        raise ValueError("train_size must be a positive integer")
    if test_size <= 0:
        raise ValueError("test_size must be a positive integer")
    if step_size is None:
        step_size = test_size
    if step_size <= 0:
        raise ValueError("step_size must be a positive integer")
    if step_size < test_size:
        raise ValueError("step_size must be greater than or equal to test_size to avoid overlapping test windows")
    if train_size + test_size > len(ordered):
        raise ValueError("train_size plus test_size must not exceed observations length")

    splits: list[WalkForwardSplit] = []
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > len(ordered):
            break
        splits.append(
            WalkForwardSplit(
                train=ordered[train_start:train_end],
                test=ordered[test_start:test_end],
                train_start_index=train_start,
                train_end_index=train_end,
                test_start_index=test_start,
                test_end_index=test_end,
            )
        )
        train_start += step_size

    return splits


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


def _coerce_ordered_observations(observations: Sequence[Any] | int) -> tuple[Any, ...]:
    if isinstance(observations, int):
        if observations <= 0:
            raise ValueError("observations must be a positive integer or a non-empty sequence")
        return tuple(range(observations))
    if not observations:
        raise ValueError("observations must be a positive integer or a non-empty sequence")
    return tuple(observations)


def _csv_safe_endpoint(value: Any) -> ReportScalar:
    if isinstance(value, str | int | float | bool | date | datetime) or value is None:
        return value
    if isinstance(value, Mapping | Sequence):
        return None
    return None


def _evaluate_statistic(statistic: Statistic, values: Sequence[float]) -> float:
    try:
        result = float(statistic(values))
    except (TypeError, ValueError) as exc:
        raise ValueError("statistic must return a finite numeric value") from exc
    if not isfinite(result):
        raise ValueError("statistic must return a finite numeric value")
    return result


def _evaluate_distribution_value(value: float) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("distribution values must be finite numeric values") from exc
    if not isfinite(result):
        raise ValueError("distribution values must be finite numeric values")
    return result


def _iter_named_distributions(
    distributions: Mapping[str, Sequence[float]] | Sequence[tuple[str, Sequence[float]]],
) -> tuple[tuple[str, Sequence[float]], ...]:
    if isinstance(distributions, Mapping):
        return tuple(distributions.items())
    if isinstance(distributions, str | bytes):
        raise ValueError("distributions must be an ordered mapping or sequence of baseline ID and distribution pairs")

    named_distributions: list[tuple[str, Sequence[float]]] = []
    for item in distributions:
        if not isinstance(item, Sequence) or isinstance(item, str | bytes) or len(item) != 2:
            raise ValueError("distributions must be an ordered mapping or sequence of baseline ID and distribution pairs")
        baseline_id, distribution = item
        if not isinstance(baseline_id, str):
            raise ValueError("baseline IDs must be strings")
        named_distributions.append((baseline_id, distribution))
    return tuple(named_distributions)


def _coerce_interval_bounds(interval: Sequence[float]) -> tuple[float, float]:
    if isinstance(interval, str | bytes):
        raise ValueError("interval must contain exactly two finite numeric bounds")
    if len(interval) != 2:
        raise ValueError("interval must contain exactly two finite numeric bounds")

    try:
        lower = float(interval[0])
        upper = float(interval[1])
    except (TypeError, ValueError) as exc:
        raise ValueError("interval must contain exactly two finite numeric bounds") from exc
    if not isfinite(lower) or not isfinite(upper):
        raise ValueError("interval must contain exactly two finite numeric bounds")
    return lower, upper


def _iter_named_intervals(
    intervals: Mapping[str, Sequence[float]] | Sequence[tuple[str, Sequence[float]]],
) -> tuple[tuple[str, Sequence[float]], ...]:
    if isinstance(intervals, Mapping):
        return tuple(intervals.items())
    if isinstance(intervals, str | bytes):
        raise ValueError("intervals must be an ordered mapping or sequence of name and interval pairs")

    named_intervals: list[tuple[str, Sequence[float]]] = []
    for item in intervals:
        if not isinstance(item, Sequence) or isinstance(item, str | bytes) or len(item) != 2:
            raise ValueError("intervals must be an ordered mapping or sequence of name and interval pairs")
        statistic_name, interval = item
        if not isinstance(statistic_name, str):
            raise ValueError("statistic names must be strings")
        named_intervals.append((statistic_name, interval))
    return tuple(named_intervals)


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
