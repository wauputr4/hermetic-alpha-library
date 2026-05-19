import pytest

from hermetic_alpha.analysis import (
    PermutationTestResult,
    WalkForwardSplit,
    bootstrap_percentile_interval,
    low_sample_warning,
    permutation_test,
    permutation_test_result_row,
    random_baseline_distribution,
    walk_forward_splits,
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


def test_permutation_test_is_seeded_and_inspectable():
    first = permutation_test(
        [1.0, 1.0, 0.0],
        [0.0, 0.0, 0.0],
        permutations=20,
        seed=19,
        alternative="greater",
    )
    second = permutation_test(
        [1.0, 1.0, 0.0],
        [0.0, 0.0, 0.0],
        permutations=20,
        seed=19,
        alternative="greater",
    )

    assert isinstance(first, PermutationTestResult)
    assert first == second
    assert first.observed_statistic == pytest.approx(2 / 3)
    assert first.p_value == pytest.approx(6 / 21)
    assert first.to_dict()["seed"] == 19


def test_permutation_test_supports_two_sided_p_value():
    result = permutation_test(
        [3.0, 4.0],
        [1.0, 2.0],
        permutations=8,
        seed=2,
        alternative="two-sided",
    )

    assert result.observed_statistic == 3.5
    assert result.null_mean == pytest.approx(3.0625)
    assert result.p_value == pytest.approx(6 / 9)


def test_permutation_test_supports_event_study_style_probability_statistic():
    result = permutation_test(
        [1.0, 1.0, 0.0],
        [1.0, 0.0, 0.0, 0.0],
        permutations=25,
        seed=5,
        statistic=lambda values: sum(values) / len(values),
        alternative="greater",
    )

    assert result.observed_statistic == pytest.approx(2 / 3)
    assert 0 < result.p_value <= 1


def test_permutation_test_result_row_flattens_distribution_metadata():
    result = permutation_test(
        [1.0, 1.0, 0.0],
        [0.0, 0.0, 0.0],
        permutations=20,
        seed=19,
        alternative="greater",
    )

    row = permutation_test_result_row(result)

    assert row == {
        "observed_statistic": pytest.approx(2 / 3),
        "p_value": pytest.approx(6 / 21),
        "alternative": "greater",
        "permutations": 20,
        "seed": 19,
        "null_mean": pytest.approx(result.null_mean),
        "null_distribution_count": 20,
        "null_distribution_min": min(result.null_distribution),
        "null_distribution_max": max(result.null_distribution),
    }
    assert result.to_dict()["null_distribution"] == result.null_distribution


def test_permutation_test_result_row_handles_empty_distribution_explicitly():
    result = PermutationTestResult(
        observed_statistic=0.25,
        p_value=1.0,
        alternative="two-sided",
        permutations=0,
        seed=None,
        null_distribution=[],
        null_mean=0.0,
    )

    row = permutation_test_result_row(result)

    assert row["null_distribution_count"] == 0
    assert row["null_distribution_min"] is None
    assert row["null_distribution_max"] is None


def test_walk_forward_splits_generate_chronological_windows():
    splits = walk_forward_splits(["d1", "d2", "d3", "d4", "d5", "d6"], train_size=3, test_size=1)

    assert splits == [
        WalkForwardSplit(("d1", "d2", "d3"), ("d4",), 0, 3, 3, 4),
        WalkForwardSplit(("d2", "d3", "d4"), ("d5",), 1, 4, 4, 5),
        WalkForwardSplit(("d3", "d4", "d5"), ("d6",), 2, 5, 5, 6),
    ]
    assert splits[0].to_dict() == {
        "train": ["d1", "d2", "d3"],
        "test": ["d4"],
        "train_start_index": 0,
        "train_end_index": 3,
        "test_start_index": 3,
        "test_end_index": 4,
    }


def test_walk_forward_splits_support_index_counts_and_step_size():
    splits = walk_forward_splits(10, train_size=3, test_size=2, step_size=2)

    assert [(split.train, split.test) for split in splits] == [
        ((0, 1, 2), (3, 4)),
        ((2, 3, 4), (5, 6)),
        ((4, 5, 6), (7, 8)),
    ]


def test_walk_forward_splits_prevent_train_test_leakage():
    splits = walk_forward_splits(range(8), train_size=3, test_size=2, step_size=2)

    for split in splits:
        assert split.train_end_index == split.test_start_index
        assert max(split.train) < min(split.test)


def test_walk_forward_splits_validate_inputs():
    with pytest.raises(ValueError, match="observations must be"):
        walk_forward_splits([], train_size=1, test_size=1)

    with pytest.raises(ValueError, match="train_size must be"):
        walk_forward_splits([1, 2], train_size=0, test_size=1)

    with pytest.raises(ValueError, match="test_size must be"):
        walk_forward_splits([1, 2], train_size=1, test_size=0)

    with pytest.raises(ValueError, match="step_size must be"):
        walk_forward_splits([1, 2, 3], train_size=1, test_size=1, step_size=0)

    with pytest.raises(ValueError, match="avoid overlapping test windows"):
        walk_forward_splits([1, 2, 3, 4, 5], train_size=2, test_size=2, step_size=1)

    with pytest.raises(ValueError, match="must not exceed observations length"):
        walk_forward_splits([1, 2], train_size=2, test_size=1)


def test_validation_helpers_validate_inputs():
    with pytest.raises(ValueError, match="values must not be empty"):
        bootstrap_percentile_interval([])

    with pytest.raises(ValueError, match="sample_size must not exceed values length"):
        random_baseline_distribution([1.0], 2)

    with pytest.raises(ValueError, match="sample_size must not be negative"):
        low_sample_warning(-1)

    with pytest.raises(ValueError, match="observed_values must not be empty"):
        permutation_test([], [1.0])

    with pytest.raises(ValueError, match="baseline_values must not be empty"):
        permutation_test([1.0], [])

    with pytest.raises(ValueError, match="permutations must be a positive integer"):
        permutation_test([1.0], [0.0], permutations=0)

    with pytest.raises(ValueError, match="alternative must be"):
        permutation_test([1.0], [0.0], alternative="different")

    with pytest.raises(ValueError, match="statistic must return a finite numeric value"):
        permutation_test([1.0], [0.0], statistic=lambda values: "not numeric")


def test_low_sample_warning_returns_message_only_below_threshold():
    assert low_sample_warning(30) is None
    assert low_sample_warning(4, minimum=5) == (
        "Low sample size: 4 observations; treat results as exploratory until at least 5 are available."
    )
