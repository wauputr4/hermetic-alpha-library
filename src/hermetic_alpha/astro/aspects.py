"""Aspect detection utilities."""

from __future__ import annotations

from datetime import datetime
from itertools import combinations
from typing import Mapping

from hermetic_alpha.models import AspectEvent, PlanetPosition

from .math import aspect_strength, circular_distance

ASPECT_ANGLES: dict[str, float] = {
    "conjunction": 0.0,
    "sextile": 60.0,
    "square": 90.0,
    "trine": 120.0,
    "opposition": 180.0,
}


def detect_aspect(
    body_a: str,
    longitude_a: float,
    body_b: str,
    longitude_b: float,
    aspect: str,
    max_orb: float,
    timestamp: datetime | None = None,
) -> AspectEvent | None:
    """Detect whether two bodies form a requested aspect within max_orb."""
    if aspect not in ASPECT_ANGLES:
        raise ValueError(f"Unsupported aspect: {aspect}")

    actual_angle = circular_distance(longitude_a, longitude_b)
    target_angle = ASPECT_ANGLES[aspect]
    orb = abs(actual_angle - target_angle)

    if orb > max_orb:
        return None

    return AspectEvent(
        body_a=body_a,
        body_b=body_b,
        aspect=aspect,
        target_angle=target_angle,
        actual_angle=actual_angle,
        orb=orb,
        max_orb=max_orb,
        strength=aspect_strength(orb, max_orb),
        timestamp=timestamp,
    )


def find_aspects(
    longitudes: Mapping[str, float | PlanetPosition],
    aspects: Mapping[str, float] | None = None,
    timestamp: datetime | None = None,
) -> list[AspectEvent]:
    """Find all configured aspects between all supplied body longitudes.

    Args:
        longitudes: Mapping of body name to ecliptic longitude in degrees, or
            PlanetPosition values. When PlanetPosition values are supplied, their
            timestamps are propagated to detected AspectEvent objects.
        aspects: Mapping of aspect name to max orb. Defaults to 3° for major aspects.
        timestamp: Optional timestamp to attach to every detected event when raw
            longitude floats are supplied.
    """
    aspect_orbs = aspects or {name: 3.0 for name in ASPECT_ANGLES}
    events: list[AspectEvent] = []

    def unpack(body: str) -> tuple[float, datetime | None]:
        value = longitudes[body]
        if isinstance(value, PlanetPosition):
            return value.longitude, value.timestamp
        return value, timestamp

    for body_a, body_b in combinations(longitudes.keys(), 2):
        longitude_a, timestamp_a = unpack(body_a)
        longitude_b, timestamp_b = unpack(body_b)
        event_timestamp = timestamp_a if timestamp_a == timestamp_b else timestamp
        for aspect, max_orb in aspect_orbs.items():
            event = detect_aspect(
                body_a,
                longitude_a,
                body_b,
                longitude_b,
                aspect,
                max_orb,
                timestamp=event_timestamp,
            )
            if event is not None:
                events.append(event)

    return events
