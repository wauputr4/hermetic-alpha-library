"""Aspect detection utilities."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from itertools import combinations
from typing import Iterable, Mapping

from hermetic_alpha.models import AspectEvent, AspectPhase, PlanetPosition

from .math import ANGLE_TOLERANCE, aspect_strength, circular_distance

ASPECT_ANGLES: dict[str, float] = {
    "conjunction": 0.0,
    "sextile": 60.0,
    "square": 90.0,
    "trine": 120.0,
    "opposition": 180.0,
}

PHASE_PROJECTION_STEP = 1e-6


def _aspect_orb(longitude_a: float, longitude_b: float, target_angle: float) -> float:
    return abs(circular_distance(longitude_a, longitude_b) - target_angle)


def _classify_phase(
    longitude_a: float,
    speed_a: float | None,
    longitude_b: float,
    speed_b: float | None,
    target_angle: float,
    orb: float,
) -> AspectPhase:
    if orb <= ANGLE_TOLERANCE:
        return "exact"
    if speed_a is None or speed_b is None:
        return "unknown"

    projected_orb = _aspect_orb(
        longitude_a + (speed_a * PHASE_PROJECTION_STEP),
        longitude_b + (speed_b * PHASE_PROJECTION_STEP),
        target_angle,
    )
    delta = projected_orb - orb
    if abs(delta) <= ANGLE_TOLERANCE:
        return "unknown"
    if delta < 0:
        return "applying"
    return "separating"


def detect_aspect(
    body_a: str,
    longitude_a: float,
    body_b: str,
    longitude_b: float,
    aspect: str,
    max_orb: float,
    timestamp: datetime | None = None,
    speed_a: float | None = None,
    speed_b: float | None = None,
) -> AspectEvent | None:
    """Detect whether two bodies form a requested aspect within max_orb."""
    if aspect not in ASPECT_ANGLES:
        raise ValueError(f"Unsupported aspect: {aspect}")

    target_angle = ASPECT_ANGLES[aspect]
    actual_angle = circular_distance(longitude_a, longitude_b)
    orb = _aspect_orb(longitude_a, longitude_b, target_angle)

    if max_orb == 0 and orb <= ANGLE_TOLERANCE:
        orb = 0.0
    elif orb > max_orb:
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
        phase=_classify_phase(longitude_a, speed_a, longitude_b, speed_b, target_angle, orb),
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

    def unpack(body: str) -> tuple[float, datetime | None, float | None]:
        value = longitudes[body]
        if isinstance(value, PlanetPosition):
            return value.longitude, value.timestamp, value.speed
        return value, timestamp, None

    for body_a, body_b in combinations(longitudes.keys(), 2):
        longitude_a, timestamp_a, speed_a = unpack(body_a)
        longitude_b, timestamp_b, speed_b = unpack(body_b)
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
                speed_a=speed_a,
                speed_b=speed_b,
            )
            if event is not None:
                events.append(event)

    return events


def scan_aspect_series(
    positions: Iterable[PlanetPosition],
    aspects: Mapping[str, float] | None = None,
) -> list[AspectEvent]:
    """Scan timestamped planet positions for aspects at each timestamp.

    Positions are grouped by exact timestamp, then each timestamp group is
    scanned independently. Missing bodies are ignored instead of inferred.
    """
    grouped: dict[datetime, dict[str, PlanetPosition]] = {}
    for position in positions:
        if not isinstance(position, PlanetPosition):
            raise ValueError("positions must contain PlanetPosition values")
        if position.timestamp.tzinfo is None or position.timestamp.utcoffset() is None:
            raise ValueError("position timestamps must be timezone-aware")
        if not position.body:
            raise ValueError("position body must not be empty")

        timestamp_group = grouped.setdefault(position.timestamp, {})
        if position.body in timestamp_group:
            raise ValueError(
                f"duplicate position for body {position.body!r} at {position.timestamp.isoformat()}"
            )
        timestamp_group[position.body] = position

    events: list[AspectEvent] = []
    for timestamp in sorted(grouped):
        timestamp_positions = {
            body: grouped[timestamp][body]
            for body in sorted(grouped[timestamp])
        }
        events.extend(find_aspects(timestamp_positions, aspects=aspects, timestamp=timestamp))
    return events


def aspect_scan_summary_row(events: Sequence[AspectEvent]) -> dict[str, object]:
    """Return compact metadata for an aspect scan.

    The summary is intended for audit tables before feature engineering or
    event-study joins. It does not replace exporting individual aspect events
    or feature rows.
    """
    timestamps: list[datetime] = []
    aspects = set[str]()
    body_pairs = set[tuple[str, str]]()
    phase_counts = {
        "applying": 0,
        "separating": 0,
        "exact": 0,
        "unknown": 0,
    }
    missing_timestamp_count = 0

    for event in events:
        aspects.add(event.aspect)
        body_pairs.add((event.body_a, event.body_b))
        phase_counts[event.phase] = phase_counts.get(event.phase, 0) + 1
        if event.timestamp is None:
            missing_timestamp_count += 1
        else:
            timestamps.append(event.timestamp)

    timestamp_count = len(set(timestamps))

    return {
        "event_count": len(events),
        "timestamp_count": timestamp_count,
        "unique_aspect_count": len(aspects),
        "unique_body_pair_count": len(body_pairs),
        "applying_phase_count": phase_counts["applying"],
        "separating_phase_count": phase_counts["separating"],
        "exact_phase_count": phase_counts["exact"],
        "unknown_phase_count": phase_counts["unknown"],
        "missing_timestamp_count": missing_timestamp_count,
        "first_timestamp": min(timestamps) if timestamps else None,
        "last_timestamp": max(timestamps) if timestamps else None,
    }


def aspect_scan_summary_rows(
    scans: Mapping[str, Sequence[AspectEvent]] | Sequence[tuple[str, Sequence[AspectEvent]]],
) -> list[dict[str, object]]:
    """Return ordered compact metadata rows for several aspect scans."""
    rows: list[dict[str, object]] = []
    seen_scan_ids: set[str] = set()
    for scan_id, events in _iter_named_aspect_scans(scans):
        if not scan_id.strip():
            raise ValueError("scan ID must not be blank")
        if scan_id in seen_scan_ids:
            raise ValueError("scan IDs must be unique")
        seen_scan_ids.add(scan_id)

        row = aspect_scan_summary_row(events)
        rows.append({"scan_id": scan_id, **row})
    return rows


def _iter_named_aspect_scans(
    scans: Mapping[str, Sequence[AspectEvent]] | Sequence[tuple[str, Sequence[AspectEvent]]],
) -> Iterable[tuple[str, Sequence[AspectEvent]]]:
    if isinstance(scans, Mapping):
        yield from scans.items()
        return
    yield from scans
