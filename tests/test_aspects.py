from datetime import datetime, timezone

import pytest

from hermetic_alpha.models import PlanetPosition

from hermetic_alpha.astro import circular_distance, detect_aspect, find_aspects, scan_aspect_series


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
