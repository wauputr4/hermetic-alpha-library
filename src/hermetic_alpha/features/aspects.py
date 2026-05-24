"""Aspect-event feature row builders."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime

from hermetic_alpha.models import AspectEvent


def aspect_event_feature_rows(events: Sequence[AspectEvent]) -> list[dict[str, object]]:
    """Return flat scalar feature rows for ordered aspect events.

    The helper preserves caller-supplied event order and emits rows that are
    directly compatible with ``hermetic_alpha.exports.to_csv()``.
    """

    return [_aspect_event_feature_row(event) for event in events]


def aspect_event_feature_group_rows(
    groups: Mapping[str, Sequence[AspectEvent]] | Sequence[tuple[str, Sequence[AspectEvent]]],
) -> list[dict[str, object]]:
    """Return ordered raw aspect feature rows for several named event groups."""

    rows: list[dict[str, object]] = []
    seen_group_ids: set[str] = set()
    for group_id, events in _iter_named_feature_matrices(groups):
        _validate_matrix_id(group_id, "group ID")
        if group_id in seen_group_ids:
            raise ValueError("group IDs must be unique")
        seen_group_ids.add(group_id)
        for row in aspect_event_feature_rows(events):
            rows.append({"group_id": group_id, **row})
    return rows


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


def aspect_event_feature_matrix_summary_row(
    events: Sequence[AspectEvent],
    feature_keys: Sequence[str] | None = None,
    *,
    matrix_id: str | None = None,
) -> dict[str, object]:
    """Return compact metadata for an aspect-event feature matrix.

    The summary is intended for audit tables before CSV export or model
    training. It reports matrix shape and timestamp boundaries without
    replacing the timestamp-level rows produced by the matrix helpers.
    """
    timestamps: list[datetime] = []
    observed_keys = set[str]()
    missing_timestamp_count = 0

    for event in events:
        observed_keys.add(_feature_key(event))
        if event.timestamp is None:
            missing_timestamp_count += 1
        else:
            timestamps.append(event.timestamp)

    configured_count: int | None = None
    duplicate_configured_count: int | None = None
    if feature_keys is not None:
        normalized_configured_keys = [_normalize_feature_key(feature_key) for feature_key in feature_keys]
        configured_count = len(set(normalized_configured_keys))
        duplicate_configured_count = len(normalized_configured_keys) - configured_count

    timestamp_count = len(set(timestamps))

    return {
        "matrix_id": matrix_id,
        "row_count": timestamp_count,
        "timestamp_count": timestamp_count,
        "observed_feature_count": len(observed_keys),
        "configured_feature_count": configured_count,
        "duplicate_configured_feature_count": duplicate_configured_count,
        "missing_timestamp_count": missing_timestamp_count,
        "event_count": len(events),
        "first_timestamp": min(timestamps) if timestamps else None,
        "last_timestamp": max(timestamps) if timestamps else None,
    }


def aspect_event_feature_matrix_summary_rows(
    matrices: Mapping[str, Sequence[AspectEvent]] | Sequence[tuple[str, Sequence[AspectEvent]]],
    feature_keys: (
        Sequence[str]
        | Mapping[str, Sequence[str]]
        | Sequence[tuple[str, Sequence[str]]]
        | None
    ) = None,
) -> list[dict[str, object]]:
    """Return ordered compact metadata rows for several feature matrices."""
    configured_by_matrix = _configured_feature_keys_by_matrix(feature_keys)
    rows: list[dict[str, object]] = []
    seen_matrix_ids: set[str] = set()

    for matrix_id, events in _iter_named_feature_matrices(matrices):
        _validate_matrix_id(matrix_id, "matrix ID")
        if matrix_id in seen_matrix_ids:
            raise ValueError("matrix IDs must be unique")
        seen_matrix_ids.add(matrix_id)

        row = aspect_event_feature_matrix_summary_row(
            events,
            _feature_keys_for_matrix(feature_keys, configured_by_matrix, matrix_id),
        )
        rows.append({**row, "matrix_id": matrix_id})
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


def _iter_named_feature_matrices(
    matrices: Mapping[str, Sequence[AspectEvent]] | Sequence[tuple[str, Sequence[AspectEvent]]],
) -> Iterable[tuple[str, Sequence[AspectEvent]]]:
    if isinstance(matrices, Mapping):
        yield from matrices.items()
        return
    yield from matrices


def _configured_feature_keys_by_matrix(
    feature_keys: (
        Sequence[str]
        | Mapping[str, Sequence[str]]
        | Sequence[tuple[str, Sequence[str]]]
        | None
    ),
) -> dict[str, Sequence[str]] | None:
    if feature_keys is None:
        return None
    if isinstance(feature_keys, Mapping):
        configured: dict[str, Sequence[str]] = {}
        for matrix_id, matrix_feature_keys in feature_keys.items():
            _validate_matrix_id(matrix_id, "configured matrix ID")
            configured[matrix_id] = matrix_feature_keys
        return configured
    if _is_ordered_feature_key_pairs(feature_keys):
        configured: dict[str, Sequence[str]] = {}
        for matrix_id, matrix_feature_keys in feature_keys:
            _validate_matrix_id(matrix_id, "configured matrix ID")
            if matrix_id in configured:
                raise ValueError("configured matrix IDs must be unique")
            configured[matrix_id] = matrix_feature_keys
        return configured
    return None


def _feature_keys_for_matrix(
    feature_keys: (
        Sequence[str]
        | Mapping[str, Sequence[str]]
        | Sequence[tuple[str, Sequence[str]]]
        | None
    ),
    configured_by_matrix: dict[str, Sequence[str]] | None,
    matrix_id: str,
) -> Sequence[str] | None:
    if feature_keys is None:
        return None
    if configured_by_matrix is None:
        return feature_keys  # type: ignore[return-value]
    if matrix_id not in configured_by_matrix:
        raise ValueError(f"configured feature keys are missing matrix ID {matrix_id!r}")
    return configured_by_matrix[matrix_id]


def _is_ordered_feature_key_pairs(
    feature_keys: Sequence[str] | Sequence[tuple[str, Sequence[str]]],
) -> bool:
    return bool(feature_keys) and all(
        isinstance(item, tuple) and len(item) == 2 for item in feature_keys
    )


def _normalize_feature_key(feature_key: object) -> str:
    if not isinstance(feature_key, str):
        raise ValueError("configured aspect feature keys must be non-blank strings")
    normalized = feature_key.strip().lower()
    if not normalized:
        raise ValueError("configured aspect feature keys must be non-blank strings")
    return normalized


def _normalize_feature_key_part(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("aspect feature components must be non-blank strings")
    return value.strip().lower()


def _validate_matrix_id(matrix_id: object, label: str) -> None:
    if not isinstance(matrix_id, str) or not matrix_id.strip():
        raise ValueError(f"{label} must be a non-blank string")


def _duplicate_values(values: Sequence[str]) -> list[str]:
    seen = set[str]()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return duplicates
