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
    }
