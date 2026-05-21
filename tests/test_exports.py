from datetime import datetime, timezone

import pytest

from hermetic_alpha.analysis import (
    PermutationTestResult,
    bootstrap_interval_row,
    bootstrap_interval_rows,
    bootstrap_percentile_interval,
    event_study_baseline_comparison_row,
    multi_horizon_baseline_comparison_rows,
    permutation_test,
    permutation_test_result_row,
    permutation_test_result_rows,
    random_baseline_distribution,
    random_baseline_distribution_row,
    random_baseline_distribution_rows,
    join_aspect_events_to_market_labels,
    summarize_event_study,
    summarize_multi_horizon_event_study,
    summarize_validated_event_study,
    summarize_validated_multi_horizon_event_study,
    timestamp_join_summary_row,
    validated_event_study_report_row,
    validated_multi_horizon_event_study_report_rows,
    walk_forward_split_rows,
    walk_forward_splits,
)
from hermetic_alpha.astro import (
    aspect_scan_summary_row,
    aspect_scan_summary_rows,
    planet_position_series_summary_row,
    planet_position_series_summary_rows,
)
from hermetic_alpha.exports import to_csv, to_json, write_csv, write_json
from hermetic_alpha.features import aspect_event_feature_matrix_summary_row
from hermetic_alpha.labels import (
    add_forward_returns,
    add_local_extrema_labels,
    forward_return_label_coverage_row,
    local_extrema_label_coverage_row,
    multi_horizon_forward_return_label_coverage_rows,
    multi_window_local_extrema_label_coverage_rows,
)
from hermetic_alpha.market import candle_dataset_summary_row, candle_dataset_summary_rows
from hermetic_alpha.models import AspectEvent, EventStudyResult, MarketCandle, PlanetPosition
from hermetic_alpha.similarity import (
    SimilarityCandidate,
    find_nearest,
    nearest_neighbor_rows,
    nearest_neighbor_summary_row,
    planet_position_encoding_rows,
    planet_position_vector_summary_row,
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


def test_csv_accepts_forward_return_label_coverage_rows():
    labels = add_forward_returns([100, 110, 99], [1])

    text = to_csv([forward_return_label_coverage_row(labels, 1, dataset_id="close-list")])

    assert text.splitlines()[0] == (
        "dataset_id,horizon,row_count,labeled_return_count,bullish_count,"
        "bearish_count,missing_label_count,asset,first_timestamp,last_timestamp"
    )
    assert "close-list,1,3,2,1,1,1,,,\n" in text


def test_csv_accepts_multi_horizon_forward_return_label_coverage_rows():
    labels = add_forward_returns([100, 110, 99, 120], [1, 2])

    text = to_csv(multi_horizon_forward_return_label_coverage_rows(labels, [2, 1], dataset_id="close-list"))

    assert text.splitlines()[0] == (
        "dataset_id,horizon,row_count,labeled_return_count,bullish_count,"
        "bearish_count,missing_label_count,asset,first_timestamp,last_timestamp"
    )
    assert "\nclose-list,2,4,2,1,1,2,,," in text
    assert "\nclose-list,1,4,3,2,1,1,,," in text


def test_csv_accepts_local_extrema_label_coverage_rows():
    labels = add_local_extrema_labels([100, 90, 110, 105], 1)

    text = to_csv([local_extrema_label_coverage_row(labels, 1, dataset_id="extrema")])

    assert text.splitlines()[0] == (
        "dataset_id,window,row_count,labeled_count,missing_label_count,"
        "local_top_count,local_bottom_count,asset,first_timestamp,last_timestamp"
    )
    assert "extrema,1,4,2,2,1,1,,,\n" in text


def test_csv_accepts_multi_window_local_extrema_label_coverage_rows():
    labels = add_local_extrema_labels([100, 90, 110, 105, 80], [1, 2])

    text = to_csv(multi_window_local_extrema_label_coverage_rows(labels, [2, 1], dataset_id="extrema"))

    assert text.splitlines()[0] == (
        "dataset_id,window,row_count,labeled_count,missing_label_count,"
        "local_top_count,local_bottom_count,asset,first_timestamp,last_timestamp"
    )
    assert "\nextrema,2,5,1,4,1,0,,," in text
    assert "\nextrema,1,5,3,2,1,1,,," in text


def test_csv_accepts_flat_baseline_comparison_rows():
    labels = add_forward_returns([100, 110, 99, 120], [1])
    result = summarize_event_study(labels, [0, 1], 1)

    text = to_csv([event_study_baseline_comparison_row(result)])

    assert text.splitlines()[0] == (
        "events,horizon,baseline_bullish_probability,conditional_bullish_probability,"
        "probability_delta,relative_lift"
    )


def test_csv_accepts_flat_aspect_feature_matrix_summary_rows():
    ts = datetime(2026, 5, 18, tzinfo=timezone.utc)
    events = [
        AspectEvent(
            body_a="sun",
            body_b="jupiter",
            aspect="conjunction",
            target_angle=0.0,
            actual_angle=1.25,
            orb=1.25,
            max_orb=3.0,
            strength=0.5,
            timestamp=ts,
        )
    ]

    text = to_csv(
        [
            aspect_event_feature_matrix_summary_row(
                events,
                ["sun_jupiter_conjunction"],
                matrix_id="btc-train",
            )
        ]
    )

    assert text.splitlines()[0] == (
        "matrix_id,row_count,timestamp_count,observed_feature_count,configured_feature_count,"
        "duplicate_configured_feature_count,missing_timestamp_count,event_count,"
        "first_timestamp,last_timestamp"
    )
    assert "btc-train,1,1,1,1,0,0,1,2026-05-18T00:00:00+00:00" in text


def test_csv_accepts_flat_aspect_scan_summary_rows():
    ts = datetime(2026, 5, 18, tzinfo=timezone.utc)
    events = [
        AspectEvent(
            body_a="sun",
            body_b="jupiter",
            aspect="conjunction",
            target_angle=0.0,
            actual_angle=1.25,
            orb=1.25,
            max_orb=3.0,
            strength=0.5,
            timestamp=ts,
        )
    ]

    text = to_csv([aspect_scan_summary_row(events)])

    assert text.splitlines()[0] == (
        "event_count,timestamp_count,unique_aspect_count,unique_body_pair_count,"
        "applying_phase_count,separating_phase_count,exact_phase_count,unknown_phase_count,"
        "missing_timestamp_count,first_timestamp,last_timestamp"
    )
    assert "\n1,1,1,1,0,0,0,1,0,2026-05-18T00:00:00+00:00" in text


def test_csv_accepts_flat_multi_aspect_scan_summary_rows():
    ts = datetime(2026, 5, 18, tzinfo=timezone.utc)
    events = [
        AspectEvent(
            body_a="sun",
            body_b="jupiter",
            aspect="conjunction",
            target_angle=0.0,
            actual_angle=1.25,
            orb=1.25,
            max_orb=3.0,
            strength=0.5,
            timestamp=ts,
        )
    ]

    text = to_csv(aspect_scan_summary_rows([("btc-daily", events), ("empty", [])]))

    assert text.splitlines()[0] == (
        "scan_id,event_count,timestamp_count,unique_aspect_count,unique_body_pair_count,"
        "applying_phase_count,separating_phase_count,exact_phase_count,unknown_phase_count,"
        "missing_timestamp_count,first_timestamp,last_timestamp"
    )
    assert "\nbtc-daily,1,1,1,1,0,0,0,1,0,2026-05-18T00:00:00+00:00" in text
    assert "\nempty,0,0,0,0,0,0,0,0,0,," in text


def test_csv_accepts_flat_multi_horizon_baseline_comparison_rows():
    labels = add_forward_returns([100, 110, 99, 120], [2, 1])
    results = summarize_multi_horizon_event_study(labels, [0, 1], [2, 1])

    text = to_csv(multi_horizon_baseline_comparison_rows(results))

    assert text.splitlines()[0] == (
        "events,horizon,baseline_bullish_probability,conditional_bullish_probability,"
        "probability_delta,relative_lift"
    )
    assert "\n2,2," in text
    assert "\n2,1," in text


def test_csv_accepts_flat_timestamp_join_summary_rows():
    ts = datetime(2026, 5, 17, tzinfo=timezone.utc)
    joined = join_aspect_events_to_market_labels(
        [
            AspectEvent("sun", "jupiter", "conjunction", 0, 1, 1, 3, 2 / 3, timestamp=ts),
            AspectEvent("sun", "mars", "square", 90, 93, 3, 5, 0.4, timestamp=ts.replace(day=18)),
        ],
        [{"timestamp": ts, "return_1d": 0.05, "bullish_1d": True}],
    )

    text = to_csv([timestamp_join_summary_row(joined)])

    assert text.splitlines()[0] == (
        "matched_event_count,unmatched_event_count,matched_label_index_count,"
        "first_matched_event_index,last_matched_event_index,first_unmatched_event_index,"
        "last_unmatched_event_index"
    )
    assert "\n1,1,1,0,0,1,1" in text


def test_csv_accepts_flat_candle_dataset_summary_rows():
    candles = [
        MarketCandle(datetime(2024, 5, 8, tzinfo=timezone.utc), "BTC-USD", 100, 105, 95, 102, interval="1d"),
        MarketCandle(datetime(2024, 5, 9, tzinfo=timezone.utc), "BTC-USD", 102, 106, 99, 104, interval="1d"),
    ]

    text = to_csv([candle_dataset_summary_row(candles, dataset_id="btc-daily")])

    assert text.splitlines()[0] == (
        "dataset_id,candle_count,asset,interval,source,first_timestamp,last_timestamp"
    )
    assert "\nbtc-daily,2,BTC-USD,1d," in text
    assert "2024-05-08T00:00:00+00:00,2024-05-09T00:00:00+00:00" in text


def test_csv_accepts_flat_multi_candle_dataset_summary_rows():
    btc = [MarketCandle(datetime(2024, 5, 8, tzinfo=timezone.utc), "BTC-USD", 100, 105, 95, 102)]
    eth = [MarketCandle(datetime(2024, 5, 9, tzinfo=timezone.utc), "ETH-USD", 200, 205, 195, 202)]

    text = to_csv(candle_dataset_summary_rows([("btc-daily", btc), ("eth-daily", eth)]))

    assert text.splitlines()[0] == (
        "dataset_id,candle_count,asset,interval,source,first_timestamp,last_timestamp"
    )
    assert "\nbtc-daily,1,BTC-USD,1d," in text
    assert "\neth-daily,1,ETH-USD,1d," in text


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


def test_csv_accepts_ordered_permutation_test_result_rows():
    result = permutation_test(
        [1.0, 1.0, 0.0],
        [0.0, 0.0, 0.0],
        permutations=20,
        seed=19,
        alternative="greater",
    )
    empty_result = PermutationTestResult(
        observed_statistic=0.25,
        p_value=1.0,
        alternative="two-sided",
        permutations=0,
        seed=None,
        null_distribution=[],
        null_mean=0.0,
    )

    text = to_csv(permutation_test_result_rows([
        ("bullish_7d", result),
        ("mean_return_7d", empty_result),
    ]))

    assert text.splitlines()[0] == (
        "scenario_id,observed_statistic,p_value,alternative,permutations,seed,"
        "null_mean,null_distribution_count,null_distribution_min,null_distribution_max"
    )
    assert "\nbullish_7d," in text
    assert "\nmean_return_7d,0.25,1.0,two-sided,0,,0.0,0,," in text


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


def test_csv_accepts_ordered_random_baseline_distribution_rows():
    text = to_csv(random_baseline_distribution_rows(
        [
            ("same_month", []),
            ("all_windows", [1.0, 2.0, 3.0]),
        ],
        sample_size=2,
        samples=5,
        seed=11,
    ))

    assert text.splitlines()[0] == (
        "baseline_id,distribution_count,distribution_min,distribution_max,"
        "distribution_mean,sample_size,samples,seed"
    )
    assert "\nsame_month,0,,,,2,5,11" in text
    assert "\nall_windows,3,1.0,3.0,2.0,2,5,11" in text


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


def test_csv_accepts_ordered_bootstrap_interval_rows():
    text = to_csv(bootstrap_interval_rows(
        [
            ("median_return", (-0.02, 0.03)),
            ("mean_return", (0.01, 0.05)),
        ],
        samples=200,
        confidence=0.95,
        seed=7,
    ))

    assert text.splitlines()[0] == "interval_lower,interval_upper,samples,confidence,seed,statistic_name"
    assert "\n-0.02,0.03,200,0.95,7,median_return" in text
    assert "\n0.01,0.05,200,0.95,7,mean_return" in text


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


def test_csv_accepts_flat_planet_position_encoding_rows():
    timestamp = datetime(2026, 5, 17, tzinfo=timezone.utc)

    text = to_csv(planet_position_encoding_rows([
        PlanetPosition(timestamp, "sun", 90),
    ]))

    assert text.splitlines()[0] == (
        "position_index,timestamp,body,zodiac,longitude,longitude_sin,longitude_cos"
    )
    assert "0,2026-05-17T00:00:00+00:00,sun,tropical,90," in text


def test_csv_accepts_flat_planet_position_series_summary_rows():
    timestamp = datetime(2026, 5, 17, tzinfo=timezone.utc)

    text = to_csv([
        planet_position_series_summary_row(
            [
                PlanetPosition(
                    timestamp,
                    "sun",
                    90,
                    speed=-0.1,
                    retrograde=True,
                    engine="fake",
                )
            ],
            series_id="scan-a",
        )
    ])

    assert text.splitlines()[0] == (
        "series_id,position_count,timestamp_count,unique_body_count,unique_engine_count,"
        "unique_zodiac_count,missing_speed_count,missing_retrograde_count,"
        "first_timestamp,last_timestamp"
    )
    assert "\nscan-a,1,1,1,1,1,0,0,2026-05-17T00:00:00+00:00" in text


def test_csv_accepts_flat_multi_planet_position_series_summary_rows():
    timestamp = datetime(2026, 5, 17, tzinfo=timezone.utc)
    positions = [
        PlanetPosition(
            timestamp,
            "sun",
            90,
            speed=-0.1,
            retrograde=True,
            engine="fake",
        )
    ]

    text = to_csv(planet_position_series_summary_rows([("scan-a", positions), ("empty", [])]))

    assert text.splitlines()[0] == (
        "series_id,position_count,timestamp_count,unique_body_count,unique_engine_count,"
        "unique_zodiac_count,missing_speed_count,missing_retrograde_count,"
        "first_timestamp,last_timestamp"
    )
    assert "\nscan-a,1,1,1,1,1,0,0,2026-05-17T00:00:00+00:00" in text
    assert "\nempty,0,0,0,0,0,0,0,," in text


def test_csv_accepts_flat_planet_position_vector_summary_rows():
    timestamp = datetime(2026, 5, 17, tzinfo=timezone.utc)
    text = to_csv([
        planet_position_vector_summary_row(
            [
                PlanetPosition(timestamp, "sun", 90),
                PlanetPosition(timestamp, "moon", 180),
            ],
            chart_id="chart-a",
        )
    ])

    assert text.splitlines()[0] == (
        "chart_id,position_count,vector_length,first_timestamp,first_body,first_zodiac,"
        "last_timestamp,last_body,last_zodiac"
    )
    assert "chart-a,2,4,2026-05-17T00:00:00+00:00,moon,tropical" in text


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


def test_csv_accepts_flat_nearest_neighbor_summary_rows():
    results = find_nearest(
        [1.0, 0.0],
        [
            SimilarityCandidate("distant-chart", [0.0, 1.0], payload={"asset": "ETH-USD"}),
            SimilarityCandidate("near-chart", [1.0, 0.0], payload={"asset": "BTC-USD"}),
        ],
    )

    text = to_csv([nearest_neighbor_summary_row(results, query_id="btc-query", metric="cosine", limit=10)])

    assert text.splitlines()[0] == (
        "query_id,metric,limit,result_count,top_id,top_score,top_distance,"
        "min_score,max_score,min_distance,max_distance"
    )
    assert "\nbtc-query,cosine,10,2,near-chart,1.0,0.0,0.0,1.0,0.0,1.0" in text
