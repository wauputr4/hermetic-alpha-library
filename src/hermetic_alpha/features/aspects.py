"""Aspect-event feature row builders."""

from __future__ import annotations

from collections.abc import Sequence

from hermetic_alpha.models import AspectEvent


def aspect_event_feature_rows(events: Sequence[AspectEvent]) -> list[dict[str, object]]:
    """Return flat scalar feature rows for ordered aspect events.

    The helper preserves caller-supplied event order and emits rows that are
    directly compatible with ``hermetic_alpha.exports.to_csv()``.
    """

    return [_aspect_event_feature_row(event) for event in events]


def _aspect_event_feature_row(event: AspectEvent) -> dict[str, object]:
    body_a = event.body_a.strip().lower()
    body_b = event.body_b.strip().lower()
    aspect = event.aspect.strip().lower()
    feature_key = f"{body_a}_{body_b}_{aspect}"

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
