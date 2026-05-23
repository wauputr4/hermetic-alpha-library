from datetime import datetime, timezone

import pytest

from hermetic_alpha.models import PlanetPosition

from hermetic_alpha.astro import (
    aspect_scan_event_group_rows,
    aspect_scan_summary_row,
    aspect_scan_summary_rows,
    circular_distance,
    detect_aspect,
    find_aspects,
    scan_aspect_series,
)


def test_circular_distance_wraps_zero_boundary():
    assert circular_distance(359, 1) == 2


def test_detect_conjunction_with_strength():
    event = detect_aspect("sun", 10, "jupiter", 12, "conjunction", 3)
    assert event is not None
    assert event.orb == 2
    assert round(event.strength, 4) == round(1 / 3, 4)


def test_find_aspects_between_bodies():
    events = find_aspects({"sun": 0, "jupiter": 1, "mars": 90}, {"conjunction": 3, "square": 3})
    assert {(e.body_a, e.body_b, e.aspect) for e in events} == {
        ("sun", "jupiter", "conjunction"),
        ("sun", "mars", "square"),
        ("jupiter", "mars", "square"),
    }


def test_find_aspects_supports_exact_orb_zero():
    events = find_aspects({"sun": 0, "jupiter": 0}, {"conjunction": 0})

    assert len(events) == 1
    event = events[0]
    assert event.aspect == "conjunction"
    assert event.orb == 0
    assert event.strength == 1.0


def test_find_aspects_supports_float_tolerance_for_exact_orb_zero():
    events = find_aspects({"sun": 10.1, "jupiter": 70.1}, {"sextile": 0})

    assert len(events) == 1
    event = events[0]
    assert event.aspect == "sextile"
    assert event.orb == 0
    assert event.strength == 1.0


def test_detect_aspect_preserves_timestamp():
    ts = datetime(2026, 5, 6, tzinfo=timezone.utc)
    event = detect_aspect("sun", 10, "jupiter", 12, "conjunction", 3, timestamp=ts)
    assert event is not None
    assert event.timestamp == ts


def test_find_aspects_propagates_planet_position_timestamp():
    ts = datetime(2026, 5, 6, tzinfo=timezone.utc)
    events = find_aspects({
        "sun": PlanetPosition(ts, "sun", 0),
        "jupiter": PlanetPosition(ts, "jupiter", 1),
    }, {"conjunction": 3})
    assert len(events) == 1
    assert events[0].timestamp == ts


def test_raw_float_aspects_keep_unknown_phase():
    event = detect_aspect("sun", 10, "jupiter", 12, "conjunction", 3)

    assert event is not None
    assert event.phase == "unknown"


def test_exact_aspect_returns_exact_phase_without_speed_data():
    event = detect_aspect("sun", 10.1, "jupiter", 70.1, "sextile", 0)

    assert event is not None
    assert event.phase == "exact"


def test_find_aspects_classifies_applying_conjunction_from_position_speeds():
    ts = datetime(2026, 5, 6, tzinfo=timezone.utc)

    events = find_aspects({
        "sun": PlanetPosition(ts, "sun", 10, speed=1.0),
        "jupiter": PlanetPosition(ts, "jupiter", 12, speed=-0.5),
    }, {"conjunction": 3})

    assert len(events) == 1
    assert events[0].phase == "applying"


def test_find_aspects_classifies_separating_conjunction_from_position_speeds():
    ts = datetime(2026, 5, 6, tzinfo=timezone.utc)

    events = find_aspects({
        "sun": PlanetPosition(ts, "sun", 10, speed=-1.0),
        "jupiter": PlanetPosition(ts, "jupiter", 12, speed=0.5),
    }, {"conjunction": 3})

    assert len(events) == 1
    assert events[0].phase == "separating"


def test_find_aspects_classifies_non_zero_target_with_negative_speed():
    ts = datetime(2026, 5, 6, tzinfo=timezone.utc)

    events = find_aspects({
        "sun": PlanetPosition(ts, "sun", 10, speed=-1.0),
        "mars": PlanetPosition(ts, "mars", 98, speed=0.0),
    }, {"square": 3})

    assert len(events) == 1
    assert events[0].phase == "applying"


def test_find_aspects_preserves_unknown_phase_when_position_speed_is_missing():
    ts = datetime(2026, 5, 6, tzinfo=timezone.utc)

    events = find_aspects({
        "sun": PlanetPosition(ts, "sun", 10, speed=1.0),
        "jupiter": PlanetPosition(ts, "jupiter", 12),
    }, {"conjunction": 3})

    assert len(events) == 1
    assert events[0].phase == "unknown"


def test_scan_aspect_series_groups_by_timestamp_without_mixing_positions():
    ts1 = datetime(2026, 5, 6, tzinfo=timezone.utc)
    ts2 = datetime(2026, 5, 7, tzinfo=timezone.utc)

    events = scan_aspect_series(
        [
            PlanetPosition(ts2, "sun", 0),
            PlanetPosition(ts1, "mars", 90),
            PlanetPosition(ts1, "sun", 0),
            PlanetPosition(ts2, "mars", 120),
            PlanetPosition(ts2, "venus", 180),
        ],
        {"square": 3, "trine": 3, "opposition": 3},
    )

    assert [(event.timestamp, event.body_a, event.body_b, event.aspect) for event in events] == [
        (ts1, "mars", "sun", "square"),
        (ts2, "mars", "sun", "trine"),
        (ts2, "sun", "venus", "opposition"),
    ]


def test_scan_aspect_series_scans_only_bodies_present_at_each_timestamp():
    ts1 = datetime(2026, 5, 6, tzinfo=timezone.utc)
    ts2 = datetime(2026, 5, 7, tzinfo=timezone.utc)

    events = scan_aspect_series(
        [
            PlanetPosition(ts1, "sun", 0),
            PlanetPosition(ts1, "mars", 90),
            PlanetPosition(ts2, "sun", 0),
        ],
        {"square": 3},
    )

    assert len(events) == 1
    assert events[0].timestamp == ts1
    assert (events[0].body_a, events[0].body_b, events[0].aspect) == ("mars", "sun", "square")


def test_scan_aspect_series_empty_input_returns_no_events():
    assert scan_aspect_series([]) == []


@pytest.mark.parametrize(
    ("positions", "message"),
    [
        ([object()], "PlanetPosition"),
        ([PlanetPosition(datetime(2026, 5, 6), "sun", 0)], "timezone-aware"),
        ([PlanetPosition(datetime(2026, 5, 6, tzinfo=timezone.utc), "", 0)], "body must not be empty"),
        (
            [
                PlanetPosition(datetime(2026, 5, 6, tzinfo=timezone.utc), "sun", 0),
                PlanetPosition(datetime(2026, 5, 6, tzinfo=timezone.utc), "sun", 1),
            ],
            "duplicate position",
        ),
    ],
)
def test_scan_aspect_series_rejects_invalid_position_rows(positions, message):
    with pytest.raises(ValueError, match=message):
        scan_aspect_series(positions)


def test_aspect_scan_summary_row_reports_counts_and_boundaries():
    ts1 = datetime(2026, 5, 6, tzinfo=timezone.utc)
    ts2 = datetime(2026, 5, 7, tzinfo=timezone.utc)
    events = [
        detect_aspect("sun", 10, "jupiter", 12, "conjunction", 3, timestamp=ts2, speed_a=1, speed_b=-0.5),
        detect_aspect("mars", 90, "saturn", 181, "square", 3, timestamp=ts1, speed_a=-1, speed_b=0.5),
        detect_aspect("moon", 0, "venus", 0, "conjunction", 0, timestamp=ts1),
        detect_aspect("sun", 10, "jupiter", 12, "conjunction", 3, timestamp=ts1),
    ]

    row = aspect_scan_summary_row([event for event in events if event is not None])

    assert row == {
        "event_count": 4,
        "timestamp_count": 2,
        "unique_aspect_count": 2,
        "unique_body_pair_count": 3,
        "applying_phase_count": 1,
        "separating_phase_count": 1,
        "exact_phase_count": 1,
        "unknown_phase_count": 1,
        "missing_timestamp_count": 0,
        "first_timestamp": ts1,
        "last_timestamp": ts2,
    }


def test_aspect_scan_summary_row_handles_empty_results():
    assert aspect_scan_summary_row([]) == {
        "event_count": 0,
        "timestamp_count": 0,
        "unique_aspect_count": 0,
        "unique_body_pair_count": 0,
        "applying_phase_count": 0,
        "separating_phase_count": 0,
        "exact_phase_count": 0,
        "unknown_phase_count": 0,
        "missing_timestamp_count": 0,
        "first_timestamp": None,
        "last_timestamp": None,
    }


def test_aspect_scan_summary_row_counts_missing_timestamps_from_raw_longitudes():
    ts = datetime(2026, 5, 6, tzinfo=timezone.utc)
    events = [
        *find_aspects({"sun": 0, "jupiter": 1}, {"conjunction": 3}),
        *find_aspects({"mars": PlanetPosition(ts, "mars", 90), "saturn": 180}, {"square": 3}),
    ]

    row = aspect_scan_summary_row(events)

    assert row["event_count"] == 2
    assert row["timestamp_count"] == 0
    assert row["missing_timestamp_count"] == 2
    assert row["first_timestamp"] is None
    assert row["last_timestamp"] is None


def test_aspect_scan_summary_rows_preserves_ordered_mapping_order():
    ts1 = datetime(2026, 5, 6, tzinfo=timezone.utc)
    ts2 = datetime(2026, 5, 7, tzinfo=timezone.utc)
    first = find_aspects(
        {"sun": PlanetPosition(ts1, "sun", 0), "jupiter": PlanetPosition(ts1, "jupiter", 1)},
        {"conjunction": 3},
    )
    second = find_aspects(
        {"mars": PlanetPosition(ts2, "mars", 90), "saturn": PlanetPosition(ts2, "saturn", 181)},
        {"square": 3},
    )

    rows = aspect_scan_summary_rows({"sun-jupiter": first, "mars-saturn": second})

    assert [row["scan_id"] for row in rows] == ["sun-jupiter", "mars-saturn"]
    assert [row["first_timestamp"] for row in rows] == [ts1, ts2]


def test_aspect_scan_summary_rows_accepts_ordered_pairs_and_empty_events():
    ts = datetime(2026, 5, 6, tzinfo=timezone.utc)
    events = find_aspects(
        {"sun": PlanetPosition(ts, "sun", 0), "jupiter": PlanetPosition(ts, "jupiter", 1)},
        {"conjunction": 3},
    )

    rows = aspect_scan_summary_rows([("empty-scan", []), ("active-scan", events)])

    assert [row["scan_id"] for row in rows] == ["empty-scan", "active-scan"]
    assert [row["event_count"] for row in rows] == [0, 1]
    assert rows[0]["first_timestamp"] is None


def test_aspect_scan_summary_rows_rejects_duplicate_scan_ids():
    events = find_aspects({"sun": 0, "jupiter": 1}, {"conjunction": 3})

    with pytest.raises(ValueError, match="scan IDs must be unique"):
        aspect_scan_summary_rows([("scan-a", events), ("scan-a", events)])


def test_aspect_scan_summary_rows_rejects_blank_scan_ids():
    events = find_aspects({"sun": 0, "jupiter": 1}, {"conjunction": 3})

    with pytest.raises(ValueError, match="scan ID must be a non-blank string"):
        aspect_scan_summary_rows([("   ", events)])


def test_aspect_scan_summary_rows_rejects_non_string_scan_ids():
    events = find_aspects({"sun": 0, "jupiter": 1}, {"conjunction": 3})

    with pytest.raises(ValueError, match="scan ID must be a non-blank string"):
        aspect_scan_summary_rows([(42, events)])


def test_aspect_scan_event_group_rows_preserves_ordered_mapping_order():
    ts1 = datetime(2026, 5, 6, tzinfo=timezone.utc)
    ts2 = datetime(2026, 5, 7, tzinfo=timezone.utc)
    first = find_aspects(
        {"sun": PlanetPosition(ts1, "sun", 0), "jupiter": PlanetPosition(ts1, "jupiter", 1)},
        {"conjunction": 3},
    )
    second = find_aspects(
        {"mars": PlanetPosition(ts2, "mars", 90), "saturn": PlanetPosition(ts2, "saturn", 181)},
        {"square": 3},
    )

    rows = aspect_scan_event_group_rows({"sun-jupiter": first, "mars-saturn": second})

    assert [row["scan_id"] for row in rows] == ["sun-jupiter", "mars-saturn"]
    assert [row["timestamp"] for row in rows] == [ts1.isoformat(), ts2.isoformat()]
    assert [(row["body_a"], row["body_b"], row["aspect"]) for row in rows] == [
        ("sun", "jupiter", "conjunction"),
        ("mars", "saturn", "square"),
    ]


def test_aspect_scan_event_group_rows_accepts_pairs_and_skips_empty_groups():
    ts = datetime(2026, 5, 6, tzinfo=timezone.utc)
    events = find_aspects(
        {"sun": PlanetPosition(ts, "sun", 0), "jupiter": PlanetPosition(ts, "jupiter", 1)},
        {"conjunction": 3},
    )

    rows = aspect_scan_event_group_rows([("empty-scan", []), ("active-scan", events)])

    assert [row["scan_id"] for row in rows] == ["active-scan"]
    assert rows[0]["timestamp"] == ts.isoformat()


def test_aspect_scan_event_group_rows_rejects_duplicate_scan_ids():
    events = find_aspects({"sun": 0, "jupiter": 1}, {"conjunction": 3})

    with pytest.raises(ValueError, match="scan IDs must be unique"):
        aspect_scan_event_group_rows([("scan-a", events), ("scan-a", events)])


def test_aspect_scan_event_group_rows_rejects_blank_scan_ids():
    events = find_aspects({"sun": 0, "jupiter": 1}, {"conjunction": 3})

    with pytest.raises(ValueError, match="scan ID must be a non-blank string"):
        aspect_scan_event_group_rows([("   ", events)])


def test_aspect_scan_event_group_rows_rejects_non_string_scan_ids():
    events = find_aspects({"sun": 0, "jupiter": 1}, {"conjunction": 3})

    with pytest.raises(ValueError, match="scan ID must be a non-blank string"):
        aspect_scan_event_group_rows([(42, events)])
