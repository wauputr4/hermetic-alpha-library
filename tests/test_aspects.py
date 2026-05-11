from datetime import datetime, timezone

from hermetic_alpha.models import PlanetPosition

from hermetic_alpha.astro import circular_distance, detect_aspect, find_aspects


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
