"""Circular math helpers for astrological longitude calculations."""

from __future__ import annotations


def normalize_degrees(angle: float) -> float:
    """Normalize an angle into the [0, 360) range."""
    return angle % 360


def circular_distance(a: float, b: float) -> float:
    """Return the shortest angular distance between two longitudes in degrees."""
    diff = abs(normalize_degrees(a) - normalize_degrees(b))
    return min(diff, 360 - diff)


def aspect_strength(orb: float, max_orb: float) -> float:
    """Return a 0..1 strength score where tighter orbs are stronger.

    ``max_orb`` may be zero to represent exact-match aspect matching; in that
    case strength is ``1.0`` when ``orb == 0`` and ``0.0`` otherwise.
    """
    if max_orb < 0:
        raise ValueError("max_orb must be non-negative")
    if orb < 0:
        raise ValueError("orb cannot be negative")
    if max_orb == 0:
        return 1.0 if orb == 0 else 0.0
    return max(0.0, min(1.0, 1 - (orb / max_orb)))
