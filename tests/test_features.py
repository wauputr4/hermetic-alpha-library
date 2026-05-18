from datetime import datetime, timezone

from hermetic_alpha.exports import to_csv
from hermetic_alpha.features import aspect_event_feature_rows
from hermetic_alpha.models import AspectEvent


def test_aspect_event_feature_rows_emit_flat_scalar_columns_in_input_order():
    ts = datetime(2026, 5, 18, tzinfo=timezone.utc)
    events = [
        _aspect_event("sun", "jupiter", "conjunction", ts, phase="applying"),
        _aspect_event("mars", "saturn", "square", ts, phase="separating"),
    ]

    rows = aspect_event_feature_rows(events)

    assert [row["feature_key"] for row in rows] == [
        "sun_jupiter_conjunction",
        "mars_saturn_square",
    ]
    assert rows[0] == {
        "timestamp": ts,
        "body_a": "sun",
        "body_b": "jupiter",
        "body_pair": "sun:jupiter",
        "aspect": "conjunction",
        "feature_key": "sun_jupiter_conjunction",
        "active": True,
        "target_angle": 0.0,
        "actual_angle": 1.25,
        "orb": 1.25,
        "max_orb": 3.0,
        "strength": 1 - (1.25 / 3.0),
        "phase": "applying",
    }
    assert rows[1]["body_pair"] == "mars:saturn"
    assert rows[1]["phase"] == "separating"


def test_aspect_event_feature_rows_preserve_missing_timestamps():
    rows = aspect_event_feature_rows([_aspect_event("moon", "venus", "trine", None)])

    assert rows[0]["timestamp"] is None
    assert rows[0]["feature_key"] == "moon_venus_trine"
    assert rows[0]["active"] is True


def test_aspect_event_feature_rows_are_csv_compatible():
    ts = datetime(2026, 5, 18, tzinfo=timezone.utc)
    rows = aspect_event_feature_rows([_aspect_event("sun", "jupiter", "conjunction", ts)])

    text = to_csv(rows)

    assert text.splitlines()[0] == (
        "timestamp,body_a,body_b,body_pair,aspect,feature_key,active,"
        "target_angle,actual_angle,orb,max_orb,strength,phase"
    )
    assert "2026-05-18T00:00:00+00:00,sun,jupiter,sun:jupiter,conjunction" in text


def _aspect_event(
    body_a: str,
    body_b: str,
    aspect: str,
    timestamp: datetime | None,
    *,
    phase: str = "unknown",
) -> AspectEvent:
    return AspectEvent(
        body_a=body_a,
        body_b=body_b,
        aspect=aspect,
        target_angle=0.0,
        actual_angle=1.25,
        orb=1.25,
        max_orb=3.0,
        strength=1 - (1.25 / 3.0),
        timestamp=timestamp,
        phase=phase,
    )
