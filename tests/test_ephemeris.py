from datetime import datetime, timezone, timedelta

import pytest

from hermetic_alpha.astro.ephemeris import (
    BODY_IDS,
    EphemerisBackendUnavailable,
    SwissEphemerisAdapter,
    _import_swisseph,
)


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
