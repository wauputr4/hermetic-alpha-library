from datetime import datetime, timezone

import pytest

from hermetic_alpha.exports import to_csv
from hermetic_alpha.features import (
    aspect_event_feature_matrix_rows,
    aspect_event_feature_matrix_rows_with_schema,
    aspect_event_feature_matrix_summary_row,
    aspect_event_feature_matrix_summary_rows,
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


def test_aspect_event_feature_rows_reject_non_string_feature_components():
    with pytest.raises(ValueError, match="aspect feature components must be non-blank strings"):
        aspect_event_feature_rows([_aspect_event(42, "jupiter", "conjunction", None)])


def test_aspect_event_feature_rows_reject_blank_feature_components():
    with pytest.raises(ValueError, match="aspect feature components must be non-blank strings"):
        aspect_event_feature_rows([_aspect_event("sun", "   ", "conjunction", None)])


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


def test_aspect_event_feature_matrix_rows_reject_non_string_feature_components():
    ts = datetime(2026, 5, 18, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="aspect feature components must be non-blank strings"):
        aspect_event_feature_matrix_rows([_aspect_event("sun", 42, "conjunction", ts)])


def test_aspect_event_feature_matrix_rows_reject_blank_feature_components():
    ts = datetime(2026, 5, 18, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="aspect feature components must be non-blank strings"):
        aspect_event_feature_matrix_rows([_aspect_event("sun", "jupiter", "   ", ts)])


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


def test_aspect_event_feature_matrix_rows_with_schema_rejects_non_string_configured_features():
    with pytest.raises(ValueError, match="configured aspect feature keys must be non-blank strings"):
        aspect_event_feature_matrix_rows_with_schema([], ["sun_jupiter_conjunction", 42])


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


def test_aspect_event_feature_matrix_rows_with_schema_rejects_non_string_observed_components():
    ts = datetime(2026, 5, 18, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="aspect feature components must be non-blank strings"):
        aspect_event_feature_matrix_rows_with_schema(
            [_aspect_event("sun", "jupiter", 42, ts)],
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


def test_aspect_event_feature_matrix_summary_row_reports_shape_and_boundaries():
    ts1 = datetime(2026, 5, 18, tzinfo=timezone.utc)
    ts2 = datetime(2026, 5, 19, tzinfo=timezone.utc)
    events = [
        _aspect_event("sun", "jupiter", "conjunction", ts2),
        _aspect_event("sun", "jupiter", "conjunction", ts1),
        _aspect_event("mars", "saturn", "square", ts1),
    ]

    row = aspect_event_feature_matrix_summary_row(
        events,
        ["sun_jupiter_conjunction", "mars_saturn_square"],
        matrix_id="train",
    )

    assert row == {
        "matrix_id": "train",
        "row_count": 2,
        "timestamp_count": 2,
        "observed_feature_count": 2,
        "configured_feature_count": 2,
        "duplicate_configured_feature_count": 0,
        "missing_timestamp_count": 0,
        "event_count": 3,
        "first_timestamp": ts1,
        "last_timestamp": ts2,
    }


def test_aspect_event_feature_matrix_summary_row_counts_missing_timestamps():
    ts = datetime(2026, 5, 18, tzinfo=timezone.utc)

    row = aspect_event_feature_matrix_summary_row(
        [
            _aspect_event("moon", "venus", "trine", None),
            _aspect_event("sun", "jupiter", "conjunction", ts),
        ]
    )

    assert row["row_count"] == 1
    assert row["timestamp_count"] == 1
    assert row["observed_feature_count"] == 2
    assert row["configured_feature_count"] is None
    assert row["duplicate_configured_feature_count"] is None
    assert row["missing_timestamp_count"] == 1
    assert row["first_timestamp"] == ts
    assert row["last_timestamp"] == ts


def test_aspect_event_feature_matrix_summary_row_normalizes_duplicate_configured_keys():
    row = aspect_event_feature_matrix_summary_row(
        [],
        [" Sun_Jupiter_Conjunction ", "sun_jupiter_conjunction", "mars_saturn_square"],
    )

    assert row["configured_feature_count"] == 2
    assert row["duplicate_configured_feature_count"] == 1
    assert row["row_count"] == 0
    assert row["event_count"] == 0
    assert row["first_timestamp"] is None
    assert row["last_timestamp"] is None


def test_aspect_event_feature_matrix_summary_row_rejects_empty_configured_keys():
    with pytest.raises(ValueError, match="configured aspect feature keys must be non-blank strings"):
        aspect_event_feature_matrix_summary_row([], [" "])


def test_aspect_event_feature_matrix_summary_row_rejects_non_string_configured_keys():
    with pytest.raises(ValueError, match="configured aspect feature keys must be non-blank strings"):
        aspect_event_feature_matrix_summary_row([], ["sun_jupiter_conjunction", 42])


def test_aspect_event_feature_matrix_summary_row_rejects_non_string_observed_components():
    with pytest.raises(ValueError, match="aspect feature components must be non-blank strings"):
        aspect_event_feature_matrix_summary_row(
            [_aspect_event("sun", "jupiter", 42, None)],
            ["sun_jupiter_conjunction"],
        )


def test_aspect_event_feature_matrix_summary_row_is_csv_compatible():
    ts = datetime(2026, 5, 18, tzinfo=timezone.utc)
    row = aspect_event_feature_matrix_summary_row(
        [_aspect_event("sun", "jupiter", "conjunction", ts)],
        ["sun_jupiter_conjunction"],
        matrix_id="train",
    )

    text = to_csv([row])

    assert text.splitlines()[0] == (
        "matrix_id,row_count,timestamp_count,observed_feature_count,configured_feature_count,"
        "duplicate_configured_feature_count,missing_timestamp_count,event_count,"
        "first_timestamp,last_timestamp"
    )
    assert "train,1,1,1,1,0,0,1,2026-05-18T00:00:00+00:00" in text


def test_aspect_event_feature_matrix_summary_rows_preserves_ordered_mapping_order():
    ts1 = datetime(2026, 5, 18, tzinfo=timezone.utc)
    ts2 = datetime(2026, 5, 19, tzinfo=timezone.utc)
    first = [_aspect_event("sun", "jupiter", "conjunction", ts1)]
    second = [_aspect_event("mars", "saturn", "square", ts2)]

    rows = aspect_event_feature_matrix_summary_rows({"train": first, "test": second})

    assert [row["matrix_id"] for row in rows] == ["train", "test"]
    assert rows[0]["event_count"] == 1
    assert rows[0]["first_timestamp"] == ts1
    assert rows[1]["first_timestamp"] == ts2


def test_aspect_event_feature_matrix_summary_rows_accepts_ordered_pairs_and_empty_events():
    ts = datetime(2026, 5, 18, tzinfo=timezone.utc)
    events = [_aspect_event("sun", "jupiter", "conjunction", ts)]

    rows = aspect_event_feature_matrix_summary_rows([("empty", []), ("active", events)])

    assert [row["matrix_id"] for row in rows] == ["empty", "active"]
    assert rows[0]["row_count"] == 0
    assert rows[0]["first_timestamp"] is None
    assert rows[1]["row_count"] == 1


def test_aspect_event_feature_matrix_summary_rows_rejects_duplicate_matrix_ids():
    ts = datetime(2026, 5, 18, tzinfo=timezone.utc)
    events = [_aspect_event("sun", "jupiter", "conjunction", ts)]

    with pytest.raises(ValueError, match="matrix IDs must be unique"):
        aspect_event_feature_matrix_summary_rows([("train", events), ("train", events)])


def test_aspect_event_feature_matrix_summary_rows_rejects_blank_matrix_ids():
    with pytest.raises(ValueError, match="matrix ID must be a non-blank string"):
        aspect_event_feature_matrix_summary_rows([("   ", [])])


def test_aspect_event_feature_matrix_summary_rows_rejects_non_string_matrix_ids():
    with pytest.raises(ValueError, match="matrix ID must be a non-blank string"):
        aspect_event_feature_matrix_summary_rows([(42, [])])


def test_aspect_event_feature_matrix_summary_rows_accepts_shared_configured_feature_keys():
    ts = datetime(2026, 5, 18, tzinfo=timezone.utc)
    events = [_aspect_event("sun", "jupiter", "conjunction", ts)]

    rows = aspect_event_feature_matrix_summary_rows(
        {"train": events, "test": []},
        ["sun_jupiter_conjunction", "mars_saturn_square"],
    )

    assert [row["configured_feature_count"] for row in rows] == [2, 2]
    assert [row["duplicate_configured_feature_count"] for row in rows] == [0, 0]


def test_aspect_event_feature_matrix_summary_rows_rejects_non_string_shared_configured_feature_keys():
    with pytest.raises(ValueError, match="configured aspect feature keys must be non-blank strings"):
        aspect_event_feature_matrix_summary_rows(
            {"train": []},
            ["sun_jupiter_conjunction", 42],
        )


def test_aspect_event_feature_matrix_summary_rows_accepts_per_matrix_configured_feature_keys():
    ts = datetime(2026, 5, 18, tzinfo=timezone.utc)
    events = [_aspect_event("sun", "jupiter", "conjunction", ts)]

    rows = aspect_event_feature_matrix_summary_rows(
        [("train", events), ("test", [])],
        [("train", ["sun_jupiter_conjunction"]), ("test", ["sun_jupiter_conjunction", "mars_saturn_square"])],
    )

    assert [row["configured_feature_count"] for row in rows] == [1, 2]


def test_aspect_event_feature_matrix_summary_rows_rejects_non_string_per_matrix_configured_feature_keys():
    with pytest.raises(ValueError, match="configured aspect feature keys must be non-blank strings"):
        aspect_event_feature_matrix_summary_rows(
            [("train", [])],
            [("train", ["sun_jupiter_conjunction", 42])],
        )


def test_aspect_event_feature_matrix_summary_rows_rejects_duplicate_configured_matrix_ids():
    with pytest.raises(ValueError, match="configured matrix IDs must be unique"):
        aspect_event_feature_matrix_summary_rows(
            [("train", [])],
            [("train", ["sun_jupiter_conjunction"]), ("train", ["mars_saturn_square"])],
        )


def test_aspect_event_feature_matrix_summary_rows_rejects_blank_configured_matrix_ids():
    with pytest.raises(ValueError, match="configured matrix ID must be a non-blank string"):
        aspect_event_feature_matrix_summary_rows(
            [("train", [])],
            [("   ", ["sun_jupiter_conjunction"])],
        )


def test_aspect_event_feature_matrix_summary_rows_rejects_non_string_configured_matrix_ids():
    with pytest.raises(ValueError, match="configured matrix ID must be a non-blank string"):
        aspect_event_feature_matrix_summary_rows(
            [("train", [])],
            [(42, ["sun_jupiter_conjunction"])],
        )


def test_aspect_event_feature_matrix_summary_rows_rejects_non_string_configured_mapping_ids():
    with pytest.raises(ValueError, match="configured matrix ID must be a non-blank string"):
        aspect_event_feature_matrix_summary_rows(
            [("train", [])],
            {42: ["sun_jupiter_conjunction"]},
        )


def test_aspect_event_feature_matrix_summary_rows_is_csv_compatible():
    ts = datetime(2026, 5, 18, tzinfo=timezone.utc)
    rows = aspect_event_feature_matrix_summary_rows(
        [("train", [_aspect_event("sun", "jupiter", "conjunction", ts)]), ("test", [])],
        ["sun_jupiter_conjunction"],
    )

    text = to_csv(rows)

    assert text.splitlines()[0] == (
        "matrix_id,row_count,timestamp_count,observed_feature_count,configured_feature_count,"
        "duplicate_configured_feature_count,missing_timestamp_count,event_count,"
        "first_timestamp,last_timestamp"
    )
    assert "train,1,1,1,1,0,0,1,2026-05-18T00:00:00+00:00" in text
    assert "test,0,0,0,1,0,0,0,," in text


def _aspect_event(
    body_a: object,
    body_b: object,
    aspect: object,
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
