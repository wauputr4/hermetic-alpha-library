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


def aspect_event_feature_matrix_rows_with_schema(
    events: Sequence[AspectEvent],
    feature_keys: Sequence[str],
    *,
    include_unknown_features: bool = True,
) -> list[dict[str, object]]:
    """Return timestamp-level aspect feature rows with a declared schema.

    Configured feature keys always emit ``active``, ``orb``, ``strength``, and
    ``phase`` columns. Observed features outside ``feature_keys`` are included
    by default for compatibility with exploratory workflows; pass
    ``include_unknown_features=False`` to reject them.
    """
    ordered_configured_keys = [_normalize_feature_key(feature_key) for feature_key in feature_keys]
    duplicate_configured_keys = _duplicate_values(ordered_configured_keys)
    if duplicate_configured_keys:
        raise ValueError(f"duplicate configured aspect feature {duplicate_configured_keys[0]!r}")

    grouped: dict[datetime, dict[str, AspectEvent]] = {}
    observed_keys = set[str]()
    configured_key_set = set(ordered_configured_keys)

    for index, event in enumerate(events):
        if event.timestamp is None:
            raise ValueError(f"aspect event at index {index} is missing a timestamp")
        feature_key = _feature_key(event)
        if not include_unknown_features and feature_key not in configured_key_set:
            raise ValueError(f"unknown observed aspect feature {feature_key!r}")
        timestamp_events = grouped.setdefault(event.timestamp, {})
        if feature_key in timestamp_events:
            raise ValueError(
                f"duplicate aspect feature {feature_key!r} at timestamp {event.timestamp.isoformat()}"
            )
        timestamp_events[feature_key] = event
        observed_keys.add(feature_key)

    unknown_keys = sorted(observed_keys - configured_key_set) if include_unknown_features else []
    ordered_feature_keys = [*ordered_configured_keys, *unknown_keys]

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
    body_a = _normalize_feature_key_part(event.body_a)
    body_b = _normalize_feature_key_part(event.body_b)
    aspect = _normalize_feature_key_part(event.aspect)
    return f"{body_a}_{body_b}_{aspect}"


def _normalize_feature_key(feature_key: str) -> str:
    normalized = feature_key.strip().lower()
    if not normalized:
        raise ValueError("configured aspect feature keys must be non-empty")
    return normalized


def _normalize_feature_key_part(value: str) -> str:
    return value.strip().lower()


def _duplicate_values(values: Sequence[str]) -> list[str]:
    seen = set[str]()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return duplicates
