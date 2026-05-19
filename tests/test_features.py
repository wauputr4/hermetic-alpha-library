from datetime import datetime, timezone

import pytest

from hermetic_alpha.exports import to_csv
from hermetic_alpha.features import (
    aspect_event_feature_matrix_rows,
    aspect_event_feature_matrix_rows_with_schema,
    aspect_event_feature_rows,
)
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


def test_aspect_event_feature_matrix_rows_group_events_by_timestamp():
    ts1 = datetime(2026, 5, 18, tzinfo=timezone.utc)
    ts2 = datetime(2026, 5, 19, tzinfo=timezone.utc)
    events = [
        _aspect_event("mars", "saturn", "square", ts2, phase="separating"),
        _aspect_event("sun", "jupiter", "conjunction", ts1, phase="applying"),
        _aspect_event("mars", "saturn", "square", ts1, phase="exact"),
    ]

    rows = aspect_event_feature_matrix_rows(events)

    assert [row["timestamp"] for row in rows] == [ts1, ts2]
    assert list(rows[0].keys()) == [
        "timestamp",
        "mars_saturn_square_active",
        "mars_saturn_square_orb",
        "mars_saturn_square_strength",
        "mars_saturn_square_phase",
        "sun_jupiter_conjunction_active",
        "sun_jupiter_conjunction_orb",
        "sun_jupiter_conjunction_strength",
        "sun_jupiter_conjunction_phase",
    ]
    assert rows[0]["mars_saturn_square_active"] is True
    assert rows[0]["mars_saturn_square_phase"] == "exact"
    assert rows[0]["sun_jupiter_conjunction_active"] is True
    assert rows[0]["sun_jupiter_conjunction_phase"] == "applying"
    assert rows[1]["mars_saturn_square_active"] is True
    assert rows[1]["sun_jupiter_conjunction_active"] is False
    assert rows[1]["sun_jupiter_conjunction_orb"] is None
    assert rows[1]["sun_jupiter_conjunction_phase"] is None


def test_aspect_event_feature_matrix_rows_are_csv_compatible():
    ts = datetime(2026, 5, 18, tzinfo=timezone.utc)
    rows = aspect_event_feature_matrix_rows([_aspect_event("sun", "jupiter", "conjunction", ts)])

    text = to_csv(rows)

    assert text.splitlines()[0] == (
        "timestamp,sun_jupiter_conjunction_active,sun_jupiter_conjunction_orb,"
        "sun_jupiter_conjunction_strength,sun_jupiter_conjunction_phase"
    )
    assert "2026-05-18T00:00:00+00:00,True,1.25" in text


def test_aspect_event_feature_matrix_rows_reject_missing_timestamps():
    with pytest.raises(ValueError, match="missing a timestamp"):
        aspect_event_feature_matrix_rows([_aspect_event("moon", "venus", "trine", None)])


def test_aspect_event_feature_matrix_rows_reject_duplicate_features_at_same_timestamp():
    ts = datetime(2026, 5, 18, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="duplicate aspect feature"):
        aspect_event_feature_matrix_rows(
            [
                _aspect_event("sun", "jupiter", "conjunction", ts),
                _aspect_event("sun", "jupiter", "conjunction", ts),
            ]
        )


def test_aspect_event_feature_matrix_rows_with_schema_keeps_train_test_columns_stable():
    ts_train = datetime(2026, 5, 18, tzinfo=timezone.utc)
    ts_test = datetime(2026, 5, 19, tzinfo=timezone.utc)
    schema = ["sun_jupiter_conjunction", "mars_saturn_square"]

    train_rows = aspect_event_feature_matrix_rows_with_schema(
        [_aspect_event("sun", "jupiter", "conjunction", ts_train, phase="applying")],
        schema,
        include_unknown_features=False,
    )
    test_rows = aspect_event_feature_matrix_rows_with_schema(
        [_aspect_event("mars", "saturn", "square", ts_test, phase="separating")],
        schema,
        include_unknown_features=False,
    )

    assert list(train_rows[0].keys()) == list(test_rows[0].keys())
    assert train_rows[0]["sun_jupiter_conjunction_active"] is True
    assert train_rows[0]["mars_saturn_square_active"] is False
    assert train_rows[0]["mars_saturn_square_orb"] is None
    assert train_rows[0]["mars_saturn_square_strength"] is None
    assert train_rows[0]["mars_saturn_square_phase"] is None
    assert test_rows[0]["sun_jupiter_conjunction_active"] is False
    assert test_rows[0]["mars_saturn_square_active"] is True


def test_aspect_event_feature_matrix_rows_with_schema_includes_unknown_observed_features_by_default():
    ts = datetime(2026, 5, 18, tzinfo=timezone.utc)

    rows = aspect_event_feature_matrix_rows_with_schema(
        [
            _aspect_event("sun", "jupiter", "conjunction", ts),
            _aspect_event("moon", "venus", "trine", ts),
        ],
        ["sun_jupiter_conjunction"],
    )

    assert list(rows[0].keys()) == [
        "timestamp",
        "sun_jupiter_conjunction_active",
        "sun_jupiter_conjunction_orb",
        "sun_jupiter_conjunction_strength",
        "sun_jupiter_conjunction_phase",
        "moon_venus_trine_active",
        "moon_venus_trine_orb",
        "moon_venus_trine_strength",
        "moon_venus_trine_phase",
    ]
    assert rows[0]["moon_venus_trine_active"] is True


def test_aspect_event_feature_matrix_rows_with_schema_can_reject_unknown_observed_features():
    ts = datetime(2026, 5, 18, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="unknown observed aspect feature"):
        aspect_event_feature_matrix_rows_with_schema(
            [_aspect_event("moon", "venus", "trine", ts)],
            ["sun_jupiter_conjunction"],
            include_unknown_features=False,
        )


def test_aspect_event_feature_matrix_rows_with_schema_rejects_duplicate_configured_features():
    with pytest.raises(ValueError, match="duplicate configured aspect feature"):
        aspect_event_feature_matrix_rows_with_schema(
            [],
            ["sun_jupiter_conjunction", " Sun_Jupiter_Conjunction "],
        )


def test_aspect_event_feature_matrix_rows_with_schema_rejects_duplicate_observed_features():
    ts = datetime(2026, 5, 18, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="duplicate aspect feature"):
        aspect_event_feature_matrix_rows_with_schema(
            [
                _aspect_event("sun", "jupiter", "conjunction", ts),
                _aspect_event("sun", "jupiter", "conjunction", ts),
            ],
            ["sun_jupiter_conjunction"],
        )


def test_aspect_event_feature_matrix_rows_with_schema_are_csv_compatible():
    ts = datetime(2026, 5, 18, tzinfo=timezone.utc)
    rows = aspect_event_feature_matrix_rows_with_schema(
        [_aspect_event("sun", "jupiter", "conjunction", ts)],
        ["sun_jupiter_conjunction", "mars_saturn_square"],
        include_unknown_features=False,
    )

    text = to_csv(rows)

    assert text.splitlines()[0] == (
        "timestamp,sun_jupiter_conjunction_active,sun_jupiter_conjunction_orb,"
        "sun_jupiter_conjunction_strength,sun_jupiter_conjunction_phase,"
        "mars_saturn_square_active,mars_saturn_square_orb,mars_saturn_square_strength,"
        "mars_saturn_square_phase"
    )


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
