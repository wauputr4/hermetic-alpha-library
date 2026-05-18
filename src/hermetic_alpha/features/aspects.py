"""Aspect-event feature row builders."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from hermetic_alpha.models import AspectEvent


def aspect_event_feature_rows(events: Sequence[AspectEvent]) -> list[dict[str, object]]:
    """Return flat scalar feature rows for ordered aspect events.

    The helper preserves caller-supplied event order and emits rows that are
    directly compatible with ``hermetic_alpha.exports.to_csv()``.
    """

    return [_aspect_event_feature_row(event) for event in events]


def aspect_event_feature_matrix_rows(events: Sequence[AspectEvent]) -> list[dict[str, object]]:
    """Return one flat aspect-feature row per timestamp.

    Every observed aspect feature key gets deterministic ``active``, ``orb``,
    ``strength``, and ``phase`` columns. Events without timestamps are rejected
    because they cannot be placed in a timestamp-level matrix.
    """
    grouped: dict[datetime, dict[str, AspectEvent]] = {}
    feature_keys = set[str]()

    for index, event in enumerate(events):
        if event.timestamp is None:
            raise ValueError(f"aspect event at index {index} is missing a timestamp")
        feature_key = _feature_key(event)
        timestamp_events = grouped.setdefault(event.timestamp, {})
        if feature_key in timestamp_events:
            raise ValueError(
                f"duplicate aspect feature {feature_key!r} at timestamp {event.timestamp.isoformat()}"
            )
        timestamp_events[feature_key] = event
        feature_keys.add(feature_key)

    ordered_feature_keys = sorted(feature_keys)
    rows: list[dict[str, object]] = []
    for timestamp in sorted(grouped):
        timestamp_events = grouped[timestamp]
        row: dict[str, object] = {"timestamp": timestamp}
        for feature_key in ordered_feature_keys:
            event = timestamp_events.get(feature_key)
            row[f"{feature_key}_active"] = event is not None
            row[f"{feature_key}_orb"] = event.orb if event is not None else None
            row[f"{feature_key}_strength"] = event.strength if event is not None else None
            row[f"{feature_key}_phase"] = event.phase if event is not None else None
        rows.append(row)
    return rows


def _aspect_event_feature_row(event: AspectEvent) -> dict[str, object]:
    feature_key = _feature_key(event)

    return {
        "timestamp": event.timestamp,
        "body_a": event.body_a,
        "body_b": event.body_b,
        "body_pair": f"{event.body_a}:{event.body_b}",
        "aspect": event.aspect,
        "feature_key": feature_key,
        "active": True,
        "target_angle": event.target_angle,
        "actual_angle": event.actual_angle,
        "orb": event.orb,
        "max_orb": event.max_orb,
        "strength": event.strength,
        "phase": event.phase,
    }


def _feature_key(event: AspectEvent) -> str:
    body_a = event.body_a.strip().lower()
    body_b = event.body_b.strip().lower()
    aspect = event.aspect.strip().lower()
    return f"{body_a}_{body_b}_{aspect}"
