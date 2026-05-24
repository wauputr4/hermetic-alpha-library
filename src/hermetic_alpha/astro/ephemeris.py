"""Optional ephemeris adapters for planetary position calculations."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timedelta, timezone
from types import ModuleType
from typing import Any, Protocol

from hermetic_alpha.models import PlanetPosition

from .math import normalize_degrees


class EphemerisBackendUnavailable(RuntimeError):
    """Raised when an optional ephemeris backend is not installed."""


class EphemerisAdapter(Protocol):
    """Minimal protocol for objects that can calculate planetary positions."""

    def position(self, timestamp: datetime, body: str) -> PlanetPosition:
        """Return a planetary position for a timezone-aware timestamp."""


BODY_IDS: dict[str, str] = {
    "sun": "SUN",
    "moon": "MOON",
    "mercury": "MERCURY",
    "venus": "VENUS",
    "mars": "MARS",
    "jupiter": "JUPITER",
    "saturn": "SATURN",
    "uranus": "URANUS",
    "neptune": "NEPTUNE",
    "pluto": "PLUTO",
}


def _require_aware_datetime(timestamp: datetime) -> datetime:
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return timestamp.astimezone(timezone.utc)


def _decimal_utc_hour(timestamp: datetime) -> float:
    return (
        timestamp.hour
        + (timestamp.minute / 60)
        + (timestamp.second / 3600)
        + (timestamp.microsecond / 3_600_000_000)
    )


def generate_planet_positions(
    adapter: EphemerisAdapter,
    start: datetime,
    end: datetime,
    step: timedelta,
    bodies: Sequence[str],
) -> list[PlanetPosition]:
    """Generate positions ordered by timestamp and caller-supplied body order."""
    _require_aware_datetime(start)
    _require_aware_datetime(end)
    if end < start:
        raise ValueError("end must be greater than or equal to start")
    if step <= timedelta(0):
        raise ValueError("step must be positive")
    if not bodies:
        raise ValueError("bodies must not be empty")

    positions: list[PlanetPosition] = []
    timestamp = start
    while timestamp <= end:
        for body in bodies:
            positions.append(adapter.position(timestamp, body))
        timestamp += step
    return positions


def planet_position_series_summary_row(
    positions: Sequence[PlanetPosition],
    *,
    series_id: str | None = None,
) -> dict[str, object]:
    """Return compact metadata for a generated planet-position series.

    The summary is intended for ephemeris-run audit tables before aspect
    scanning or vector encoding. It does not replace raw position rows or
    similarity vector summaries.
    """
    timestamps = [position.timestamp for position in positions]
    engines = {position.engine for position in positions if position.engine is not None}
    zodiacs = {position.zodiac for position in positions}

    return {
        "series_id": series_id,
        "position_count": len(positions),
        "timestamp_count": len(set(timestamps)),
        "unique_body_count": len({position.body for position in positions}),
        "unique_engine_count": len(engines),
        "unique_zodiac_count": len(zodiacs),
        "missing_speed_count": sum(1 for position in positions if position.speed is None),
        "missing_retrograde_count": sum(1 for position in positions if position.retrograde is None),
        "first_timestamp": min(timestamps) if timestamps else None,
        "last_timestamp": max(timestamps) if timestamps else None,
    }


def planet_position_series_summary_rows(
    series: Mapping[str, Sequence[PlanetPosition]] | Sequence[tuple[str, Sequence[PlanetPosition]]],
) -> list[dict[str, object]]:
    """Return ordered compact metadata rows for several planet-position series."""
    rows: list[dict[str, object]] = []
    seen_series_ids: set[str] = set()
    for series_id, positions in _iter_named_position_series(series):
        _validate_series_id(series_id)
        if series_id in seen_series_ids:
            raise ValueError("series IDs must be unique")
        seen_series_ids.add(series_id)
        rows.append(planet_position_series_summary_row(positions, series_id=series_id))
    return rows


def _iter_named_position_series(
    series: Mapping[str, Sequence[PlanetPosition]] | Sequence[tuple[str, Sequence[PlanetPosition]]],
) -> Iterable[tuple[str, Sequence[PlanetPosition]]]:
    if isinstance(series, Mapping):
        yield from series.items()
        return
    yield from series


def _validate_series_id(series_id: Any) -> None:
    if not isinstance(series_id, str):
        raise ValueError("series ID must be a string")
    if not series_id.strip():
        raise ValueError("series ID must not be blank")


def _import_swisseph() -> ModuleType:
    try:
        import swisseph  # type: ignore[import-not-found]
    except ImportError as exc:
        raise EphemerisBackendUnavailable(
            "pyswisseph is optional; install hermetic-alpha[ephemeris] to use SwissEphemerisAdapter"
        ) from exc
    return swisseph


class SwissEphemerisAdapter:
    """Hermetic Alpha wrapper around optional pyswisseph calculations."""

    engine_name = "pyswisseph"

    def __init__(self, ephemeris_path: str | None = None, backend: ModuleType | None = None) -> None:
        self._backend = backend or _import_swisseph()
        if ephemeris_path is not None:
            self._backend.set_ephe_path(ephemeris_path)

    @property
    def backend_version(self) -> str | None:
        return getattr(self._backend, "__version__", None)

    def position(self, timestamp: datetime, body: str) -> PlanetPosition:
        """Return a planetary position for a timezone-aware timestamp."""
        utc_timestamp = _require_aware_datetime(timestamp)
        body_key = body.lower()
        body_id_name = BODY_IDS.get(body_key)
        if body_id_name is None:
            supported = ", ".join(sorted(BODY_IDS))
            raise ValueError(f"Unsupported body: {body}. Supported bodies: {supported}")

        body_id = getattr(self._backend, body_id_name)
        flags = getattr(self._backend, "FLG_SWIEPH", 0) | getattr(self._backend, "FLG_SPEED", 0)
        julian_day = self._backend.julday(
            utc_timestamp.year,
            utc_timestamp.month,
            utc_timestamp.day,
            _decimal_utc_hour(utc_timestamp),
        )
        raw_result = self._backend.calc_ut(julian_day, body_id, flags)
        self._raise_for_calc_error(raw_result)
        values = self._extract_position_values(raw_result)
        speed = values[3] if len(values) > 3 else None

        return PlanetPosition(
            timestamp=utc_timestamp,
            body=body_key,
            longitude=normalize_degrees(values[0]),
            latitude=values[1] if len(values) > 1 else None,
            speed=speed,
            retrograde=(speed < 0) if speed is not None else None,
            zodiac="tropical",
            engine=self.engine_name,
        )

    def _raise_for_calc_error(self, raw_result: Any) -> None:
        if (
            isinstance(raw_result, tuple)
            and len(raw_result) >= 2
            and isinstance(raw_result[-1], int)
            and raw_result[-1] < 0
        ):
            get_errmsg = getattr(self._backend, "get_errmsg", None)
            message = get_errmsg() if callable(get_errmsg) else f"error code {raw_result[-1]}"
            raise ValueError(f"pyswisseph calc_ut error: {message}")

    @staticmethod
    def _extract_position_values(raw_result: Any) -> tuple[float, ...]:
        if not isinstance(raw_result, tuple) or not raw_result:
            raise ValueError("Unexpected pyswisseph calc_ut result")
        values = raw_result[0] if isinstance(raw_result[0], tuple) else raw_result
        if not isinstance(values, tuple) or len(values) < 2:
            raise ValueError("Unexpected pyswisseph position payload")
        return tuple(float(value) for value in values)
