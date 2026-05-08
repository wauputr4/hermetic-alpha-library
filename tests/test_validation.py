import pytest

from hermetic_alpha.analysis import (
    bootstrap_percentile_interval,
    low_sample_warning,
    random_baseline_distribution,
)


def test_bootstrap_percentile_interval_is_seeded_and_stable():
    interval = bootstrap_percentile_interval([0.01, 0.02, 0.05, -0.01], samples=200, seed=7)

    assert tuple(round(value, 4) for value in interval) == (-0.0025, 0.035)


def test_bootstrap_percentile_interval_supports_custom_statistic():
    interval = bootstrap_percentile_interval(
        [0.0, 1.0, 1.0, 1.0],
        samples=200,
        seed=3,
        statistic=lambda values: sum(1 for value in values if value > 0) / len(values),
    )

    assert tuple(round(value, 4) for value in interval) == (0.25, 1.0)


def test_random_baseline_distribution_is_deterministic_with_seed():
    first = random_baseline_distribution([1.0, 2.0, 3.0, 4.0], 2, samples=5, seed=11)
    second = random_baseline_distribution([1.0, 2.0, 3.0, 4.0], 2, samples=5, seed=11)

    assert first == second
    assert first == [3.5, 3.0, 1.5, 3.5, 1.5]


def test_validation_helpers_validate_inputs():
    with pytest.raises(ValueError, match="values must not be empty"):
        bootstrap_percentile_interval([])

    with pytest.raises(ValueError, match="sample_size must not exceed values length"):
        random_baseline_distribution([1.0], 2)

    with pytest.raises(ValueError, match="sample_size must not be negative"):
        low_sample_warning(-1)


def test_low_sample_warning_returns_message_only_below_threshold():
    assert low_sample_warning(30) is None
    assert low_sample_warning(4, minimum=5) == (
        "Low sample size: 4 observations; treat results as exploratory until at least 5 are available."
    )
