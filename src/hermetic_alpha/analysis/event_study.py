"""Transparent event-study summaries."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from statistics import mean, median

from hermetic_alpha.models import EventStudyResult


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


def summarize_multi_horizon_event_study(
    all_labels: Sequence[Mapping[str, float | bool | None]],
    event_indexes: Sequence[int],
    horizons: Sequence[int],
) -> dict[int, EventStudyResult]:
    """Summarize event-study results for multiple forward-return horizons.

    The returned dictionary is keyed by horizon so callers can compare 1d, 7d,
    30d, and other windows without rerunning event selection logic. Invalid event
    indexes are ignored consistently for every horizon.
    """
    unique_horizons = list(dict.fromkeys(horizons))
    return {
        horizon: summarize_event_study(all_labels, event_indexes, horizon)
        for horizon in unique_horizons
    }
