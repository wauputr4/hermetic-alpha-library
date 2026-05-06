"""Transparent event-study summaries."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median
from typing import Sequence


@dataclass(frozen=True)
class EventStudyResult:
    events: int
    horizon: int
    baseline_bullish_probability: float | None
    conditional_bullish_probability: float | None
    average_return: float | None
    median_return: float | None


def summarize_event_study(
    all_labels: Sequence[dict[str, float | bool | None]],
    event_indexes: Sequence[int],
    horizon: int,
) -> EventStudyResult:
    """Summarize forward market behavior after selected event indexes."""
    return_key = f"return_{horizon}d"
    bullish_key = f"bullish_{horizon}d"

    baseline_values = [row[bullish_key] for row in all_labels if row.get(bullish_key) is not None]
    event_rows = [all_labels[index] for index in event_indexes if 0 <= index < len(all_labels)]
    event_returns = [row[return_key] for row in event_rows if row.get(return_key) is not None]
    event_bullish = [row[bullish_key] for row in event_rows if row.get(bullish_key) is not None]

    return EventStudyResult(
        events=len(event_bullish),
        horizon=horizon,
        baseline_bullish_probability=(sum(1 for value in baseline_values if value is True) / len(baseline_values)) if baseline_values else None,
        conditional_bullish_probability=(sum(1 for value in event_bullish if value is True) / len(event_bullish)) if event_bullish else None,
        average_return=mean(event_returns) if event_returns else None,
        median_return=median(event_returns) if event_returns else None,
    )
