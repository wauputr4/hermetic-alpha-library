from datetime import datetime, timezone, timedelta

import pytest

from hermetic_alpha.astro.ephemeris import (
    BODY_IDS,
    EphemerisBackendUnavailable,
    SwissEphemerisAdapter,
    _import_swisseph,
    generate_planet_positions,
    planet_position_series_summary_row,
)
from hermetic_alpha.models import PlanetPosition


class FakeSwissEph:
    __version__ = "test"

    SUN = 0
    MARS = 4
    FLG_SWIEPH = 2
    FLG_SPEED = 256

    def __init__(self):
        self.ephemeris_path = None
        self.julian_args = None
        self.calc_args = None

    def set_ephe_path(self, path):
        self.ephemeris_path = path

    def julday(self, year, month, day, hour):
        self.julian_args = (year, month, day, hour)
        return 2460000.5

    def calc_ut(self, julian_day, body_id, flags):
        self.calc_args = (julian_day, body_id, flags)
        return ((361.25, -0.5, 1.0, -0.02, 0.0, 0.0), 0)


class FailingSwissEph(FakeSwissEph):
    def calc_ut(self, julian_day, body_id, flags):
        self.calc_args = (julian_day, body_id, flags)
        return ((0.0, 0.0, 0.0, 0.0, 0.0, 0.0), -1)

    def get_errmsg(self):
        return "missing ephemeris data"


class RecordingAdapter:
    def __init__(self):
        self.calls = []

    def position(self, timestamp, body):
        self.calls.append((timestamp, body))
        return PlanetPosition(
            timestamp=timestamp.astimezone(timezone.utc),
            body=body.lower(),
            longitude=len(self.calls),
            engine="fake",
        )


def test_generate_planet_positions_orders_timestamps_then_supplied_body_order():
    adapter = RecordingAdapter()
    start = datetime(2026, 5, 8, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 5, 10, 0, 0, tzinfo=timezone.utc)

    positions = generate_planet_positions(
        adapter,
        start=start,
        end=end,
        step=timedelta(days=1),
        bodies=["mars", "sun"],
    )

    assert adapter.calls == [
        (datetime(2026, 5, 8, tzinfo=timezone.utc), "mars"),
        (datetime(2026, 5, 8, tzinfo=timezone.utc), "sun"),
        (datetime(2026, 5, 9, tzinfo=timezone.utc), "mars"),
        (datetime(2026, 5, 9, tzinfo=timezone.utc), "sun"),
        (datetime(2026, 5, 10, tzinfo=timezone.utc), "mars"),
        (datetime(2026, 5, 10, tzinfo=timezone.utc), "sun"),
    ]
    assert [(position.timestamp, position.body) for position in positions] == [
        (datetime(2026, 5, 8, tzinfo=timezone.utc), "mars"),
        (datetime(2026, 5, 8, tzinfo=timezone.utc), "sun"),
        (datetime(2026, 5, 9, tzinfo=timezone.utc), "mars"),
        (datetime(2026, 5, 9, tzinfo=timezone.utc), "sun"),
        (datetime(2026, 5, 10, tzinfo=timezone.utc), "mars"),
        (datetime(2026, 5, 10, tzinfo=timezone.utc), "sun"),
    ]


def test_generate_planet_positions_includes_exact_end_boundary_only():
    adapter = RecordingAdapter()

    positions = generate_planet_positions(
        adapter,
        start=datetime(2026, 5, 8, tzinfo=timezone.utc),
        end=datetime(2026, 5, 9, 12, tzinfo=timezone.utc),
        step=timedelta(days=1),
        bodies=["sun"],
    )

    assert [position.timestamp for position in positions] == [
        datetime(2026, 5, 8, tzinfo=timezone.utc),
        datetime(2026, 5, 9, tzinfo=timezone.utc),
    ]


def test_generate_planet_positions_accepts_timezone_aware_range():
    adapter = RecordingAdapter()
    wib = timezone(timedelta(hours=7))

    positions = generate_planet_positions(
        adapter,
        start=datetime(2026, 5, 8, 7, tzinfo=wib),
        end=datetime(2026, 5, 8, 7, tzinfo=wib),
        step=timedelta(days=1),
        bodies=["sun"],
    )

    assert adapter.calls == [(datetime(2026, 5, 8, 7, tzinfo=wib), "sun")]
    assert positions[0].timestamp == datetime(2026, 5, 8, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    ("start", "end", "step", "bodies", "message"),
    [
        (
            datetime(2026, 5, 8),
            datetime(2026, 5, 9, tzinfo=timezone.utc),
            timedelta(days=1),
            ["sun"],
            "timezone-aware",
        ),
        (
            datetime(2026, 5, 8, tzinfo=timezone.utc),
            datetime(2026, 5, 7, tzinfo=timezone.utc),
            timedelta(days=1),
            ["sun"],
            "end must be greater than or equal to start",
        ),
        (
            datetime(2026, 5, 8, tzinfo=timezone.utc),
            datetime(2026, 5, 9, tzinfo=timezone.utc),
            timedelta(0),
            ["sun"],
            "step must be positive",
        ),
        (
            datetime(2026, 5, 8, tzinfo=timezone.utc),
            datetime(2026, 5, 9, tzinfo=timezone.utc),
            timedelta(days=1),
            [],
            "bodies must not be empty",
        ),
    ],
)
def test_generate_planet_positions_rejects_invalid_inputs(start, end, step, bodies, message):
    with pytest.raises(ValueError, match=message):
        generate_planet_positions(RecordingAdapter(), start, end, step, bodies)


def test_planet_position_series_summary_row_reports_generated_position_metadata():
    adapter = RecordingAdapter()
    start = datetime(2026, 5, 8, tzinfo=timezone.utc)
    end = datetime(2026, 5, 9, tzinfo=timezone.utc)
    positions = generate_planet_positions(
        adapter,
        start=start,
        end=end,
        step=timedelta(days=1),
        bodies=["mars", "sun"],
    )

    row = planet_position_series_summary_row(positions, series_id="btc-daily")

    assert row == {
        "series_id": "btc-daily",
        "position_count": 4,
        "timestamp_count": 2,
        "unique_body_count": 2,
        "unique_engine_count": 1,
        "unique_zodiac_count": 1,
        "missing_speed_count": 4,
        "missing_retrograde_count": 4,
        "first_timestamp": start,
        "last_timestamp": end,
    }


def test_planet_position_series_summary_row_handles_empty_positions():
    assert planet_position_series_summary_row([]) == {
        "series_id": None,
        "position_count": 0,
        "timestamp_count": 0,
        "unique_body_count": 0,
        "unique_engine_count": 0,
        "unique_zodiac_count": 0,
        "missing_speed_count": 0,
        "missing_retrograde_count": 0,
        "first_timestamp": None,
        "last_timestamp": None,
    }


def test_planet_position_series_summary_row_counts_mixed_metadata():
    ts1 = datetime(2026, 5, 8, tzinfo=timezone.utc)
    ts2 = datetime(2026, 5, 9, tzinfo=timezone.utc)
    positions = [
        PlanetPosition(ts2, "sun", 10, speed=1.0, retrograde=False, zodiac="tropical", engine="fake-a"),
        PlanetPosition(ts1, "moon", 20, speed=None, retrograde=None, zodiac="sidereal", engine="fake-b"),
        PlanetPosition(ts1, "sun", 30, speed=-0.5, retrograde=True, zodiac="sidereal", engine=None),
    ]

    row = planet_position_series_summary_row(positions)

    assert row["position_count"] == 3
    assert row["timestamp_count"] == 2
    assert row["unique_body_count"] == 2
    assert row["unique_engine_count"] == 2
    assert row["unique_zodiac_count"] == 2
    assert row["missing_speed_count"] == 1
    assert row["missing_retrograde_count"] == 1
    assert row["first_timestamp"] == ts1
    assert row["last_timestamp"] == ts2


def test_swiss_ephemeris_adapter_returns_normalized_planet_position():
    backend = FakeSwissEph()
    adapter = SwissEphemerisAdapter(ephemeris_path="/tmp/ephe", backend=backend)

    timestamp = datetime(2026, 5, 8, 12, 30, tzinfo=timezone.utc)
    position = adapter.position(timestamp, "Sun")

    assert position.timestamp == timestamp
    assert position.body == "sun"
    assert position.longitude == 1.25
    assert position.latitude == -0.5
    assert position.speed == -0.02
    assert position.retrograde is True
    assert position.engine == "pyswisseph"
    assert adapter.backend_version == "test"
    assert backend.ephemeris_path == "/tmp/ephe"
    assert backend.julian_args == (2026, 5, 8, 12.5)
    assert backend.calc_args == (2460000.5, backend.SUN, backend.FLG_SWIEPH | backend.FLG_SPEED)


def test_swiss_ephemeris_adapter_converts_aware_timezones_to_utc():
    backend = FakeSwissEph()
    adapter = SwissEphemerisAdapter(backend=backend)

    timestamp = datetime(2026, 5, 8, 19, 30, tzinfo=timezone(timedelta(hours=7)))
    position = adapter.position(timestamp, "mars")

    assert position.timestamp == datetime(2026, 5, 8, 12, 30, tzinfo=timezone.utc)
    assert backend.julian_args == (2026, 5, 8, 12.5)
    assert backend.calc_args[1] == backend.MARS


def test_swiss_ephemeris_adapter_rejects_naive_timestamps():
    adapter = SwissEphemerisAdapter(backend=FakeSwissEph())

    with pytest.raises(ValueError, match="timezone-aware"):
        adapter.position(datetime(2026, 5, 8, 12, 30), "sun")


def test_swiss_ephemeris_adapter_rejects_unsupported_body():
    adapter = SwissEphemerisAdapter(backend=FakeSwissEph())

    with pytest.raises(ValueError, match="Unsupported body"):
        adapter.position(datetime(2026, 5, 8, tzinfo=timezone.utc), "ceres")


def test_swiss_ephemeris_adapter_rejects_negative_calc_status():
    adapter = SwissEphemerisAdapter(backend=FailingSwissEph())

    with pytest.raises(ValueError, match="pyswisseph calc_ut error: missing ephemeris data"):
        adapter.position(datetime(2026, 5, 8, tzinfo=timezone.utc), "sun")


def test_body_id_map_includes_major_research_bodies():
    assert {"sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"}.issubset(BODY_IDS)


def test_optional_swisseph_import_reports_install_extra(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "swisseph":
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(EphemerisBackendUnavailable, match=r"hermetic-alpha\[ephemeris\]"):
        _import_swisseph()
