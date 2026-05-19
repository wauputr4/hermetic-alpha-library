from datetime import datetime, timezone

import pytest

from hermetic_alpha.analysis import (
    bootstrap_interval_row,
    bootstrap_percentile_interval,
    event_study_baseline_comparison_row,
    permutation_test,
    permutation_test_result_row,
    random_baseline_distribution,
    random_baseline_distribution_row,
    summarize_event_study,
    summarize_validated_event_study,
    summarize_validated_multi_horizon_event_study,
    validated_event_study_report_row,
    validated_multi_horizon_event_study_report_rows,
    walk_forward_split_rows,
    walk_forward_splits,
)
from hermetic_alpha.exports import to_csv, to_json, write_csv, write_json
from hermetic_alpha.labels import add_forward_returns
from hermetic_alpha.models import EventStudyResult, MarketCandle
from hermetic_alpha.similarity import (
    SimilarityCandidate,
    find_nearest,
    nearest_neighbor_rows,
)


def test_json_exports_model_objects_and_mappings(tmp_path):
    result = EventStudyResult(
        events=2,
        horizon=7,
        baseline_bullish_probability=0.5,
        conditional_bullish_probability=0.75,
        average_return=0.04,
        median_return=0.03,
    )

    text = to_json({"result": result, "source": "unit"})
    assert '"average_return": 0.04' in text
    assert text.index('"result"') < text.index('"source"')

    path = tmp_path / "result.json"
    write_json(result, path)
    assert path.read_text(encoding="utf-8").endswith("\n")
    assert '"events": 2' in path.read_text(encoding="utf-8")


def test_json_exports_native_dates():
    ts = datetime(2026, 5, 17, 1, 2, tzinfo=timezone.utc)

    text = to_json({"timestamp": ts, "date": ts.date()})

    assert '"timestamp": "2026-05-17T01:02:00+00:00"' in text
    assert '"date": "2026-05-17"' in text


def test_csv_exports_model_rows_with_stable_header(tmp_path):
    ts = datetime(2026, 5, 6, tzinfo=timezone.utc)
    rows = [
        MarketCandle(ts, "BTC-USD", 1.0, 2.0, 0.5, 1.5, volume=10.0),
        {"timestamp": ts.isoformat(), "asset": "ETH-USD", "close": 3.0, "extra": "ok"},
    ]

    text = to_csv(rows)
    assert text.splitlines()[0] == "timestamp,asset,open,high,low,close,volume,interval,source,extra"
    assert "BTC-USD" in text
    assert "ETH-USD" in text

    path = tmp_path / "rows.csv"
    write_csv(rows, path)
    assert path.read_text(encoding="utf-8") == text


def test_csv_exports_native_dates():
    ts = datetime(2026, 5, 17, 1, 2, tzinfo=timezone.utc)

    text = to_csv([{"timestamp": ts, "date": ts.date(), "asset": "BTC-USD"}])

    assert "2026-05-17T01:02:00+00:00,2026-05-17,BTC-USD\n" in text


def test_csv_empty_inputs_and_explicit_header():
    assert to_csv([]) == "\r\n" or to_csv([]) == "\n"
    assert to_csv([], fieldnames=["asset", "close"]) == "asset,close\n"


def test_csv_rejects_nested_values():
    with pytest.raises(TypeError, match="unsupported nested value"):
        to_csv([{"asset": "BTC-USD", "nested": {"close": 1.0}}])


def test_csv_rejects_extra_fields_with_explicit_header():
    with pytest.raises(ValueError, match="outside the configured header: extra"):
        to_csv([{"asset": "BTC-USD", "close": 1.0, "extra": "nope"}], fieldnames=["asset", "close"])


def test_csv_accepts_flat_validated_event_study_report_rows():
    labels = add_forward_returns([100, 110, 99, 120], [1])
    report = summarize_validated_event_study(labels, [0, 1], 1, bootstrap_samples=20, bootstrap_seed=3)

    text = to_csv([validated_event_study_report_row(report)])

    header = text.splitlines()[0]
    assert "events,horizon,baseline_bullish_probability" in header
    assert "return_confidence_interval_lower,return_confidence_interval_upper" in header
    assert "Low sample size: 2 observations" in text


def test_csv_accepts_flat_validated_multi_horizon_event_study_report_rows():
    labels = add_forward_returns([100, 110, 99, 120], [1, 2])
    reports = summarize_validated_multi_horizon_event_study(
        labels,
        [0, 1],
        [2, 1],
        bootstrap_samples=20,
        bootstrap_seed=3,
    )

    text = to_csv(validated_multi_horizon_event_study_report_rows(reports))

    assert text.splitlines()[0] == (
        "events,horizon,baseline_bullish_probability,conditional_bullish_probability,"
        "average_return,median_return,low_sample_warning,bootstrap_samples,"
        "bootstrap_confidence,bootstrap_seed,return_confidence_interval_lower,"
        "return_confidence_interval_upper"
    )
    assert "\n2,2," in text
    assert "\n2,1," in text


def test_csv_accepts_flat_baseline_comparison_rows():
    labels = add_forward_returns([100, 110, 99, 120], [1])
    result = summarize_event_study(labels, [0, 1], 1)

    text = to_csv([event_study_baseline_comparison_row(result)])

    assert text.splitlines()[0] == (
        "events,horizon,baseline_bullish_probability,conditional_bullish_probability,"
        "probability_delta,relative_lift"
    )


def test_csv_accepts_flat_permutation_test_result_rows():
    result = permutation_test(
        [1.0, 1.0, 0.0],
        [0.0, 0.0, 0.0],
        permutations=20,
        seed=19,
        alternative="greater",
    )

    text = to_csv([permutation_test_result_row(result)])

    assert text.splitlines()[0] == (
        "observed_statistic,p_value,alternative,permutations,seed,null_mean,"
        "null_distribution_count,null_distribution_min,null_distribution_max"
    )
    assert "greater,20,19" in text


def test_csv_accepts_flat_random_baseline_distribution_rows():
    distribution = random_baseline_distribution(
        [1.0, 2.0, 3.0, 4.0],
        2,
        samples=5,
        seed=11,
    )

    text = to_csv([
        random_baseline_distribution_row(
            distribution,
            sample_size=2,
            samples=5,
            seed=11,
        )
    ])

    assert text.splitlines()[0] == (
        "distribution_count,distribution_min,distribution_max,distribution_mean,"
        "sample_size,samples,seed"
    )
    assert "\n5,1.5,3.5,2.6,2,5,11" in text


def test_csv_accepts_flat_bootstrap_interval_rows():
    interval = bootstrap_percentile_interval([0.01, 0.02, 0.05, -0.01], samples=200, seed=7)

    text = to_csv([
        bootstrap_interval_row(
            interval,
            samples=200,
            confidence=0.95,
            seed=7,
            statistic_name="mean_return",
        )
    ])

    assert text.splitlines()[0] == "interval_lower,interval_upper,samples,confidence,seed,statistic_name"
    assert "\n-0.0025,0.035,200,0.95,7,mean_return" in text


def test_csv_accepts_flat_walk_forward_split_rows():
    splits = walk_forward_splits(6, train_size=3, test_size=1)

    text = to_csv(walk_forward_split_rows(splits))

    assert text.splitlines()[0] == (
        "split_index,train_start_index,train_end_index,test_start_index,test_end_index,"
        "train_size,test_size,train_first,train_last,test_first,test_last"
    )
    assert "\n0,0,3,3,4,3,1,0,2,3,3" in text
    assert "\n2,2,5,5,6,3,1,2,4,5,5" in text


def test_csv_accepts_walk_forward_rows_with_nested_endpoints_removed():
    splits = walk_forward_splits(
        [{"close": 100.0}, {"close": 101.0}, {"close": 102.0}],
        train_size=1,
        test_size=1,
    )

    text = to_csv(walk_forward_split_rows(splits))

    assert "train_first,train_last,test_first,test_last" in text
    assert "\n0,0,1,1,2,1,1,,,," in text


def test_csv_accepts_flat_nearest_neighbor_rows():
    results = find_nearest(
        [1.0, 0.0],
        [
            SimilarityCandidate("distant-chart", [0.0, 1.0], payload={"asset": "ETH-USD"}),
            SimilarityCandidate("near-chart", [1.0, 0.0], payload={"asset": "BTC-USD"}),
        ],
    )

    text = to_csv(nearest_neighbor_rows(results, payload_fields=["asset"]))

    assert text.splitlines()[0] == "rank,id,score,distance,payload_asset"
    assert "\n1,near-chart,1.0,0.0,BTC-USD" in text
    assert "\n2,distant-chart,0.0,1.0,ETH-USD" in text
