from datetime import datetime, timezone

from hermetic_alpha import (
    AspectDefinition,
    EventStudyResult,
    MarketCandle,
    PlanetPosition,
    aspect_event_feature_matrix_rows,
    aspect_event_feature_matrix_rows_with_schema,
    aspect_event_feature_matrix_summary_row,
    aspect_event_feature_matrix_summary_rows,
    aspect_event_feature_rows,
)
from hermetic_alpha.analysis import (
    aspect_event_study,
    bootstrap_interval_row,
    bootstrap_interval_rows,
    multi_horizon_baseline_comparison_group_rows,
    multi_horizon_baseline_comparison_rows,
    permutation_test_result_rows,
    random_baseline_distribution_rows,
    summarize_validated_multi_horizon_event_study,
    timestamp_join_summary_row,
    timestamp_join_summary_rows,
    validated_multi_horizon_event_study_report_rows,
    walk_forward_split_group_rows,
)
from hermetic_alpha.astro import AspectDefinition as AstroAspectDefinition
from hermetic_alpha.astro import (
    aspect_scan_summary_row,
    aspect_scan_summary_rows,
    planet_position_series_summary_row,
    planet_position_series_summary_rows,
)
from hermetic_alpha.features import (
    aspect_event_feature_matrix_rows as features_aspect_event_feature_matrix_rows,
    aspect_event_feature_matrix_rows_with_schema as features_aspect_event_feature_matrix_rows_with_schema,
    aspect_event_feature_matrix_summary_row as features_aspect_event_feature_matrix_summary_row,
    aspect_event_feature_matrix_summary_rows as features_aspect_event_feature_matrix_summary_rows,
    aspect_event_feature_rows as features_aspect_event_feature_rows,
)
from hermetic_alpha.market import candle_dataset_summary_row, candle_dataset_summary_rows
from hermetic_alpha.labels import (
    forward_return_label_coverage_row,
    local_extrema_label_coverage_row,
    multi_dataset_forward_return_label_coverage_rows,
    multi_dataset_local_extrema_label_coverage_rows,
    multi_horizon_forward_return_label_coverage_rows,
    multi_window_local_extrema_label_coverage_rows,
)
from hermetic_alpha.similarity import (
    nearest_neighbor_summary_row,
    nearest_neighbor_summary_rows,
    planet_position_encoding_rows,
    planet_position_vector_summary_row,
    planet_position_vector_summary_rows,
)


def test_public_api_exports_match_documented_entrypoints():
    assert AspectDefinition is AstroAspectDefinition
    assert aspect_event_feature_rows is features_aspect_event_feature_rows
    assert aspect_event_feature_matrix_rows is features_aspect_event_feature_matrix_rows
    assert aspect_event_feature_matrix_rows_with_schema is features_aspect_event_feature_matrix_rows_with_schema
    assert aspect_event_feature_matrix_summary_row is features_aspect_event_feature_matrix_summary_row
    assert aspect_event_feature_matrix_summary_rows is features_aspect_event_feature_matrix_summary_rows
    assert callable(aspect_event_study)
    assert callable(aspect_scan_summary_row)
    assert callable(aspect_scan_summary_rows)
    assert callable(planet_position_series_summary_row)
    assert callable(planet_position_series_summary_rows)
    assert callable(bootstrap_interval_row)
    assert callable(bootstrap_interval_rows)
    assert callable(multi_horizon_baseline_comparison_group_rows)
    assert callable(multi_horizon_baseline_comparison_rows)
    assert callable(permutation_test_result_rows)
    assert callable(random_baseline_distribution_rows)
    assert callable(planet_position_encoding_rows)
    assert callable(planet_position_vector_summary_row)
    assert callable(planet_position_vector_summary_rows)
    assert callable(nearest_neighbor_summary_row)
    assert callable(nearest_neighbor_summary_rows)
    assert callable(summarize_validated_multi_horizon_event_study)
    assert callable(timestamp_join_summary_row)
    assert callable(timestamp_join_summary_rows)
    assert callable(validated_multi_horizon_event_study_report_rows)
    assert callable(walk_forward_split_group_rows)
    assert callable(candle_dataset_summary_row)
    assert callable(candle_dataset_summary_rows)
    assert callable(forward_return_label_coverage_row)
    assert callable(local_extrema_label_coverage_row)
    assert callable(multi_dataset_forward_return_label_coverage_rows)
    assert callable(multi_dataset_local_extrema_label_coverage_rows)
    assert callable(multi_horizon_forward_return_label_coverage_rows)
    assert callable(multi_window_local_extrema_label_coverage_rows)

    ts = datetime(2026, 5, 6, tzinfo=timezone.utc)
    labels = [{"return_1d": 0.1, "bullish_1d": True}, {"return_1d": -0.05, "bullish_1d": False}]
    result = aspect_event_study(labels, event_indexes=[0], horizon=1)

    assert isinstance(result, EventStudyResult)
    assert result.horizon == 1
    assert result.events == 1
    assert MarketCandle(ts, "BTC-USD", 1.0, 2.0, 0.5, 1.5).asset == "BTC-USD"
    assert PlanetPosition(ts, "sun", 10.0).to_dict()["timestamp"] == ts.isoformat()
