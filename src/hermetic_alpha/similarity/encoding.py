"""Circular longitude encoders for chart similarity workflows."""

from __future__ import annotations

from math import cos, radians, sin
from typing import Sequence

from hermetic_alpha.astro.math import normalize_degrees
from hermetic_alpha.models import PlanetPosition


def encode_longitude(longitude: float) -> tuple[float, float]:
    """Encode a longitude in degrees as a circular ``(sin, cos)`` pair."""

    angle = radians(normalize_degrees(longitude))
    return (sin(angle), cos(angle))


def encode_planet_positions(positions: Sequence[PlanetPosition]) -> list[float]:
    """Encode positions into a deterministic numeric similarity vector.

    Positions are sorted by timestamp, body, and zodiac before encoding. Each
    position contributes two values: ``longitude_sin`` then ``longitude_cos``.
    """

    vector: list[float] = []
    for position in sorted(positions, key=_position_sort_key):
        vector.extend(encode_longitude(position.longitude))
    return vector


def _position_sort_key(position: PlanetPosition) -> tuple[str, str, str]:
    return (position.timestamp.isoformat(), position.body, position.zodiac)
