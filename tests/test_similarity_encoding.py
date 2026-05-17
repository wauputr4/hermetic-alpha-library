from datetime import datetime, timedelta, timezone
from math import isclose

from hermetic_alpha.models import PlanetPosition
from hermetic_alpha.similarity import encode_longitude, encode_planet_positions


def test_encode_longitude_normalizes_circular_degrees():
    sin_a, cos_a = encode_longitude(359)
    sin_b, cos_b = encode_longitude(-1)

    assert isclose(sin_a, sin_b, abs_tol=1e-12)
    assert isclose(cos_a, cos_b, abs_tol=1e-12)


def test_encode_longitude_keeps_nearby_wraparound_values_close():
    sin_359, cos_359 = encode_longitude(359)
    sin_1, cos_1 = encode_longitude(1)

    distance = ((sin_359 - sin_1) ** 2 + (cos_359 - cos_1) ** 2) ** 0.5
    assert distance < 0.04


def test_encode_planet_positions_uses_stable_timestamp_body_ordering():
    early = datetime(2026, 5, 17, 0, 0, tzinfo=timezone.utc)
    later = datetime(2026, 5, 18, 0, 0, tzinfo=timezone.utc)
    positions = [
        PlanetPosition(later, "moon", 180),
        PlanetPosition(early, "sun", 90),
        PlanetPosition(early, "jupiter", 0),
    ]

    vector = encode_planet_positions(positions)

    assert vector == [
        *encode_longitude(0),
        *encode_longitude(90),
        *encode_longitude(180),
    ]


def test_encode_planet_positions_compares_aware_timestamps_chronologically():
    utc = datetime(2026, 5, 17, 0, 0, tzinfo=timezone.utc)
    same_instant_wib = datetime(
        2026, 5, 17, 7, 0, tzinfo=timezone(timedelta(hours=7))
    )
    positions = [
        PlanetPosition(same_instant_wib, "sun", 90),
        PlanetPosition(utc, "jupiter", 0),
    ]

    vector = encode_planet_positions(positions)

    assert vector == [
        *encode_longitude(0),
        *encode_longitude(90),
    ]
