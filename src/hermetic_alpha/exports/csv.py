"""CSV serialization helpers for flat Hermetic Alpha result rows."""

from __future__ import annotations

import csv
from datetime import date, datetime
from io import StringIO
from os import PathLike
from pathlib import Path
from typing import Any, Mapping, Sequence

FlatValue = str | int | float | bool | None


def to_csv(rows: Any, *, fieldnames: Sequence[str] | None = None) -> str:
    """Return CSV text for flat mappings or objects with ``to_dict()``."""

    normalized_rows = _normalize_rows(rows)
    header = _validate_explicit_fieldnames(fieldnames) if fieldnames is not None else _fieldnames(normalized_rows)

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=header, extrasaction="raise", lineterminator="\n")
    writer.writeheader()
    for row in normalized_rows:
        _validate_flat_row(row)
        if fieldnames is not None:
            _validate_header_fields(row, header)
        writer.writerow(row)
    return output.getvalue()


def write_csv(rows: Any, path: str | PathLike[str], *, fieldnames: Sequence[str] | None = None) -> None:
    """Write CSV text to ``path``."""

    with Path(path).open("w", encoding="utf-8", newline="") as file:
        file.write(to_csv(rows, fieldnames=fieldnames))


def _normalize_rows(rows: Any) -> list[dict[str, Any]]:
    if rows is None:
        return []
    if _is_row(rows):
        return [_normalize_row(rows)]
    if isinstance(rows, Sequence) and not isinstance(rows, str | bytes | bytearray):
        return [_normalize_row(row) for row in rows]
    raise TypeError("CSV export expects a mapping, model object, or sequence of rows")


def _normalize_row(row: Any) -> dict[str, Any]:
    if hasattr(row, "to_dict") and callable(row.to_dict):
        row = row.to_dict()
    if not isinstance(row, Mapping):
        raise TypeError("CSV rows must be mappings or objects with to_dict()")
    return {str(key): _normalize_flat_value(value) for key, value in row.items()}


def _is_row(value: Any) -> bool:
    return isinstance(value, Mapping) or (hasattr(value, "to_dict") and callable(value.to_dict))


def _fieldnames(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    return fieldnames


def _validate_explicit_fieldnames(fieldnames: Sequence[str]) -> list[str]:
    header: list[str] = []
    seen: set[str] = set()
    for name in fieldnames:
        if not isinstance(name, str):
            raise TypeError(f"CSV fieldnames must be strings, got {type(name).__name__}")
        normalized = name.strip()
        if not normalized:
            raise ValueError("CSV fieldnames must not contain blank names")
        if normalized in seen:
            raise ValueError(f"CSV fieldnames must be unique: {normalized}")
        seen.add(normalized)
        header.append(normalized)
    return header


def _validate_flat_row(row: Mapping[str, Any]) -> None:
    for key, value in row.items():
        if not isinstance(value, FlatValue):
            raise TypeError(f"CSV field {key!r} contains unsupported nested value {type(value).__name__}")


def _validate_header_fields(row: Mapping[str, Any], fieldnames: Sequence[str]) -> None:
    extra_fields = set(row).difference(fieldnames)
    if extra_fields:
        fields = ", ".join(sorted(extra_fields))
        raise ValueError(f"CSV row contains fields outside the configured header: {fields}")


def _normalize_flat_value(value: Any) -> Any:
    if isinstance(value, datetime | date):
        return value.isoformat()
    return value
