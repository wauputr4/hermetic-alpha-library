import pytest
from datetime import datetime, timezone

from hermetic_alpha.analysis import (
    ValidatedEventStudyReport,
    event_study_baseline_comparison_row,
    join_aspect_events_to_market_labels,
    summarize_event_study,
    summarize_multi_horizon_event_study,
    summarize_validated_event_study,
    summarize_validated_multi_horizon_event_study,
    timestamp_join_summary_row,
    validated_event_study_report_row,
    validated_multi_horizon_event_study_report_rows,
)
from hermetic_alpha.labels import (
    add_candle_forward_returns,
    add_candle_local_extrema_labels,
    add_forward_returns,
    add_local_extrema_labels,
    bullish_probability,
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
