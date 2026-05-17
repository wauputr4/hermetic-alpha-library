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
from .similarity import encode_longitude, encode_planet_positions

__all__ = [
    "__version__",
    "AspectDefinition",
    "AspectEvent",
    "EventStudyResult",
    "MarketCandle",
    "MarketLabel",
    "PlanetPosition",
    "encode_longitude",
    "encode_planet_positions",
]
