"""Transparent event-study summaries."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from collections.abc import Sequence
from statistics import mean, median
from typing import Mapping

from .validation import bootstrap_percentile_interval, low_sample_warning
from hermetic_alpha.models import AspectEvent, EventStudyResult, MarketLabel

EventStudyLabelRow = dict[str, object]
MarketLabelInput = MarketLabel | Mapping[str, object]


@dataclass(frozen=True)
class AspectMarketJoin:
    """One exact timestamp match between an aspect event and a market label."""

    event: AspectEvent
    label: EventStudyLabelRow
    event_index: int
    label_index: int

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["event"] = self.event.to_dict()
        return data


@dataclass(frozen=True)
class TimestampJoinResult:
    """Inspectable exact timestamp join output for event-study selection."""

    labels: list[EventStudyLabelRow]
    event_indexes: list[int]
    joined: list[AspectMarketJoin]
    unmatched_event_indexes: list[int]

    @property
    def matched_events(self) -> int:
        return len(self.joined)

    @property
    def unmatched_events(self) -> int:
        return len(self.unmatched_event_indexes)

    def to_dict(self) -> dict[str, object]:
        return {
            "labels": self.labels,
            "event_indexes": self.event_indexes,
            "joined": [record.to_dict() for record in self.joined],
            "matched_events": self.matched_events,
            "unmatched_events": self.unmatched_events,
            "unmatched_event_indexes": self.unmatched_event_indexes,
        }


@dataclass(frozen=True)
class ValidatedEventStudyReport:
    """Event-study summary plus validation metadata for cautious reporting."""

    summary: EventStudyResult
    low_sample_warning: str | None
    return_confidence_interval: tuple[float, float] | None
    bootstrap_samples: int
    bootstrap_confidence: float
    bootstrap_seed: int | None

    def to_dict(self) -> dict[str, object]:
        return {
            "summary": self.summary.to_dict(),
            "low_sample_warning": self.low_sample_warning,
            "return_confidence_interval": (
                list(self.return_confidence_interval)
                if self.return_confidence_interval is not None
                else None
            ),
            "bootstrap_samples": self.bootstrap_samples,
            "bootstrap_confidence": self.bootstrap_confidence,
            "bootstrap_seed": self.bootstrap_seed,
        }


def validated_event_study_report_row(report: ValidatedEventStudyReport) -> dict[str, object]:
    """Return a flat scalar row for CSV-friendly validated report export."""
    interval_lower: float | None = None
    interval_upper: float | None = None
    if report.return_confidence_interval is not None:
        interval_lower, interval_upper = report.return_confidence_interval

    summary = report.summary
    return {
        "events": summary.events,
        "horizon": summary.horizon,
        "baseline_bullish_probability": summary.baseline_bullish_probability,
        "conditional_bullish_probability": summary.conditional_bullish_probability,
        "average_return": summary.average_return,
        "median_return": summary.median_return,
        "low_sample_warning": report.low_sample_warning,
        "bootstrap_samples": report.bootstrap_samples,
        "bootstrap_confidence": report.bootstrap_confidence,
        "bootstrap_seed": report.bootstrap_seed,
        "return_confidence_interval_lower": interval_lower,
        "return_confidence_interval_upper": interval_upper,
    }


def aspect_event_study(
    all_labels: Sequence[dict[str, float | bool | None]],
    event_indexes: Sequence[int],
    horizon: int,
) -> EventStudyResult:
    """Backward-compatible alias for ``summarize_event_study``.

    Existing notebooks and docs that still import ``aspect_event_study`` can
    continue to run while the preferred public name is ``summarize_event_study``.
    """
    return summarize_event_study(all_labels, event_indexes, horizon)


def join_aspect_events_to_market_labels(
    events: Sequence[AspectEvent],
    market_labels: Sequence[MarketLabelInput],
) -> TimestampJoinResult:
    """Join aspect events to market labels by exact timestamp.

    Unmatched events are skipped and reported through
    ``unmatched_event_indexes``. Duplicate market-label timestamps fail because
    event-study selection would otherwise be ambiguous.
    """
    normalized_labels = [_normalize_market_label(label) for label in market_labels]
    label_index_by_timestamp: dict[datetime, int] = {}
    for index, label in enumerate(normalized_labels):
        timestamp = _label_timestamp(label, index)
        if timestamp in label_index_by_timestamp:
            raise ValueError(f"duplicate market label timestamp: {timestamp.isoformat()}")
        label_index_by_timestamp[timestamp] = index

    matched: list[AspectMarketJoin] = []
    unmatched_event_indexes: list[int] = []
    for event_index, event in sorted(enumerate(events), key=_event_sort_key):
        if event.timestamp is None:
            raise ValueError(f"aspect event at index {event_index} is missing a timestamp")
        label_index = label_index_by_timestamp.get(event.timestamp)
        if label_index is None:
            unmatched_event_indexes.append(event_index)
            continue
        matched.append(
            AspectMarketJoin(
                event=event,
                label=normalized_labels[label_index],
                event_index=event_index,
                label_index=label_index,
            )
        )

    return TimestampJoinResult(
        labels=normalized_labels,
        event_indexes=[record.label_index for record in matched],
        joined=matched,
        unmatched_event_indexes=unmatched_event_indexes,
    )


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


def summarize_validated_event_study(
    all_labels: Sequence[dict[str, float | bool | None]],
    event_indexes: Sequence[int],
    horizon: int,
    *,
    bootstrap_samples: int = 1000,
    bootstrap_confidence: float = 0.95,
    bootstrap_seed: int | None = None,
    minimum_events: int = 30,
) -> ValidatedEventStudyReport:
    """Summarize an event study with bootstrap and sample-size metadata."""
    summary = summarize_event_study(all_labels, event_indexes, horizon)
    event_returns = _event_return_values(all_labels, event_indexes, horizon)
    confidence_interval = (
        bootstrap_percentile_interval(
            event_returns,
            samples=bootstrap_samples,
            confidence=bootstrap_confidence,
            seed=bootstrap_seed,
        )
        if event_returns
        else None
    )
    return ValidatedEventStudyReport(
        summary=summary,
        low_sample_warning=low_sample_warning(summary.events, minimum=minimum_events),
        return_confidence_interval=confidence_interval,
        bootstrap_samples=bootstrap_samples,
        bootstrap_confidence=bootstrap_confidence,
        bootstrap_seed=bootstrap_seed,
    )


def _event_return_values(
    all_labels: Sequence[dict[str, float | bool | None]],
    event_indexes: Sequence[int],
    horizon: int,
) -> list[float]:
    return_key = f"return_{horizon}d"
    values: list[float] = []
    for index in event_indexes:
        if index < 0 or index >= len(all_labels):
            continue
        value = all_labels[index].get(return_key)
        if value is not None:
            values.append(float(value))
    return values


def _event_sort_key(indexed_event: tuple[int, AspectEvent]) -> tuple[datetime, int]:
    index, event = indexed_event
    if event.timestamp is None:
        raise ValueError(f"aspect event at index {index} is missing a timestamp")
    return event.timestamp, index


def _normalize_market_label(label: MarketLabelInput) -> EventStudyLabelRow:
    if isinstance(label, MarketLabel):
        row: EventStudyLabelRow = {
            "timestamp": label.timestamp,
            "asset": label.asset,
            f"return_{label.horizon}d": label.forward_return,
            f"bullish_{label.horizon}d": label.bullish,
            f"local_top_{label.horizon}d": label.local_top,
            f"local_bottom_{label.horizon}d": label.local_bottom,
        }
        return row
    return dict(label)


def _label_timestamp(label: EventStudyLabelRow, index: int) -> datetime:
    timestamp = label.get("timestamp")
    if not isinstance(timestamp, datetime):
        raise ValueError(f"market label at index {index} must include a datetime timestamp")
    return timestamp


def summarize_multi_horizon_event_study(
    all_labels: Sequence[dict[str, float | bool | None]],
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
