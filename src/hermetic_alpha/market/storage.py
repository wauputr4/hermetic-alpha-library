"""Dependency-free local storage helpers for market candles."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
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


def candle_dataset_summary_row(
    candles: Sequence[MarketCandle],
    *,
    dataset_id: str | None = None,
) -> dict[str, object]:
    """Return compact flat metadata for a non-empty candle dataset."""

    if not candles:
        raise CandleStorageError("cannot summarize an empty candle dataset")

    assets = {candle.asset for candle in candles}
    if len(assets) != 1:
        raise CandleStorageError("candle dataset summary requires a single asset")

    intervals = {candle.interval for candle in candles}
    if len(intervals) != 1:
        raise CandleStorageError("candle dataset summary requires a single interval")

    sources = {candle.source for candle in candles}
    ordered = sorted(candles, key=lambda candle: candle.timestamp)
    return {
        "dataset_id": dataset_id,
        "candle_count": len(candles),
        "asset": ordered[0].asset,
        "interval": ordered[0].interval,
        "source": ordered[0].source if len(sources) == 1 else None,
        "first_timestamp": ordered[0].timestamp,
        "last_timestamp": ordered[-1].timestamp,
    }


def candle_dataset_summary_rows(
    datasets: Mapping[str, Sequence[MarketCandle]] | Sequence[tuple[str, Sequence[MarketCandle]]],
) -> list[dict[str, object]]:
    """Return ordered flat metadata rows for several candle datasets."""

    rows: list[dict[str, object]] = []
    seen_dataset_ids: set[str] = set()
    for dataset_id, candles in _iter_named_candle_datasets(datasets):
        _validate_required_dataset_id(dataset_id)
        if dataset_id in seen_dataset_ids:
            raise CandleStorageError("dataset IDs must be unique")
        seen_dataset_ids.add(dataset_id)
        rows.append(candle_dataset_summary_row(candles, dataset_id=dataset_id))
    return rows


def candle_dataset_group_rows(
    datasets: Mapping[str, Sequence[MarketCandle]] | Sequence[tuple[str, Sequence[MarketCandle]]],
) -> list[dict[str, object]]:
    """Return ordered raw candle rows for several named datasets."""

    rows: list[dict[str, object]] = []
    seen_dataset_ids: set[str] = set()
    for dataset_id, candles in _iter_named_candle_datasets(datasets):
        _validate_required_dataset_id(dataset_id)
        if dataset_id in seen_dataset_ids:
            raise CandleStorageError("dataset IDs must be unique")
        seen_dataset_ids.add(dataset_id)
        for candle in candles:
            rows.append({"dataset_id": dataset_id, **candle.to_dict()})
    return rows


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


def _iter_named_candle_datasets(
    datasets: Mapping[str, Sequence[MarketCandle]] | Sequence[tuple[str, Sequence[MarketCandle]]],
) -> Iterable[tuple[str, Sequence[MarketCandle]]]:
    if isinstance(datasets, Mapping):
        yield from datasets.items()
        return
    for index, entry in enumerate(datasets):
        if not isinstance(entry, Sequence) or isinstance(entry, (str, bytes)) or len(entry) != 2:
            raise CandleStorageError(
                f"named candle dataset entry {index} must be a two-item (dataset_id, candles) pair"
            )
        dataset_id, candles = entry
        yield dataset_id, candles


def _validate_required_dataset_id(dataset_id: str) -> None:
    if not isinstance(dataset_id, str):
        raise CandleStorageError("dataset ID must be a string")
    if not dataset_id.strip():
        raise CandleStorageError("dataset ID must not be blank")


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
    if not isinstance(value, str) or not value.strip():
        raise CandleStorageError(f"candle row {index} field {field} must be a non-empty string")
    return value


def _require_float(value: Any, field: str, index: int) -> float:
    if isinstance(value, bool):
        raise CandleStorageError(f"candle row {index} field {field} must be numeric")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise CandleStorageError(f"candle row {index} field {field} must be numeric") from exc
