"""Aspect detection utilities."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Mapping

from .math import aspect_strength, circular_distance

ASPECT_ANGLES: dict[str, float] = {
    "conjunction": 0.0,
    "sextile": 60.0,
    "square": 90.0,
    "trine": 120.0,
    "opposition": 180.0,
}


@dataclass(frozen=True)
class AspectEvent:
    body_a: str
    body_b: str
    aspect: str
    target_angle: float
    actual_angle: float
    orb: float
    max_orb: float
    strength: float


def detect_aspect(
    body_a: str,
    longitude_a: float,
    body_b: str,
    longitude_b: float,
    aspect: str,
    max_orb: float,
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
    )


def find_aspects(
    longitudes: Mapping[str, float],
    aspects: Mapping[str, float] | None = None,
) -> list[AspectEvent]:
    """Find all configured aspects between all supplied body longitudes.

    Args:
        longitudes: Mapping of body name to ecliptic longitude in degrees.
        aspects: Mapping of aspect name to max orb. Defaults to 3° for major aspects.
    """
    aspect_orbs = aspects or {name: 3.0 for name in ASPECT_ANGLES}
    events: list[AspectEvent] = []

    for body_a, body_b in combinations(longitudes.keys(), 2):
        for aspect, max_orb in aspect_orbs.items():
            event = detect_aspect(
                body_a,
                longitudes[body_a],
                body_b,
                longitudes[body_b],
                aspect,
                max_orb,
            )
            if event is not None:
                events.append(event)

    return events
