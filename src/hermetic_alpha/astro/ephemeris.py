"""Optional ephemeris adapters for planetary position calculations."""

from __future__ import annotations

from datetime import datetime, timezone
from types import ModuleType
from typing import Any

from hermetic_alpha.models import PlanetPosition

from .math import normalize_degrees


class EphemerisBackendUnavailable(RuntimeError):
    """Raised when an optional ephemeris backend is not installed."""


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

    @staticmethod
    def _extract_position_values(raw_result: Any) -> tuple[float, ...]:
        if not isinstance(raw_result, tuple) or not raw_result:
            raise ValueError("Unexpected pyswisseph calc_ut result")
        values = raw_result[0] if isinstance(raw_result[0], tuple) else raw_result
        if not isinstance(values, tuple) or len(values) < 2:
            raise ValueError("Unexpected pyswisseph position payload")
        return tuple(float(value) for value in values)
