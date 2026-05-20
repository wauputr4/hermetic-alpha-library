from datetime import datetime, timezone

from hermetic_alpha import (
    AspectDefinition,
    EventStudyResult,
    MarketCandle,
    PlanetPosition,
    aspect_event_feature_matrix_rows,
    aspect_event_feature_matrix_rows_with_schema,
    aspect_event_feature_rows,
)
from hermetic_alpha.analysis import (
    aspect_event_study,
    bootstrap_interval_row,
    multi_horizon_baseline_comparison_rows,
    summarize_validated_multi_horizon_event_study,
    timestamp_join_summary_row,
    validated_multi_horizon_event_study_report_rows,
)
from hermetic_alpha.astro import AspectDefinition as AstroAspectDefinition
from hermetic_alpha.features import (
    aspect_event_feature_matrix_rows as features_aspect_event_feature_matrix_rows,
    aspect_event_feature_matrix_rows_with_schema as features_aspect_event_feature_matrix_rows_with_schema,
    aspect_event_feature_rows as features_aspect_event_feature_rows,
)
from hermetic_alpha.market import candle_dataset_summary_row
from hermetic_alpha.similarity import planet_position_encoding_rows, planet_position_vector_summary_row


def test_public_api_exports_match_documented_entrypoints():
    assert AspectDefinition is AstroAspectDefinition
    assert aspect_event_feature_rows is features_aspect_event_feature_rows
    assert aspect_event_feature_matrix_rows is features_aspect_event_feature_matrix_rows
    assert aspect_event_feature_matrix_rows_with_schema is features_aspect_event_feature_matrix_rows_with_schema
    assert callable(aspect_event_study)
    assert callable(bootstrap_interval_row)
    assert callable(multi_horizon_baseline_comparison_rows)
    assert callable(planet_position_encoding_rows)
    assert callable(planet_position_vector_summary_row)
    assert callable(summarize_validated_multi_horizon_event_study)
    assert callable(timestamp_join_summary_row)
    assert callable(validated_multi_horizon_event_study_report_rows)
    assert callable(candle_dataset_summary_row)

    ts = datetime(2026, 5, 6, tzinfo=timezone.utc)
    labels = [{"return_1d": 0.1, "bullish_1d": True}, {"return_1d": -0.05, "bullish_1d": False}]
    result = aspect_event_study(labels, event_indexes=[0], horizon=1)

    assert isinstance(result, EventStudyResult)
    assert result.horizon == 1
    assert result.events == 1
    assert MarketCandle(ts, "BTC-USD", 1.0, 2.0, 0.5, 1.5).asset == "BTC-USD"
    assert PlanetPosition(ts, "sun", 10.0).to_dict()["timestamp"] == ts.isoformat()
