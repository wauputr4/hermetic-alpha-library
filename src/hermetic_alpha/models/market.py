"""Market and analysis domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(frozen=True)
class MarketCandle:
    """Normalized OHLCV candle."""

    timestamp: datetime
    asset: str
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
    interval: str = "1d"
    source: str | None = None

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass(frozen=True)
class MarketLabel:
    """Market outcome label for one timestamp and horizon."""

    timestamp: datetime
    asset: str
    horizon: int
    forward_return: float | None
    bullish: bool | None
    local_top: bool | None = None
    local_bottom: bool | None = None

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass(frozen=True)
class EventStudyResult:
    """Summary of market behavior after selected astro events."""

    events: int
    horizon: int
    baseline_bullish_probability: float | None
    conditional_bullish_probability: float | None
    average_return: float | None
    median_return: float | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
