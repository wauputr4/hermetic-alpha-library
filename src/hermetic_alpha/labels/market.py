"""Market labeling helpers for forward-return based research."""

from __future__ import annotations

from collections.abc import Sequence


def add_forward_returns(closes: Sequence[float], horizons: Sequence[int]) -> list[dict[str, float | bool | None]]:
    """Create forward return and bullish labels for a sequence of close prices."""
    rows: list[dict[str, float | bool | None]] = []
    for index, close in enumerate(closes):
        row: dict[str, float | bool | None] = {}
        for horizon in horizons:
            if horizon <= 0:
                raise ValueError("horizons must be positive integers")
            future_index = index + horizon
            return_key = f"return_{horizon}d"
            bullish_key = f"bullish_{horizon}d"
            if future_index >= len(closes):
                row[return_key] = None
                row[bullish_key] = None
                continue
            forward_return = (closes[future_index] / close) - 1
            row[return_key] = forward_return
            row[bullish_key] = forward_return > 0
        rows.append(row)
    return rows


def bullish_probability(labels: Sequence[dict[str, float | bool | None]], horizon: int) -> float | None:
    """Calculate bullish probability for a horizon from label rows."""
    key = f"bullish_{horizon}d"
    values = [row[key] for row in labels if row.get(key) is not None]
    if not values:
        return None
    return sum(1 for value in values if value is True) / len(values)
