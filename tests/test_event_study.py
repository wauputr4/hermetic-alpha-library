import pytest
from datetime import datetime, timezone

from hermetic_alpha.analysis import (
    ValidatedEventStudyReport,
    event_study_baseline_comparison_row,
    join_aspect_events_to_market_labels,
    multi_horizon_baseline_comparison_group_rows,
    multi_horizon_baseline_comparison_rows,
    summarize_event_study,
    summarize_multi_horizon_event_study,
    summarize_validated_event_study,
    summarize_validated_multi_horizon_event_study,
    timestamp_join_summary_row,
    timestamp_join_summary_rows,
    validated_event_study_report_row,
    validated_multi_horizon_event_study_report_group_rows,
    validated_multi_horizon_event_study_report_rows,
)
from hermetic_alpha.labels import (
    add_candle_forward_returns,
    add_candle_local_extrema_labels,
    add_forward_returns,
    add_local_extrema_labels,
    bullish_probability,
    forward_return_label_coverage_row,
    forward_return_label_group_rows,
    local_extrema_label_coverage_row,
    multi_dataset_forward_return_label_coverage_rows,
    multi_dataset_local_extrema_label_coverage_rows,
    multi_horizon_forward_return_label_coverage_rows,
    multi_window_local_extrema_label_coverage_rows,
)
from hermetic_alpha.models import AspectEvent, MarketCandle, MarketLabel


def test_forward_returns_and_bullish_probability():
    labels = add_forward_returns([100, 110, 99, 120], [1])
    assert round(labels[0]["return_1d"], 4) == 0.1
    assert labels[-1]["return_1d"] is None
    assert bullish_probability(labels, 1) == 2 / 3


def test_forward_returns_with_zero_close_is_safe():
    labels = add_forward_returns([100, 0, 110], [1])

    assert labels[0]["return_1d"] == -1.0
    assert labels[0]["bullish_1d"] is False
    assert labels[1]["return_1d"] is None
    assert labels[1]["bullish_1d"] is None


def test_candle_forward_returns_preserve_timestamp_and_asset():
    ts1 = datetime(2026, 5, 6, tzinfo=timezone.utc)
    ts2 = datetime(2026, 5, 7, tzinfo=timezone.utc)
    labels = add_candle_forward_returns(
        [
            MarketCandle(ts1, "BTC-USD", 100, 110, 90, 100),
            MarketCandle(ts2, "BTC-USD", 105, 115, 95, 110),
        ],
        [1],
    )

    assert labels[0]["timestamp"] == ts1
    assert labels[0]["asset"] == "BTC-USD"
    assert labels[0]["return_1d"] == pytest.approx(0.1)
    assert labels[0]["bullish_1d"] is True
    assert labels[1] == {"timestamp": ts2, "asset": "BTC-USD", "return_1d": None, "bullish_1d": None}


def test_candle_forward_returns_match_multi_horizon_close_labels():
    candles = [
        MarketCandle(datetime(2026, 5, day, tzinfo=timezone.utc), "BTC-USD", close, close, close, close)
        for day, close in [(6, 100), (7, 110), (8, 121), (9, 90)]
    ]

    labels = add_candle_forward_returns(candles, [1, 2])

    expected = add_forward_returns([100, 110, 121, 90], [1, 2])
    for index, expected_row in enumerate(expected):
        assert labels[index]["timestamp"] == candles[index].timestamp
        assert labels[index]["asset"] == "BTC-USD"
        assert {key: labels[index][key] for key in expected_row} == expected_row


def test_candle_forward_returns_with_zero_close_is_safe():
    candles = [
        MarketCandle(datetime(2026, 5, day, tzinfo=timezone.utc), "BTC-USD", close, close, close, close)
        for day, close in [(6, 100), (7, 0), (8, 110)]
    ]

    labels = add_candle_forward_returns(candles, [1])

    assert labels[0]["return_1d"] == -1.0
    assert labels[0]["bullish_1d"] is False
    assert labels[1]["return_1d"] is None
    assert labels[1]["bullish_1d"] is None


def test_candle_forward_returns_reject_mixed_assets():
    candles = [
        MarketCandle(datetime(2026, 5, 6, tzinfo=timezone.utc), "BTC-USD", 100, 100, 100, 100),
        MarketCandle(datetime(2026, 5, 7, tzinfo=timezone.utc), "ETH-USD", 110, 110, 110, 110),
    ]

    with pytest.raises(ValueError, match="single asset"):
        add_candle_forward_returns(candles, [1])


def test_forward_return_label_coverage_row_summarizes_timestamped_candle_labels():
    candles = [
        MarketCandle(datetime(2026, 5, day, tzinfo=timezone.utc), "BTC-USD", close, close, close, close)
        for day, close in [(6, 100), (7, 110), (8, 99), (9, 120)]
    ]
    labels = add_candle_forward_returns(candles, [1])

    row = forward_return_label_coverage_row(labels, 1, dataset_id="btc-daily")

    assert row == {
        "dataset_id": "btc-daily",
        "horizon": 1,
        "row_count": 4,
        "labeled_return_count": 3,
        "bullish_count": 2,
        "bearish_count": 1,
        "missing_label_count": 1,
        "asset": "BTC-USD",
        "first_timestamp": candles[0].timestamp,
        "last_timestamp": candles[-1].timestamp,
    }


def test_forward_return_label_coverage_row_summarizes_plain_close_labels():
    labels = add_forward_returns([100, 90, 120], [1])

    row = forward_return_label_coverage_row(labels, 1)

    assert row["dataset_id"] is None
    assert row["row_count"] == 3
    assert row["labeled_return_count"] == 2
    assert row["bullish_count"] == 1
    assert row["bearish_count"] == 1
    assert row["missing_label_count"] == 1
    assert row["asset"] is None
    assert row["first_timestamp"] is None
    assert row["last_timestamp"] is None


def test_forward_return_label_coverage_row_handles_empty_input_and_missing_horizon():
    assert forward_return_label_coverage_row([], 1) == {
        "dataset_id": None,
        "horizon": 1,
        "row_count": 0,
        "labeled_return_count": 0,
        "bullish_count": 0,
        "bearish_count": 0,
        "missing_label_count": 0,
        "asset": None,
        "first_timestamp": None,
        "last_timestamp": None,
    }

    row = forward_return_label_coverage_row([{"return_2d": 0.1, "bullish_2d": True}], 1)
    assert row["row_count"] == 1
    assert row["labeled_return_count"] == 0
    assert row["missing_label_count"] == 1


def test_forward_return_label_coverage_row_validates_horizon():
    with pytest.raises(ValueError, match="positive integer"):
        forward_return_label_coverage_row([], 0)


def test_forward_return_label_coverage_row_rejects_blank_dataset_id():
    with pytest.raises(ValueError, match="dataset ID must not be blank"):
        forward_return_label_coverage_row([], 1, dataset_id="   ")


def test_forward_return_label_coverage_row_rejects_non_string_dataset_id():
    with pytest.raises(ValueError, match="dataset ID must be a string"):
        forward_return_label_coverage_row([], 1, dataset_id=123)  # type: ignore[arg-type]


def test_multi_horizon_forward_return_label_coverage_rows_preserve_order_and_deduplicate():
    labels = add_forward_returns([100, 110, 99, 120], [1, 2])

    rows = multi_horizon_forward_return_label_coverage_rows(labels, [2, 1, 2], dataset_id="close-list")

    assert [row["horizon"] for row in rows] == [2, 1]
    assert [row["dataset_id"] for row in rows] == ["close-list", "close-list"]
    assert rows[0]["row_count"] == 4
    assert rows[0]["labeled_return_count"] == 2
    assert rows[1]["labeled_return_count"] == 3


def test_multi_horizon_forward_return_label_coverage_rows_summarize_timestamped_candle_labels():
    candles = [
        MarketCandle(datetime(2026, 5, day, tzinfo=timezone.utc), "BTC-USD", close, close, close, close)
        for day, close in [(6, 100), (7, 110), (8, 99), (9, 120)]
    ]
    labels = add_candle_forward_returns(candles, [1, 2])

    rows = multi_horizon_forward_return_label_coverage_rows(labels, [1, 2], dataset_id="btc-daily")

    assert len(rows) == 2
    assert rows[0]["asset"] == "BTC-USD"
    assert rows[0]["first_timestamp"] == candles[0].timestamp
    assert rows[0]["last_timestamp"] == candles[-1].timestamp
    assert rows[1]["horizon"] == 2
    assert rows[1]["labeled_return_count"] == 2


def test_multi_horizon_forward_return_label_coverage_rows_validate_horizons():
    with pytest.raises(ValueError, match="positive integers"):
        multi_horizon_forward_return_label_coverage_rows([], [])
    with pytest.raises(ValueError, match="positive integers"):
        multi_horizon_forward_return_label_coverage_rows([], [1, 0])
    with pytest.raises(ValueError, match="dataset ID must not be blank"):
        multi_horizon_forward_return_label_coverage_rows([], [1], dataset_id=" ")


def test_multi_dataset_forward_return_label_coverage_rows_preserve_ordered_mapping_order():
    train = add_forward_returns([100, 110, 99, 120], [1, 2])
    test = add_forward_returns([200, 190, 210], [1, 2])

    rows = multi_dataset_forward_return_label_coverage_rows({"train": train, "test": test}, [2, 1, 2])

    assert [(row["dataset_id"], row["horizon"]) for row in rows] == [
        ("train", 2),
        ("train", 1),
        ("test", 2),
        ("test", 1),
    ]
    assert rows[0]["row_count"] == 4
    assert rows[2]["row_count"] == 3


def test_multi_dataset_forward_return_label_coverage_rows_accepts_ordered_pairs():
    train = add_forward_returns([100, 110, 99], [1])
    test = add_forward_returns([200, 210, 220], [1])

    rows = multi_dataset_forward_return_label_coverage_rows([("test", test), ("train", train)], [1])

    assert [row["dataset_id"] for row in rows] == ["test", "train"]


def test_multi_dataset_forward_return_label_coverage_rows_validates_dataset_ids():
    labels = add_forward_returns([100, 110], [1])

    with pytest.raises(ValueError, match="dataset IDs must be unique"):
        multi_dataset_forward_return_label_coverage_rows([("train", labels), ("train", labels)], [1])
    with pytest.raises(ValueError, match="dataset ID must not be blank"):
        multi_dataset_forward_return_label_coverage_rows([(" ", labels)], [1])
    with pytest.raises(ValueError, match="dataset ID must be a string"):
        multi_dataset_forward_return_label_coverage_rows([(123, labels)], [1])  # type: ignore[list-item]


def test_multi_dataset_forward_return_label_coverage_rows_accepts_empty_label_datasets():
    rows = multi_dataset_forward_return_label_coverage_rows({"empty": []}, [1])

    assert rows == [
        {
            "dataset_id": "empty",
            "horizon": 1,
            "row_count": 0,
            "labeled_return_count": 0,
            "bullish_count": 0,
            "bearish_count": 0,
            "missing_label_count": 0,
            "asset": None,
            "first_timestamp": None,
            "last_timestamp": None,
        }
    ]


def test_forward_return_label_group_rows_preserve_dataset_and_row_order():
    train = add_forward_returns([100, 110, 99], [1])
    test = add_forward_returns([200, 190, 210], [1])

    rows = forward_return_label_group_rows([("test", test), ("train", train)])

    assert [row["dataset_id"] for row in rows] == ["test", "test", "test", "train", "train", "train"]
    assert rows[0]["return_1d"] == pytest.approx(-0.05)
    assert rows[0]["bullish_1d"] is False
    assert rows[1]["return_1d"] == pytest.approx(0.10526315789473684)
    assert rows[1]["bullish_1d"] is True
    assert rows[2]["return_1d"] is None
    assert rows[2]["bullish_1d"] is None
    assert rows[3]["return_1d"] == pytest.approx(0.1)
    assert rows[3]["bullish_1d"] is True
    assert rows[4]["return_1d"] == pytest.approx(-0.1)
    assert rows[4]["bullish_1d"] is False
    assert rows[5]["return_1d"] is None
    assert rows[5]["bullish_1d"] is None


def test_forward_return_label_group_rows_preserve_timestamped_label_fields():
    candles = [
        MarketCandle(datetime(2026, 5, day, tzinfo=timezone.utc), "BTC-USD", close, close, close, close)
        for day, close in [(6, 100), (7, 110)]
    ]
    labels = add_candle_forward_returns(candles, [1])

    rows = forward_return_label_group_rows({"btc-daily": labels})

    assert rows[0]["dataset_id"] == "btc-daily"
    assert rows[0]["timestamp"] == candles[0].timestamp
    assert rows[0]["asset"] == "BTC-USD"
    assert rows[0]["return_1d"] == pytest.approx(0.1)
    assert rows[0]["bullish_1d"] is True
    assert rows[1] == {
        "dataset_id": "btc-daily",
        "timestamp": candles[1].timestamp,
        "asset": "BTC-USD",
        "return_1d": None,
        "bullish_1d": None,
    }


def test_forward_return_label_group_rows_validate_dataset_ids():
    labels = add_forward_returns([100, 110], [1])

    with pytest.raises(ValueError, match="dataset IDs must be unique"):
        forward_return_label_group_rows([("train", labels), ("train", labels)])
    with pytest.raises(ValueError, match="dataset ID must not be blank"):
        forward_return_label_group_rows([(" ", labels)])
    with pytest.raises(ValueError, match="dataset ID must be a string"):
        forward_return_label_group_rows([(123, labels)])  # type: ignore[list-item]


def test_forward_return_label_group_rows_skip_empty_label_datasets():
    labels = add_forward_returns([100, 110], [1])

    rows = forward_return_label_group_rows([("empty", []), ("train", labels)])

    assert [row["dataset_id"] for row in rows] == ["train", "train"]


def test_candle_local_extrema_labels_preserve_timestamp_and_asset():
    candles = [
        MarketCandle(datetime(2026, 5, day, tzinfo=timezone.utc), "BTC-USD", close, close, close, close)
        for day, close in [(6, 100), (7, 90), (8, 110)]
    ]

    labels = add_candle_local_extrema_labels(candles, 1)

    assert labels[0] == {
        "timestamp": candles[0].timestamp,
        "asset": "BTC-USD",
        "local_top_1d": None,
        "local_bottom_1d": None,
    }
    assert labels[1]["timestamp"] == candles[1].timestamp
    assert labels[1]["asset"] == "BTC-USD"
    assert labels[1]["local_top_1d"] is False
    assert labels[1]["local_bottom_1d"] is True
    assert labels[2] == {
        "timestamp": candles[2].timestamp,
        "asset": "BTC-USD",
        "local_top_1d": None,
        "local_bottom_1d": None,
    }


def test_candle_local_extrema_labels_match_multi_window_close_labels():
    candles = [
        MarketCandle(datetime(2026, 5, day, tzinfo=timezone.utc), "BTC-USD", close, close, close, close)
        for day, close in [(6, 100), (7, 90), (8, 110), (9, 105), (10, 95), (11, 115), (12, 108)]
    ]

    labels = add_candle_local_extrema_labels(candles, [1, 2, 1])

    expected = add_local_extrema_labels([100, 90, 110, 105, 95, 115, 108], [1, 2, 1])
    for index, expected_row in enumerate(expected):
        assert labels[index]["timestamp"] == candles[index].timestamp
        assert labels[index]["asset"] == "BTC-USD"
        assert {key: labels[index][key] for key in expected_row} == expected_row
    assert labels[1]["local_top_2d"] is None
    assert labels[-2]["local_bottom_2d"] is None


def test_local_extrema_label_coverage_row_summarizes_centered_window_edges():
    labels = add_local_extrema_labels([100, 90, 110, 105, 95], 1)

    row = local_extrema_label_coverage_row(labels, 1, dataset_id="close-list")

    assert row == {
        "dataset_id": "close-list",
        "window": 1,
        "row_count": 5,
        "labeled_count": 3,
        "missing_label_count": 2,
        "local_top_count": 1,
        "local_bottom_count": 1,
        "asset": None,
        "first_timestamp": None,
        "last_timestamp": None,
    }


def test_local_extrema_label_coverage_row_summarizes_timestamped_candle_labels():
    candles = [
        MarketCandle(datetime(2026, 5, day, tzinfo=timezone.utc), "BTC-USD", close, close, close, close)
        for day, close in [(6, 100), (7, 90), (8, 110), (9, 105), (10, 95)]
    ]
    labels = add_candle_local_extrema_labels(candles, 1)

    row = local_extrema_label_coverage_row(labels, 1)

    assert row["row_count"] == 5
    assert row["labeled_count"] == 3
    assert row["missing_label_count"] == 2
    assert row["local_top_count"] == 1
    assert row["local_bottom_count"] == 1
    assert row["asset"] == "BTC-USD"
    assert row["first_timestamp"] == candles[0].timestamp
    assert row["last_timestamp"] == candles[-1].timestamp


def test_local_extrema_label_coverage_row_handles_empty_input_and_missing_window():
    assert local_extrema_label_coverage_row([], 1) == {
        "dataset_id": None,
        "window": 1,
        "row_count": 0,
        "labeled_count": 0,
        "missing_label_count": 0,
        "local_top_count": 0,
        "local_bottom_count": 0,
        "asset": None,
        "first_timestamp": None,
        "last_timestamp": None,
    }

    row = local_extrema_label_coverage_row([{"local_top_2d": True, "local_bottom_2d": False}], 1)
    assert row["row_count"] == 1
    assert row["labeled_count"] == 0
    assert row["missing_label_count"] == 1


def test_local_extrema_label_coverage_row_validates_window():
    with pytest.raises(ValueError, match="positive integer"):
        local_extrema_label_coverage_row([], 0)


def test_local_extrema_label_coverage_row_rejects_blank_dataset_id():
    with pytest.raises(ValueError, match="dataset ID must not be blank"):
        local_extrema_label_coverage_row([], 1, dataset_id="   ")


def test_local_extrema_label_coverage_row_rejects_non_string_dataset_id():
    with pytest.raises(ValueError, match="dataset ID must be a string"):
        local_extrema_label_coverage_row([], 1, dataset_id=123)  # type: ignore[arg-type]


def test_multi_window_local_extrema_label_coverage_rows_preserve_order_and_deduplicate():
    labels = add_local_extrema_labels([100, 90, 110, 105, 80], [1, 2])

    rows = multi_window_local_extrema_label_coverage_rows(labels, [2, 1, 2], dataset_id="close-list")

    assert [row["window"] for row in rows] == [2, 1]
    assert [row["dataset_id"] for row in rows] == ["close-list", "close-list"]
    assert rows[0]["labeled_count"] == 1
    assert rows[0]["missing_label_count"] == 4
    assert rows[1]["labeled_count"] == 3
    assert rows[1]["missing_label_count"] == 2


def test_multi_window_local_extrema_label_coverage_rows_summarize_timestamped_candle_labels():
    candles = [
        MarketCandle(datetime(2026, 5, day, tzinfo=timezone.utc), "BTC-USD", close, close, close, close)
        for day, close in [(6, 100), (7, 90), (8, 110), (9, 105), (10, 80)]
    ]
    labels = add_candle_local_extrema_labels(candles, [1, 2])

    rows = multi_window_local_extrema_label_coverage_rows(labels, [1, 2], dataset_id="btc-daily")

    assert len(rows) == 2
    assert rows[0]["asset"] == "BTC-USD"
    assert rows[0]["first_timestamp"] == candles[0].timestamp
    assert rows[0]["last_timestamp"] == candles[-1].timestamp
    assert rows[1]["window"] == 2
    assert rows[1]["labeled_count"] == 1


def test_multi_window_local_extrema_label_coverage_rows_validate_windows():
    with pytest.raises(ValueError, match="positive integers"):
        multi_window_local_extrema_label_coverage_rows([], [])
    with pytest.raises(ValueError, match="positive integers"):
        multi_window_local_extrema_label_coverage_rows([], [1, 0])
    with pytest.raises(ValueError, match="dataset ID must not be blank"):
        multi_window_local_extrema_label_coverage_rows([], [1], dataset_id=" ")


def test_multi_dataset_local_extrema_label_coverage_rows_preserve_ordered_mapping_order():
    train = add_local_extrema_labels([100, 90, 110, 105, 80], [1, 2])
    test = add_local_extrema_labels([200, 210, 190, 220], [1, 2])

    rows = multi_dataset_local_extrema_label_coverage_rows({"train": train, "test": test}, [2, 1, 2])

    assert [(row["dataset_id"], row["window"]) for row in rows] == [
        ("train", 2),
        ("train", 1),
        ("test", 2),
        ("test", 1),
    ]
    assert rows[0]["row_count"] == 5
    assert rows[2]["row_count"] == 4


def test_multi_dataset_local_extrema_label_coverage_rows_accepts_ordered_pairs():
    train = add_local_extrema_labels([100, 90, 110], 1)
    test = add_local_extrema_labels([200, 210, 190], 1)

    rows = multi_dataset_local_extrema_label_coverage_rows([("test", test), ("train", train)], 1)

    assert [row["dataset_id"] for row in rows] == ["test", "train"]


def test_multi_dataset_local_extrema_label_coverage_rows_validates_dataset_ids():
    labels = add_local_extrema_labels([100, 90, 110], 1)

    with pytest.raises(ValueError, match="dataset IDs must be unique"):
        multi_dataset_local_extrema_label_coverage_rows([("train", labels), ("train", labels)], 1)
    with pytest.raises(ValueError, match="dataset ID must not be blank"):
        multi_dataset_local_extrema_label_coverage_rows([(" ", labels)], 1)
    with pytest.raises(ValueError, match="dataset ID must be a string"):
        multi_dataset_local_extrema_label_coverage_rows([(123, labels)], 1)  # type: ignore[list-item]


def test_multi_dataset_local_extrema_label_coverage_rows_accepts_empty_label_datasets():
    rows = multi_dataset_local_extrema_label_coverage_rows({"empty": []}, 1)

    assert rows == [
        {
            "dataset_id": "empty",
            "window": 1,
            "row_count": 0,
            "labeled_count": 0,
            "missing_label_count": 0,
            "local_top_count": 0,
            "local_bottom_count": 0,
            "asset": None,
            "first_timestamp": None,
            "last_timestamp": None,
        }
    ]


def test_candle_local_extrema_labels_reject_mixed_assets():
    candles = [
        MarketCandle(datetime(2026, 5, 6, tzinfo=timezone.utc), "BTC-USD", 100, 100, 100, 100),
        MarketCandle(datetime(2026, 5, 7, tzinfo=timezone.utc), "ETH-USD", 110, 110, 110, 110),
    ]

    with pytest.raises(ValueError, match="single asset"):
        add_candle_local_extrema_labels(candles, 1)


def test_local_extrema_labels_mark_top_bottom_and_neutral_cases():
    labels = add_local_extrema_labels([100, 90, 110, 105, 95, 115, 108], 1)

    assert labels[0] == {"local_top_1d": None, "local_bottom_1d": None}
    assert labels[1]["local_bottom_1d"] is True
    assert labels[2]["local_top_1d"] is True
    assert labels[3]["local_top_1d"] is False
    assert labels[3]["local_bottom_1d"] is False
    assert labels[-1] == {"local_top_1d": None, "local_bottom_1d": None}


def test_local_extrema_labels_support_multiple_windows():
    labels = add_local_extrema_labels([100, 90, 110, 105, 95, 115, 108], [1, 2, 1])

    assert list(labels[0].keys()) == ["local_top_1d", "local_bottom_1d", "local_top_2d", "local_bottom_2d"]
    assert labels[2]["local_top_1d"] is True
    assert labels[2]["local_top_2d"] is True
    assert labels[4]["local_bottom_1d"] is True
    assert labels[4]["local_bottom_2d"] is True
    assert labels[1]["local_top_2d"] is None
    assert labels[-2]["local_bottom_2d"] is None


def test_local_extrema_labels_validate_window_size():
    with pytest.raises(ValueError, match="windows must be positive integers"):
        add_local_extrema_labels([100, 90, 110], 0)

    with pytest.raises(ValueError, match="windows must be positive integers"):
        add_local_extrema_labels([100, 90, 110], [1, -2])


def test_event_study_summary():
    labels = add_forward_returns([100, 110, 99, 120], [1])
    result = summarize_event_study(labels, [0, 1], 1)
    assert result.events == 2
    assert result.baseline_bullish_probability == 2 / 3
    assert result.conditional_bullish_probability == 1 / 2


def test_multi_horizon_event_study_summary():
    labels = add_forward_returns([100, 110, 121, 90], [1, 2])
    results = summarize_multi_horizon_event_study(labels, [0, 1, 99], [1, 2, 1])

    assert list(results.keys()) == [1, 2]
    assert results[1].events == 2
    assert results[1].conditional_bullish_probability == 1.0
    assert results[2].events == 2
    assert results[2].conditional_bullish_probability == 1 / 2
    assert round(results[2].average_return, 4) == 0.0141


def test_validated_event_study_report_is_seeded_and_warns_on_low_samples():
    labels = add_forward_returns([100, 110, 99, 120, 126], [1])

    report = summarize_validated_event_study(
        labels,
        [0, 1, 2],
        1,
        bootstrap_samples=100,
        bootstrap_seed=17,
        minimum_events=5,
    )
    duplicate = summarize_validated_event_study(
        labels,
        [0, 1, 2],
        1,
        bootstrap_samples=100,
        bootstrap_seed=17,
        minimum_events=5,
    )

    assert isinstance(report, ValidatedEventStudyReport)
    assert report == duplicate
    assert report.summary.events == 3
    assert report.summary.conditional_bullish_probability == 2 / 3
    assert report.low_sample_warning == (
        "Low sample size: 3 observations; treat results as exploratory until at least 5 are available."
    )
    assert tuple(round(value, 4) for value in report.return_confidence_interval or ()) == (-0.1, 0.1747)


def test_validated_event_study_report_skips_interval_when_returns_are_missing():
    labels = add_forward_returns([100, 110], [1])

    report = summarize_validated_event_study(labels, [1], 1, bootstrap_samples=10, minimum_events=1)

    assert report.summary.events == 0
    assert report.summary.average_return is None
    assert report.return_confidence_interval is None


def test_validated_multi_horizon_event_study_reports_preserve_order_and_settings():
    labels = add_forward_returns([100, 110, 99, 120, 126], [1, 2])

    reports = summarize_validated_multi_horizon_event_study(
        labels,
        [0, 1, 2],
        [2, 1],
        bootstrap_samples=100,
        bootstrap_confidence=0.9,
        bootstrap_seed=17,
        minimum_events=5,
    )
    duplicate = summarize_validated_multi_horizon_event_study(
        labels,
        [0, 1, 2],
        [2, 1],
        bootstrap_samples=100,
        bootstrap_confidence=0.9,
        bootstrap_seed=17,
        minimum_events=5,
    )

    assert list(reports.keys()) == [2, 1]
    assert reports == duplicate
    assert all(isinstance(report, ValidatedEventStudyReport) for report in reports.values())
    assert [report.summary.horizon for report in reports.values()] == [2, 1]
    assert {report.bootstrap_samples for report in reports.values()} == {100}
    assert {report.bootstrap_confidence for report in reports.values()} == {0.9}
    assert {report.bootstrap_seed for report in reports.values()} == {17}
    assert reports[2].summary.events == 3
    assert reports[1].low_sample_warning == (
        "Low sample size: 3 observations; treat results as exploratory until at least 5 are available."
    )


def test_validated_multi_horizon_event_study_deduplicates_horizons():
    labels = add_forward_returns([100, 110, 121, 90], [1, 2])

    reports = summarize_validated_multi_horizon_event_study(labels, [0, 1], [1, 2, 1], bootstrap_samples=10)

    assert list(reports.keys()) == [1, 2]
    assert reports[1].summary.events == 2
    assert reports[2].summary.events == 2


def test_validated_multi_horizon_event_study_keeps_missing_return_interval_behavior():
    labels = add_forward_returns([100, 110], [1, 2])

    reports = summarize_validated_multi_horizon_event_study(labels, [1], [1, 2], bootstrap_samples=10, minimum_events=1)

    assert reports[1].summary.events == 0
    assert reports[1].return_confidence_interval is None
    assert reports[2].summary.events == 0
    assert reports[2].return_confidence_interval is None


def test_validated_event_study_report_serializes_summary_and_metadata():
    labels = add_forward_returns([100, 110, 121], [1])

    report = summarize_validated_event_study(labels, [0, 1], 1, bootstrap_samples=20, bootstrap_seed=3)
    data = report.to_dict()

    assert data["summary"]["events"] == 2
    assert data["bootstrap_samples"] == 20
    assert data["bootstrap_seed"] == 3
    assert isinstance(data["return_confidence_interval"], list)


def test_validated_event_study_report_row_flattens_summary_and_metadata():
    labels = add_forward_returns([100, 110, 99, 120, 126], [1])

    report = summarize_validated_event_study(
        labels,
        [0, 1, 2],
        1,
        bootstrap_samples=100,
        bootstrap_confidence=0.95,
        bootstrap_seed=17,
        minimum_events=5,
    )
    row = validated_event_study_report_row(report)

    assert row == {
        "events": 3,
        "horizon": 1,
        "baseline_bullish_probability": 3 / 4,
        "conditional_bullish_probability": 2 / 3,
        "average_return": pytest.approx(0.07070707070707076),
        "median_return": pytest.approx(0.1),
        "low_sample_warning": (
            "Low sample size: 3 observations; treat results as exploratory until at least 5 are available."
        ),
        "bootstrap_samples": 100,
        "bootstrap_confidence": 0.95,
        "bootstrap_seed": 17,
        "return_confidence_interval_lower": pytest.approx(-0.1),
        "return_confidence_interval_upper": pytest.approx(0.1747474747474748),
    }


def test_validated_event_study_report_row_uses_none_for_missing_interval_bounds():
    labels = add_forward_returns([100, 110], [1])

    report = summarize_validated_event_study(labels, [1], 1, bootstrap_samples=10, minimum_events=1)
    row = validated_event_study_report_row(report)

    assert row["return_confidence_interval_lower"] is None
    assert row["return_confidence_interval_upper"] is None
    assert row["average_return"] is None


def test_validated_multi_horizon_event_study_report_rows_flatten_mapping_in_order():
    labels = add_forward_returns([100, 110, 99, 120, 126], [1, 2])
    reports = summarize_validated_multi_horizon_event_study(
        labels,
        [0, 1, 2],
        [2, 1],
        bootstrap_samples=50,
        bootstrap_seed=7,
        minimum_events=5,
    )

    rows = validated_multi_horizon_event_study_report_rows(reports)

    assert [row["horizon"] for row in rows] == [2, 1]
    assert rows[0]["events"] == 3
    assert rows[0]["bootstrap_seed"] == 7
    assert rows[1]["low_sample_warning"] == (
        "Low sample size: 3 observations; treat results as exploratory until at least 5 are available."
    )


def test_validated_multi_horizon_event_study_report_rows_flatten_sequence_in_order():
    labels = add_forward_returns([100, 110, 99], [1, 2])
    reports = summarize_validated_multi_horizon_event_study(
        labels,
        [1],
        [1, 2],
        bootstrap_samples=10,
        minimum_events=1,
    )

    rows = validated_multi_horizon_event_study_report_rows([reports[2], reports[1]])

    assert [row["horizon"] for row in rows] == [2, 1]
    assert rows[0]["return_confidence_interval_lower"] is None
    assert rows[0]["return_confidence_interval_upper"] is None


def test_validated_multi_horizon_event_study_report_group_rows_preserve_mapping_order():
    labels = add_forward_returns([100, 110, 99, 120, 126], [2, 1])
    train_reports = summarize_validated_multi_horizon_event_study(
        labels,
        [0, 1, 2],
        [2, 1],
        bootstrap_samples=20,
        bootstrap_seed=3,
        minimum_events=5,
    )
    test_reports = summarize_validated_multi_horizon_event_study(
        labels,
        [1],
        [1],
        bootstrap_samples=20,
        bootstrap_seed=5,
        minimum_events=1,
    )

    rows = validated_multi_horizon_event_study_report_group_rows({
        "train": train_reports,
        "test": test_reports,
    })

    assert [row["report_group_id"] for row in rows] == ["train", "train", "test"]
    assert [row["horizon"] for row in rows] == [2, 1, 1]
    assert rows[0] == {
        "report_group_id": "train",
        **validated_event_study_report_row(train_reports[2]),
    }
    assert rows[1] == {
        "report_group_id": "train",
        **validated_event_study_report_row(train_reports[1]),
    }
    assert rows[2] == {
        "report_group_id": "test",
        **validated_event_study_report_row(test_reports[1]),
    }


def test_validated_multi_horizon_event_study_report_group_rows_preserve_pair_order_and_skip_empty_groups():
    labels = add_forward_returns([100, 110, 99], [1, 2])
    reports = summarize_validated_multi_horizon_event_study(
        labels,
        [1],
        [1, 2],
        bootstrap_samples=10,
        minimum_events=1,
    )

    rows = validated_multi_horizon_event_study_report_group_rows([
        ("empty", []),
        ("test", [reports[2], reports[1]]),
    ])

    assert [row["report_group_id"] for row in rows] == ["test", "test"]
    assert [row["horizon"] for row in rows] == [2, 1]


def test_validated_multi_horizon_event_study_report_group_rows_reject_duplicate_group_ids():
    labels = add_forward_returns([100, 110, 99], [1])
    reports = summarize_validated_multi_horizon_event_study(
        labels,
        [0],
        [1],
        bootstrap_samples=10,
        minimum_events=1,
    )

    with pytest.raises(ValueError, match="report group IDs must be unique"):
        validated_multi_horizon_event_study_report_group_rows([
            ("train", reports),
            ("train", reports),
        ])


def test_validated_multi_horizon_event_study_report_group_rows_reject_blank_group_ids():
    with pytest.raises(ValueError, match="report group ID must not be blank"):
        validated_multi_horizon_event_study_report_group_rows([("   ", [])])


def test_validated_multi_horizon_event_study_report_group_rows_reject_non_string_group_ids():
    with pytest.raises(ValueError, match="report group ID must be a string"):
        validated_multi_horizon_event_study_report_group_rows({123: []})  # type: ignore[dict-item]

    with pytest.raises(ValueError, match="report group ID must be a string"):
        validated_multi_horizon_event_study_report_group_rows([(123, [])])  # type: ignore[list-item]


def test_event_study_baseline_comparison_row_calculates_delta_and_lift():
    result = summarize_event_study(add_forward_returns([100, 110, 99, 120], [1]), [0, 1], 1)

    row = event_study_baseline_comparison_row(result)

    assert row == {
        "events": 2,
        "horizon": 1,
        "baseline_bullish_probability": 2 / 3,
        "conditional_bullish_probability": 1 / 2,
        "probability_delta": pytest.approx(-1 / 6),
        "relative_lift": pytest.approx(-0.25),
    }


def test_event_study_baseline_comparison_row_uses_none_for_missing_probabilities():
    result = summarize_event_study(add_forward_returns([100], [1]), [0], 1)

    row = event_study_baseline_comparison_row(result)

    assert row["baseline_bullish_probability"] is None
    assert row["conditional_bullish_probability"] is None
    assert row["probability_delta"] is None
    assert row["relative_lift"] is None


def test_event_study_baseline_comparison_row_uses_none_for_zero_baseline_lift():
    result = summarize_event_study(add_forward_returns([100, 90, 80], [1]), [0], 1)

    row = event_study_baseline_comparison_row(result)

    assert row["baseline_bullish_probability"] == 0
    assert row["conditional_bullish_probability"] == 0
    assert row["probability_delta"] == 0
    assert row["relative_lift"] is None


def test_multi_horizon_baseline_comparison_rows_preserve_mapping_order():
    labels = add_forward_returns([100, 110, 99, 120], [2, 1])
    results = summarize_multi_horizon_event_study(labels, [0, 1], [2, 1])

    rows = multi_horizon_baseline_comparison_rows(results)

    assert [row["horizon"] for row in rows] == [2, 1]
    assert rows[0] == event_study_baseline_comparison_row(results[2])
    assert rows[1] == event_study_baseline_comparison_row(results[1])


def test_multi_horizon_baseline_comparison_rows_flatten_sequence_in_order():
    labels = add_forward_returns([100, 110, 99, 120], [1, 2])
    results = summarize_multi_horizon_event_study(labels, [0, 1], [1, 2])

    rows = multi_horizon_baseline_comparison_rows([results[2], results[1]])

    assert [row["horizon"] for row in rows] == [2, 1]


def test_multi_horizon_baseline_comparison_rows_accept_empty_input():
    assert multi_horizon_baseline_comparison_rows({}) == []
    assert multi_horizon_baseline_comparison_rows([]) == []


def test_multi_horizon_baseline_comparison_group_rows_preserve_mapping_order():
    labels = add_forward_returns([100, 110, 99, 120], [2, 1])
    train_results = summarize_multi_horizon_event_study(labels, [0, 1], [2, 1])
    test_results = summarize_multi_horizon_event_study(labels, [1], [1])

    rows = multi_horizon_baseline_comparison_group_rows({
        "train": train_results,
        "test": test_results,
    })

    assert [row["comparison_group_id"] for row in rows] == ["train", "train", "test"]
    assert [row["horizon"] for row in rows] == [2, 1, 1]
    assert rows[0] == {"comparison_group_id": "train", **event_study_baseline_comparison_row(train_results[2])}
    assert rows[1] == {"comparison_group_id": "train", **event_study_baseline_comparison_row(train_results[1])}
    assert rows[2] == {"comparison_group_id": "test", **event_study_baseline_comparison_row(test_results[1])}


def test_multi_horizon_baseline_comparison_group_rows_preserve_pair_order_and_skip_empty_groups():
    labels = add_forward_returns([100, 110, 99, 120], [1, 2])
    results = summarize_multi_horizon_event_study(labels, [0, 1], [1, 2])

    rows = multi_horizon_baseline_comparison_group_rows([
        ("empty", []),
        ("test", [results[2], results[1]]),
    ])

    assert [row["comparison_group_id"] for row in rows] == ["test", "test"]
    assert [row["horizon"] for row in rows] == [2, 1]


def test_multi_horizon_baseline_comparison_group_rows_reject_duplicate_group_ids():
    labels = add_forward_returns([100, 110, 99, 120], [1])
    results = summarize_multi_horizon_event_study(labels, [0, 1], [1])

    with pytest.raises(ValueError, match="comparison group IDs must be unique"):
        multi_horizon_baseline_comparison_group_rows([
            ("train", results),
            ("train", results),
        ])


def test_multi_horizon_baseline_comparison_group_rows_reject_blank_group_ids():
    with pytest.raises(ValueError, match="comparison group ID must not be blank"):
        multi_horizon_baseline_comparison_group_rows([("   ", [])])


def test_multi_horizon_baseline_comparison_group_rows_reject_non_string_group_ids():
    with pytest.raises(ValueError, match="comparison group ID must be a string"):
        multi_horizon_baseline_comparison_group_rows({123: []})  # type: ignore[dict-item]

    with pytest.raises(ValueError, match="comparison group ID must be a string"):
        multi_horizon_baseline_comparison_group_rows([(123, [])])  # type: ignore[list-item]


def test_join_aspect_events_to_market_labels_orders_matches_by_event_timestamp():
    ts1 = datetime(2026, 5, 6, tzinfo=timezone.utc)
    ts2 = datetime(2026, 5, 7, tzinfo=timezone.utc)
    labels = [
        {"timestamp": ts2, "return_1d": -0.05, "bullish_1d": False},
        {"timestamp": ts1, "return_1d": 0.1, "bullish_1d": True},
    ]
    events = [
        _aspect_event("sun", "mars", ts2),
        _aspect_event("sun", "jupiter", ts1),
    ]

    joined = join_aspect_events_to_market_labels(events, labels)

    assert joined.event_indexes == [1, 0]
    assert [(record.event_index, record.label_index) for record in joined.joined] == [(1, 1), (0, 0)]
    assert joined.matched_events == 2
    assert joined.unmatched_events == 0


def test_timestamp_join_summary_row_reports_all_matched_join_counts_and_bounds():
    ts1 = datetime(2026, 5, 6, tzinfo=timezone.utc)
    ts2 = datetime(2026, 5, 7, tzinfo=timezone.utc)
    joined = join_aspect_events_to_market_labels(
        [_aspect_event("sun", "mars", ts2), _aspect_event("sun", "jupiter", ts1)],
        [
            {"timestamp": ts2, "return_1d": -0.05, "bullish_1d": False},
            {"timestamp": ts1, "return_1d": 0.1, "bullish_1d": True},
        ],
    )

    row = timestamp_join_summary_row(joined)

    assert row == {
        "matched_event_count": 2,
        "unmatched_event_count": 0,
        "matched_label_index_count": 2,
        "first_matched_event_index": 1,
        "last_matched_event_index": 0,
        "first_unmatched_event_index": None,
        "last_unmatched_event_index": None,
    }


def test_join_aspect_events_to_market_labels_reports_unmatched_events():
    ts1 = datetime(2026, 5, 6, tzinfo=timezone.utc)
    ts2 = datetime(2026, 5, 7, tzinfo=timezone.utc)

    joined = join_aspect_events_to_market_labels(
        [_aspect_event("sun", "jupiter", ts1), _aspect_event("sun", "mars", ts2)],
        [{"timestamp": ts1, "return_1d": 0.1, "bullish_1d": True}],
    )

    assert joined.event_indexes == [0]
    assert joined.unmatched_event_indexes == [1]
    assert joined.unmatched_events == 1


def test_timestamp_join_summary_row_reports_partially_unmatched_join_bounds():
    ts1 = datetime(2026, 5, 6, tzinfo=timezone.utc)
    ts2 = datetime(2026, 5, 7, tzinfo=timezone.utc)
    ts3 = datetime(2026, 5, 8, tzinfo=timezone.utc)
    joined = join_aspect_events_to_market_labels(
        [
            _aspect_event("sun", "jupiter", ts1),
            _aspect_event("sun", "mars", ts2),
            _aspect_event("moon", "jupiter", ts3),
        ],
        [{"timestamp": ts2, "return_1d": 0.1, "bullish_1d": True}],
    )

    row = timestamp_join_summary_row(joined)

    assert row["matched_event_count"] == 1
    assert row["unmatched_event_count"] == 2
    assert row["matched_label_index_count"] == 1
    assert row["first_matched_event_index"] == 1
    assert row["last_matched_event_index"] == 1
    assert row["first_unmatched_event_index"] == 0
    assert row["last_unmatched_event_index"] == 2


def test_timestamp_join_summary_row_handles_empty_matched_and_unmatched_edges():
    ts = datetime(2026, 5, 6, tzinfo=timezone.utc)
    no_matches = join_aspect_events_to_market_labels(
        [_aspect_event("sun", "jupiter", ts)],
        [],
    )
    empty = join_aspect_events_to_market_labels([], [])

    assert timestamp_join_summary_row(no_matches) == {
        "matched_event_count": 0,
        "unmatched_event_count": 1,
        "matched_label_index_count": 0,
        "first_matched_event_index": None,
        "last_matched_event_index": None,
        "first_unmatched_event_index": 0,
        "last_unmatched_event_index": 0,
    }
    assert timestamp_join_summary_row(empty) == {
        "matched_event_count": 0,
        "unmatched_event_count": 0,
        "matched_label_index_count": 0,
        "first_matched_event_index": None,
        "last_matched_event_index": None,
        "first_unmatched_event_index": None,
        "last_unmatched_event_index": None,
    }


def test_timestamp_join_summary_rows_preserves_ordered_mapping_input():
    ts1 = datetime(2026, 5, 6, tzinfo=timezone.utc)
    ts2 = datetime(2026, 5, 7, tzinfo=timezone.utc)
    train_join = join_aspect_events_to_market_labels(
        [_aspect_event("sun", "jupiter", ts1), _aspect_event("moon", "mars", ts2)],
        [{"timestamp": ts1, "return_1d": 0.1, "bullish_1d": True}],
    )
    test_join = join_aspect_events_to_market_labels(
        [_aspect_event("sun", "mars", ts2)],
        [{"timestamp": ts2, "return_1d": -0.05, "bullish_1d": False}],
    )

    rows = timestamp_join_summary_rows({"train": train_join, "test": test_join})

    assert [row["join_id"] for row in rows] == ["train", "test"]
    assert rows[0] == {
        "join_id": "train",
        "matched_event_count": 1,
        "unmatched_event_count": 1,
        "matched_label_index_count": 1,
        "first_matched_event_index": 0,
        "last_matched_event_index": 0,
        "first_unmatched_event_index": 1,
        "last_unmatched_event_index": 1,
    }
    assert rows[1]["matched_event_count"] == 1


def test_timestamp_join_summary_rows_accepts_pair_input_and_empty_results():
    ts = datetime(2026, 5, 6, tzinfo=timezone.utc)
    no_matches = join_aspect_events_to_market_labels([_aspect_event("sun", "jupiter", ts)], [])
    empty = join_aspect_events_to_market_labels([], [])

    rows = timestamp_join_summary_rows([("no-matches", no_matches), ("empty", empty)])

    assert rows[0] == {
        "join_id": "no-matches",
        "matched_event_count": 0,
        "unmatched_event_count": 1,
        "matched_label_index_count": 0,
        "first_matched_event_index": None,
        "last_matched_event_index": None,
        "first_unmatched_event_index": 0,
        "last_unmatched_event_index": 0,
    }
    assert rows[1] == {
        "join_id": "empty",
        "matched_event_count": 0,
        "unmatched_event_count": 0,
        "matched_label_index_count": 0,
        "first_matched_event_index": None,
        "last_matched_event_index": None,
        "first_unmatched_event_index": None,
        "last_unmatched_event_index": None,
    }


def test_timestamp_join_summary_rows_rejects_duplicate_and_blank_join_ids():
    empty = join_aspect_events_to_market_labels([], [])

    with pytest.raises(ValueError, match="join IDs must be unique"):
        timestamp_join_summary_rows([("same", empty), ("same", empty)])

    with pytest.raises(ValueError, match="join ID must not be blank"):
        timestamp_join_summary_rows([(" ", empty)])


def test_timestamp_join_summary_rows_rejects_non_string_join_ids():
    empty = join_aspect_events_to_market_labels([], [])

    with pytest.raises(ValueError, match="join ID must be a string"):
        timestamp_join_summary_rows({123: empty})  # type: ignore[dict-item]

    with pytest.raises(ValueError, match="join ID must be a string"):
        timestamp_join_summary_rows([(123, empty)])  # type: ignore[list-item]


def test_join_aspect_events_to_market_labels_rejects_duplicate_label_timestamps():
    ts = datetime(2026, 5, 6, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="duplicate market label timestamp"):
        join_aspect_events_to_market_labels(
            [_aspect_event("sun", "jupiter", ts)],
            [
                {"timestamp": ts, "return_1d": 0.1, "bullish_1d": True},
                {"timestamp": ts, "return_1d": -0.1, "bullish_1d": False},
            ],
        )


def test_join_aspect_events_to_market_labels_rejects_events_without_timestamps():
    with pytest.raises(ValueError, match="missing a timestamp"):
        join_aspect_events_to_market_labels(
            [_aspect_event("sun", "jupiter", None)],
            [],
        )


def test_join_aspect_events_to_market_labels_supports_market_label_models_for_event_study():
    ts1 = datetime(2026, 5, 6, tzinfo=timezone.utc)
    ts2 = datetime(2026, 5, 7, tzinfo=timezone.utc)
    labels = [
        MarketLabel(ts1, "BTC-USD", 1, 0.1, True),
        MarketLabel(ts2, "BTC-USD", 1, -0.05, False),
    ]

    joined = join_aspect_events_to_market_labels([_aspect_event("sun", "jupiter", ts1)], labels)
    result = summarize_event_study(joined.labels, joined.event_indexes, 1)

    assert result.events == 1
    assert result.baseline_bullish_probability == 1 / 2
    assert result.conditional_bullish_probability == 1.0


def _aspect_event(body_a: str, body_b: str, timestamp: datetime | None) -> AspectEvent:
    return AspectEvent(
        body_a=body_a,
        body_b=body_b,
        aspect="conjunction",
        target_angle=0,
        actual_angle=1,
        orb=1,
        max_orb=3,
        strength=2 / 3,
        timestamp=timestamp,
    )
