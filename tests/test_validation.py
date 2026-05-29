import pytest

from hermetic_alpha.analysis import (
    PermutationTestResult,
    WalkForwardSplit,
    bootstrap_interval_row,
    bootstrap_interval_rows,
    bootstrap_percentile_interval,
    low_sample_warning,
    permutation_test,
    permutation_test_result_row,
    permutation_test_result_rows,
    random_baseline_distribution,
    random_baseline_distribution_row,
    random_baseline_distribution_rows,
    walk_forward_split_group_rows,
    walk_forward_split_rows,
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


def test_bootstrap_interval_row_flattens_seeded_interval_metadata():
    interval = bootstrap_percentile_interval([0.01, 0.02, 0.05, -0.01], samples=200, seed=7)

    row = bootstrap_interval_row(
        interval,
        samples=200,
        confidence=0.95,
        seed=7,
        statistic_name="mean_return",
    )

    assert row == {
        "interval_lower": pytest.approx(-0.0025),
        "interval_upper": pytest.approx(0.035),
        "samples": 200,
        "confidence": 0.95,
        "seed": 7,
        "statistic_name": "mean_return",
    }
    assert tuple(round(value, 4) for value in interval) == (-0.0025, 0.035)


def test_bootstrap_interval_row_allows_omitted_metadata():
    row = bootstrap_interval_row((0.1, 0.2))

    assert row == {
        "interval_lower": 0.1,
        "interval_upper": 0.2,
        "samples": None,
        "confidence": None,
        "seed": None,
        "statistic_name": None,
    }


def test_bootstrap_interval_rows_preserve_mapping_order_and_shared_metadata():
    rows = bootstrap_interval_rows(
        {
            "mean_return": (0.01, 0.05),
            "bullish_probability": (0.4, 0.7),
        },
        samples=500,
        confidence=0.9,
        seed=17,
    )

    assert rows == [
        {
            "interval_lower": 0.01,
            "interval_upper": 0.05,
            "samples": 500,
            "confidence": 0.9,
            "seed": 17,
            "statistic_name": "mean_return",
        },
        {
            "interval_lower": 0.4,
            "interval_upper": 0.7,
            "samples": 500,
            "confidence": 0.9,
            "seed": 17,
            "statistic_name": "bullish_probability",
        },
    ]


def test_bootstrap_interval_rows_preserve_sequence_order():
    rows = bootstrap_interval_rows([
        ("median_return", (-0.02, 0.03)),
        ("mean_return", (0.01, 0.05)),
    ])

    assert [row["statistic_name"] for row in rows] == ["median_return", "mean_return"]
    assert rows[0]["interval_lower"] == -0.02
    assert rows[1]["interval_upper"] == 0.05


def test_random_baseline_distribution_is_deterministic_with_seed():
    first = random_baseline_distribution([1.0, 2.0, 3.0, 4.0], 2, samples=5, seed=11)
    second = random_baseline_distribution([1.0, 2.0, 3.0, 4.0], 2, samples=5, seed=11)

    assert first == second
    assert first == [3.5, 3.0, 1.5, 3.5, 1.5]


def test_random_baseline_distribution_row_summarizes_seeded_distribution():
    distribution = random_baseline_distribution(
        [1.0, 2.0, 3.0, 4.0],
        2,
        samples=5,
        seed=11,
    )

    row = random_baseline_distribution_row(
        distribution,
        sample_size=2,
        samples=5,
        seed=11,
    )

    assert row == {
        "distribution_count": 5,
        "distribution_min": 1.5,
        "distribution_max": 3.5,
        "distribution_mean": 2.6,
        "sample_size": 2,
        "samples": 5,
        "seed": 11,
    }
    assert distribution == [3.5, 3.0, 1.5, 3.5, 1.5]


def test_random_baseline_distribution_row_handles_empty_distribution():
    row = random_baseline_distribution_row([], sample_size=2, samples=0, seed=None)

    assert row == {
        "distribution_count": 0,
        "distribution_min": None,
        "distribution_max": None,
        "distribution_mean": None,
        "sample_size": 2,
        "samples": 0,
        "seed": None,
    }


def test_random_baseline_distribution_rows_preserve_mapping_order_and_shared_metadata():
    rows = random_baseline_distribution_rows(
        {
            "all_windows": [0.1, 0.2, 0.3],
            "same_regime": [-0.1, 0.0, 0.1],
        },
        sample_size=2,
        samples=100,
        seed=11,
    )

    assert rows == [
        {
            "baseline_id": "all_windows",
            "distribution_count": 3,
            "distribution_min": 0.1,
            "distribution_max": 0.3,
            "distribution_mean": pytest.approx(0.2),
            "sample_size": 2,
            "samples": 100,
            "seed": 11,
        },
        {
            "baseline_id": "same_regime",
            "distribution_count": 3,
            "distribution_min": -0.1,
            "distribution_max": 0.1,
            "distribution_mean": 0.0,
            "sample_size": 2,
            "samples": 100,
            "seed": 11,
        },
    ]


def test_random_baseline_distribution_rows_preserve_sequence_order_and_empty_distributions():
    rows = random_baseline_distribution_rows([
        ("same_month", []),
        ("all_windows", [1.0, 3.0]),
    ])

    assert [row["baseline_id"] for row in rows] == ["same_month", "all_windows"]
    assert rows[0]["distribution_count"] == 0
    assert rows[0]["distribution_min"] is None
    assert rows[1]["distribution_mean"] == 2.0


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


def test_permutation_test_result_rows_preserve_mapping_order():
    first = permutation_test(
        [1.0, 1.0, 0.0],
        [0.0, 0.0, 0.0],
        permutations=20,
        seed=19,
        alternative="greater",
    )
    second = PermutationTestResult(
        observed_statistic=0.25,
        p_value=1.0,
        alternative="two-sided",
        permutations=0,
        seed=None,
        null_distribution=[],
        null_mean=0.0,
    )

    rows = permutation_test_result_rows({
        "bullish_7d": first,
        "mean_return_7d": second,
    })

    assert [row["scenario_id"] for row in rows] == ["bullish_7d", "mean_return_7d"]
    assert rows[0]["null_distribution_count"] == 20
    assert rows[1]["null_distribution_count"] == 0
    assert rows[1]["null_distribution_min"] is None
    assert rows[1]["null_distribution_max"] is None


def test_permutation_test_result_rows_preserve_sequence_order():
    first = PermutationTestResult(
        observed_statistic=0.5,
        p_value=0.25,
        alternative="greater",
        permutations=3,
        seed=7,
        null_distribution=[0.1, 0.2, 0.3],
        null_mean=0.2,
    )
    second = PermutationTestResult(
        observed_statistic=-0.1,
        p_value=0.5,
        alternative="less",
        permutations=2,
        seed=11,
        null_distribution=[-0.2, 0.0],
        null_mean=-0.1,
    )

    rows = permutation_test_result_rows([
        ("mean_return_30d", first),
        ("bullish_1d", second),
    ])

    assert [row["scenario_id"] for row in rows] == ["mean_return_30d", "bullish_1d"]
    assert rows[0]["observed_statistic"] == 0.5
    assert rows[1]["alternative"] == "less"


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


def test_walk_forward_split_rows_flatten_boundaries_and_endpoints():
    splits = walk_forward_splits(["d1", "d2", "d3", "d4", "d5", "d6"], train_size=3, test_size=1)

    rows = walk_forward_split_rows(splits)

    assert rows == [
        {
            "split_index": 0,
            "train_start_index": 0,
            "train_end_index": 3,
            "test_start_index": 3,
            "test_end_index": 4,
            "train_size": 3,
            "test_size": 1,
            "train_first": "d1",
            "train_last": "d3",
            "test_first": "d4",
            "test_last": "d4",
        },
        {
            "split_index": 1,
            "train_start_index": 1,
            "train_end_index": 4,
            "test_start_index": 4,
            "test_end_index": 5,
            "train_size": 3,
            "test_size": 1,
            "train_first": "d2",
            "train_last": "d4",
            "test_first": "d5",
            "test_last": "d5",
        },
        {
            "split_index": 2,
            "train_start_index": 2,
            "train_end_index": 5,
            "test_start_index": 5,
            "test_end_index": 6,
            "train_size": 3,
            "test_size": 1,
            "train_first": "d3",
            "train_last": "d5",
            "test_first": "d6",
            "test_last": "d6",
        },
    ]
    assert splits[0].to_dict() == {
        "train": ["d1", "d2", "d3"],
        "test": ["d4"],
        "train_start_index": 0,
        "train_end_index": 3,
        "test_start_index": 3,
        "test_end_index": 4,
    }


def test_walk_forward_split_rows_replace_nested_endpoints_with_none():
    split = WalkForwardSplit(
        train=({"close": 100.0}, {"close": 101.0}),
        test=([102.0], [103.0]),
        train_start_index=0,
        train_end_index=2,
        test_start_index=2,
        test_end_index=4,
    )

    rows = walk_forward_split_rows([split])

    assert rows[0]["train_first"] is None
    assert rows[0]["train_last"] is None
    assert rows[0]["test_first"] is None
    assert rows[0]["test_last"] is None


def test_walk_forward_split_group_rows_preserve_mapping_order_and_emit_group_ids():
    expanding = walk_forward_splits(["d1", "d2", "d3", "d4", "d5"], train_size=2, test_size=1)
    monthly = walk_forward_splits(["m1", "m2", "m3", "m4"], train_size=2, test_size=1, step_size=1)

    rows = walk_forward_split_group_rows({
        "expanding-daily": expanding,
        "monthly": monthly[:1],
    })

    assert [row["split_group_id"] for row in rows] == [
        "expanding-daily",
        "expanding-daily",
        "expanding-daily",
        "monthly",
    ]
    assert rows[0]["split_index"] == 0
    assert rows[2]["test_last"] == "d5"
    assert rows[3]["train_first"] == "m1"


def test_walk_forward_split_group_rows_preserve_pair_order_and_skip_empty_groups():
    active = walk_forward_splits([1, 2, 3, 4], train_size=2, test_size=1)

    rows = walk_forward_split_group_rows([
        ("empty", []),
        ("active", active[:1]),
    ])

    assert [row["split_group_id"] for row in rows] == ["active"]
    assert rows[0]["train_size"] == 2
    assert rows[0]["test_first"] == 3


def test_walk_forward_split_group_rows_reject_duplicate_and_blank_group_ids():
    split = WalkForwardSplit(("d1",), ("d2",), 0, 1, 1, 2)

    with pytest.raises(ValueError, match="split group IDs must be unique"):
        walk_forward_split_group_rows([("daily", [split]), ("daily", [split])])

    with pytest.raises(ValueError, match="split group ID must not be blank"):
        walk_forward_split_group_rows([("   ", [split])])


def test_walk_forward_split_group_rows_reject_whitespace_padded_group_ids():
    split = WalkForwardSplit(("d1",), ("d2",), 0, 1, 1, 2)

    with pytest.raises(ValueError, match="split group ID must not include leading or trailing whitespace"):
        walk_forward_split_group_rows([(" daily", [split])])

    with pytest.raises(ValueError, match="split group ID must not include leading or trailing whitespace"):
        walk_forward_split_group_rows([("daily ", [split])])


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

    with pytest.raises(ValueError, match="distribution values must be finite numeric values"):
        random_baseline_distribution_row([float("nan")])

    with pytest.raises(ValueError, match="baseline IDs must be unique"):
        random_baseline_distribution_rows([
            ("all_windows", [0.1]),
            ("all_windows", [0.2]),
        ])

    with pytest.raises(ValueError, match="baseline ID must not be blank"):
        random_baseline_distribution_rows([("   ", [0.1])])

    with pytest.raises(ValueError, match="baseline ID must not include leading or trailing whitespace"):
        random_baseline_distribution_rows([(" baseline", [0.1])])

    with pytest.raises(ValueError, match="baseline ID must not include leading or trailing whitespace"):
        random_baseline_distribution_rows([("baseline ", [0.1])])

    with pytest.raises(ValueError, match="baseline ID must be a string"):
        random_baseline_distribution_rows({123: [0.1]})  # type: ignore[dict-item]

    with pytest.raises(ValueError, match="distribution values must be finite numeric values"):
        random_baseline_distribution_rows({"all_windows": [float("nan")]})

    with pytest.raises(ValueError, match="interval must contain exactly two finite numeric bounds"):
        bootstrap_interval_row((0.1,))

    with pytest.raises(ValueError, match="interval must contain exactly two finite numeric bounds"):
        bootstrap_interval_row(("low", 0.2))

    with pytest.raises(ValueError, match="interval must contain exactly two finite numeric bounds"):
        bootstrap_interval_row((0.1, float("nan")))

    with pytest.raises(ValueError, match="statistic names must be unique"):
        bootstrap_interval_rows([
            ("mean_return", (0.1, 0.2)),
            ("mean_return", (0.2, 0.3)),
        ])

    with pytest.raises(ValueError, match="statistic name must not be blank"):
        bootstrap_interval_rows([("   ", (0.1, 0.2))])

    with pytest.raises(ValueError, match="statistic name must not include leading or trailing whitespace"):
        bootstrap_interval_rows([(" mean", (0.1, 0.2))])

    with pytest.raises(ValueError, match="statistic name must not include leading or trailing whitespace"):
        bootstrap_interval_rows([("mean ", (0.1, 0.2))])

    with pytest.raises(ValueError, match="statistic name must be a string"):
        bootstrap_interval_rows({123: (0.1, 0.2)})  # type: ignore[dict-item]

    with pytest.raises(ValueError, match="interval must contain exactly two finite numeric bounds"):
        bootstrap_interval_rows({"mean_return": (0.1,)})

    result = PermutationTestResult(
        observed_statistic=0.5,
        p_value=0.25,
        alternative="greater",
        permutations=3,
        seed=7,
        null_distribution=[0.1, 0.2, 0.3],
        null_mean=0.2,
    )
    with pytest.raises(ValueError, match="scenario IDs must be unique"):
        permutation_test_result_rows([
            ("bullish_7d", result),
            ("bullish_7d", result),
        ])

    with pytest.raises(ValueError, match="scenario ID must not be blank"):
        permutation_test_result_rows([("   ", result)])

    with pytest.raises(ValueError, match="scenario ID must not include leading or trailing whitespace"):
        permutation_test_result_rows([(" scenario", result)])

    with pytest.raises(ValueError, match="scenario ID must not include leading or trailing whitespace"):
        permutation_test_result_rows([("scenario ", result)])

    with pytest.raises(ValueError, match="scenario ID must be a string"):
        permutation_test_result_rows({123: result})  # type: ignore[dict-item]

    with pytest.raises(ValueError, match="results must contain PermutationTestResult values"):
        permutation_test_result_rows([("bullish_7d", object())])

    split = WalkForwardSplit(("d1",), ("d2",), 0, 1, 1, 2)
    with pytest.raises(ValueError, match="split group ID must be a string"):
        walk_forward_split_group_rows({123: [split]})  # type: ignore[dict-item]


def test_low_sample_warning_returns_message_only_below_threshold():
    assert low_sample_warning(30) is None
    assert low_sample_warning(4, minimum=5) == (
        "Low sample size: 4 observations; treat results as exploratory until at least 5 are available."
    )
