"""Circular longitude encoders for chart similarity workflows."""

from __future__ import annotations

from datetime import date, datetime
from math import cos, radians, sin
from typing import Sequence

from hermetic_alpha.astro.math import normalize_degrees
from hermetic_alpha.models import PlanetPosition

EncodingScalar = str | int | float | bool | date | datetime | None


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


def planet_position_encoding_rows(positions: Sequence[PlanetPosition]) -> list[dict[str, EncodingScalar]]:
    """Return flat inspectable rows for encoded planet-position components."""

    rows: list[dict[str, EncodingScalar]] = []
    for position_index, position in enumerate(sorted(positions, key=_position_sort_key)):
        longitude_sin, longitude_cos = encode_longitude(position.longitude)
        rows.append(
            {
                "position_index": position_index,
                "timestamp": position.timestamp,
                "body": position.body,
                "zodiac": position.zodiac,
                "longitude": position.longitude,
                "longitude_sin": longitude_sin,
                "longitude_cos": longitude_cos,
            }
        )
    return rows


def planet_position_vector_summary_row(
    positions: Sequence[PlanetPosition],
    *,
    chart_id: EncodingScalar = None,
) -> dict[str, EncodingScalar]:
    """Return compact chart-state vector metadata for CSV-friendly audits."""

    ordered_positions = sorted(positions, key=_position_sort_key)
    first_position = ordered_positions[0] if ordered_positions else None
    last_position = ordered_positions[-1] if ordered_positions else None
    return {
        "chart_id": chart_id,
        "position_count": len(ordered_positions),
        "vector_length": len(ordered_positions) * 2,
        "first_timestamp": first_position.timestamp if first_position is not None else None,
        "first_body": first_position.body if first_position is not None else None,
        "first_zodiac": first_position.zodiac if first_position is not None else None,
        "last_timestamp": last_position.timestamp if last_position is not None else None,
        "last_body": last_position.body if last_position is not None else None,
        "last_zodiac": last_position.zodiac if last_position is not None else None,
    }


def _position_sort_key(position: PlanetPosition) -> tuple[datetime, str, str]:
    return (position.timestamp, position.body, position.zodiac)
