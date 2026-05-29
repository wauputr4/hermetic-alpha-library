"""JSON serialization helpers for library-owned result data."""

from __future__ import annotations

import json
from datetime import date, datetime
from os import PathLike
from pathlib import Path
from typing import Any, Mapping, Sequence

ExportValue = Any


def to_json(data: ExportValue, *, indent: int = 2, sort_keys: bool = True) -> str:
    """Return deterministic JSON for mappings, sequences, and model objects."""

    return json.dumps(_normalize(data), indent=indent, sort_keys=sort_keys)


def write_json(
    data: ExportValue,
    path: str | PathLike[str],
    *,
    indent: int = 2,
    sort_keys: bool = True,
) -> None:
    """Write deterministic JSON to ``path``."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(to_json(data, indent=indent, sort_keys=sort_keys) + "\n", encoding="utf-8")


def _normalize(value: ExportValue) -> ExportValue:
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _normalize(value.to_dict())
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {_normalize_object_key(key): _normalize(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [_normalize(item) for item in value]
    return value


def _normalize_object_key(key: Any) -> str:
    if not isinstance(key, str):
        raise TypeError(f"JSON object keys must be strings, got {type(key).__name__}")
    stripped = key.strip()
    if not stripped:
        raise ValueError("JSON object keys must not be blank")
    if key != stripped:
        raise ValueError(
            f"JSON object keys must not contain leading or trailing whitespace: {key!r}"
        )
    return key
