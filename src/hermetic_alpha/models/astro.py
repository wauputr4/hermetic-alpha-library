"""Astrological domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Literal

ZodiacMode = Literal["tropical", "sidereal"]
AspectPhase = Literal["applying", "separating", "exact", "unknown"]


@dataclass(frozen=True)
class PlanetPosition:
    """Planetary position at a timestamp."""

    timestamp: datetime
    body: str
    longitude: float
    latitude: float | None = None
    speed: float | None = None
    retrograde: bool | None = None
    zodiac: ZodiacMode = "tropical"
    engine: str | None = None

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass(frozen=True)
class AspectDefinition:
    """Configured aspect rule."""

    name: str
    angle: float
    default_orb: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AspectEvent:
    """Detected aspect event between two bodies."""

    body_a: str
    body_b: str
    aspect: str
    target_angle: float
    actual_angle: float
    orb: float
    max_orb: float
    strength: float
    timestamp: datetime | None = None
    phase: AspectPhase = "unknown"

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat() if self.timestamp else None
        return data
