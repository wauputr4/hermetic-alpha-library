"""Dependency-free local storage helpers for market candles."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

from hermetic_alpha.models import MarketCandle


REQUIRED_CANDLE_FIELDS = ("timestamp", "asset", "open", "high", "low", "close", "interval")


class CandleStorageError(ValueError):
    """Raised when stored candle rows cannot be read as MarketCandle values."""


def write_candles_json(path: str | Path, candles: Iterable[MarketCandle]) -> None:
    """Write non-empty market candles to a local JSON file."""
    rows = [candle.to_dict() for candle in candles]
    if not rows:
        raise CandleStorageError("cannot write an empty candle dataset")

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_candles_json(path: str | Path) -> list[MarketCandle]:
    """Read market candles from a local JSON file."""
    source = Path(path)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CandleStorageError(f"{source} does not contain valid candle JSON") from exc
    except OSError as exc:
        raise CandleStorageError(f"{source} could not be read") from exc

    if not isinstance(payload, list):
        raise CandleStorageError("candle JSON must contain a list of rows")
    if not payload:
        raise CandleStorageError("candle JSON must contain at least one row")

    return [_candle_from_row(row, index) for index, row in enumerate(payload)]


def _candle_from_row(row: Any, index: int) -> MarketCandle:
    if not isinstance(row, dict):
        raise CandleStorageError(f"candle row {index} must be an object")

    missing = [field for field in REQUIRED_CANDLE_FIELDS if field not in row]
    if missing:
        raise CandleStorageError(f"candle row {index} is missing required field(s): {', '.join(missing)}")

    timestamp = _parse_timestamp(row["timestamp"], index)
    volume = row.get("volume")
    return MarketCandle(
        timestamp=timestamp,
        asset=_require_string(row["asset"], "asset", index),
        open=_require_float(row["open"], "open", index),
        high=_require_float(row["high"], "high", index),
        low=_require_float(row["low"], "low", index),
        close=_require_float(row["close"], "close", index),
        volume=None if volume is None else _require_float(volume, "volume", index),
        interval=_require_string(row["interval"], "interval", index),
        source=None if row.get("source") is None else _require_string(row["source"], "source", index),
    )


def _parse_timestamp(value: Any, index: int) -> datetime:
    if not isinstance(value, str):
        raise CandleStorageError(f"candle row {index} timestamp must be an ISO datetime string")
    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CandleStorageError(f"candle row {index} has an invalid timestamp") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise CandleStorageError(f"candle row {index} timestamp must include timezone information")
    return timestamp


def _require_string(value: Any, field: str, index: int) -> str:
    if not isinstance(value, str) or not value:
        raise CandleStorageError(f"candle row {index} field {field} must be a non-empty string")
    return value


def _require_float(value: Any, field: str, index: int) -> float:
    if isinstance(value, bool):
        raise CandleStorageError(f"candle row {index} field {field} must be numeric")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise CandleStorageError(f"candle row {index} field {field} must be numeric") from exc
