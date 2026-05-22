"""Hermetic Alpha core library."""

__version__ = "0.1.0"

from .models import (
    AspectDefinition,
    AspectEvent,
    EventStudyResult,
    MarketCandle,
    MarketLabel,
    PlanetPosition,
)
from .features import (
    aspect_event_feature_matrix_rows,
    aspect_event_feature_matrix_rows_with_schema,
    aspect_event_feature_matrix_summary_row,
    aspect_event_feature_matrix_summary_rows,
    aspect_event_feature_rows,
)
from .similarity import encode_longitude, encode_planet_positions

__all__ = [
    "__version__",
    "AspectDefinition",
    "AspectEvent",
    "EventStudyResult",
    "MarketCandle",
    "MarketLabel",
    "PlanetPosition",
    "aspect_event_feature_matrix_rows",
    "aspect_event_feature_matrix_rows_with_schema",
    "aspect_event_feature_matrix_summary_row",
    "aspect_event_feature_matrix_summary_rows",
    "aspect_event_feature_rows",
    "encode_longitude",
    "encode_planet_positions",
]
