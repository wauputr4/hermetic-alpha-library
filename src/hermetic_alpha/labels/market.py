"""Market labeling helpers for market-outcome research."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

from hermetic_alpha.models import MarketCandle


TimestampedForwardReturnRow = dict[str, object]
TimestampedLocalExtremaRow = dict[str, object]
ForwardReturnCoverageRow = dict[str, object]
LocalExtremaCoverageRow = dict[str, object]
MultiHorizonForwardReturnCoverageRows = list[ForwardReturnCoverageRow]
MultiWindowLocalExtremaCoverageRows = list[LocalExtremaCoverageRow]
MultiDatasetForwardReturnCoverageRows = list[ForwardReturnCoverageRow]
MultiDatasetLocalExtremaCoverageRows = list[LocalExtremaCoverageRow]
ForwardReturnLabelGroupRows = list[TimestampedForwardReturnRow]
LocalExtremaLabelGroupRows = list[TimestampedLocalExtremaRow]


def add_forward_returns(closes: Sequence[float], horizons: Sequence[int]) -> list[dict[str, float | bool | None]]:
    """Create forward return and bullish labels for a sequence of close prices.

    Non-positive base closes (for example zero) are treated as invalid for return
    calculation and produce ``None`` labels for that row.
    """
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
            if close <= 0:
                row[return_key] = None
                row[bullish_key] = None
                continue
            forward_return = (closes[future_index] / close) - 1
            row[return_key] = forward_return
            row[bullish_key] = forward_return > 0
        rows.append(row)
    return rows


def add_candle_forward_returns(
    candles: Sequence[MarketCandle],
    horizons: Sequence[int],
) -> list[TimestampedForwardReturnRow]:
    """Create timestamped forward-return labels from ordered market candles."""
    _validate_single_asset(candles)
    labels = add_forward_returns([candle.close for candle in candles], horizons)
    rows: list[TimestampedForwardReturnRow] = []
    for candle, label in zip(candles, labels, strict=True):
        rows.append({"timestamp": candle.timestamp, "asset": candle.asset, **label})
    return rows


def add_candle_local_extrema_labels(
    candles: Sequence[MarketCandle],
    windows: int | Sequence[int],
) -> list[TimestampedLocalExtremaRow]:
    """Create timestamped local top/bottom labels from ordered market candles."""
    _validate_single_asset(candles)
    labels = add_local_extrema_labels([candle.close for candle in candles], windows)
    rows: list[TimestampedLocalExtremaRow] = []
    for candle, label in zip(candles, labels, strict=True):
        rows.append({"timestamp": candle.timestamp, "asset": candle.asset, **label})
    return rows


def _validate_single_asset(candles: Sequence[MarketCandle]) -> None:
    assets = {candle.asset for candle in candles}
    if len(assets) > 1:
        raise ValueError("candle labels require a single asset")


def _normalize_windows(windows: int | Sequence[int]) -> list[int]:
    if isinstance(windows, int):
        normalized = [windows]
    else:
        normalized = list(dict.fromkeys(windows))

    if not normalized or any(window <= 0 for window in normalized):
        raise ValueError("windows must be positive integers")
    return normalized


def _normalize_horizons(horizons: Sequence[int]) -> list[int]:
    normalized = list(dict.fromkeys(horizons))
    if not normalized or any(horizon <= 0 for horizon in normalized):
        raise ValueError("horizons must be positive integers")
    return normalized


def add_local_extrema_labels(closes: Sequence[float], windows: int | Sequence[int]) -> list[dict[str, bool | None]]:
    """Label closes that are local tops or bottoms within centered windows."""
    normalized_windows = _normalize_windows(windows)
    close_count = len(closes)
    keys = [(window, f"local_top_{window}d", f"local_bottom_{window}d") for window in normalized_windows]

    rows: list[dict[str, bool | None]] = []
    for index, close in enumerate(closes):
        row: dict[str, bool | None] = {}
        for window, top_key, bottom_key in keys:
            start = index - window
            end = index + window + 1
            if start < 0 or end > close_count:
                row[top_key] = None
                row[bottom_key] = None
                continue

            window_closes = closes[start:end]
            row[top_key] = close == max(window_closes)
            row[bottom_key] = close == min(window_closes)
        rows.append(row)
    return rows


def bullish_probability(labels: Sequence[dict[str, float | bool | None]], horizon: int) -> float | None:
    """Calculate bullish probability for a horizon from label rows."""
    key = f"bullish_{horizon}d"
    values = [row[key] for row in labels if row.get(key) is not None]
    if not values:
        return None
    return sum(1 for value in values if value is True) / len(values)


def forward_return_label_coverage_row(
    labels: Sequence[dict[str, object]],
    horizon: int,
    *,
    dataset_id: str | None = None,
) -> ForwardReturnCoverageRow:
    """Return compact CSV-compatible coverage metadata for forward-return labels."""
    if horizon <= 0:
        raise ValueError("horizon must be a positive integer")
    _validate_dataset_id(dataset_id)

    return_key = f"return_{horizon}d"
    bullish_key = f"bullish_{horizon}d"
    row_count = len(labels)
    labeled_return_count = sum(1 for row in labels if row.get(return_key) is not None)
    bullish_count = sum(1 for row in labels if row.get(bullish_key) is True)
    bearish_count = sum(1 for row in labels if row.get(bullish_key) is False)
    assets = {row.get("asset") for row in labels if row.get("asset") is not None}

    return {
        "dataset_id": dataset_id,
        "horizon": horizon,
        "row_count": row_count,
        "labeled_return_count": labeled_return_count,
        "bullish_count": bullish_count,
        "bearish_count": bearish_count,
        "missing_label_count": row_count - bullish_count - bearish_count,
        "asset": next(iter(assets)) if len(assets) == 1 else None,
        "first_timestamp": labels[0].get("timestamp") if labels else None,
        "last_timestamp": labels[-1].get("timestamp") if labels else None,
    }


def multi_horizon_forward_return_label_coverage_rows(
    labels: Sequence[dict[str, object]],
    horizons: Sequence[int],
    *,
    dataset_id: str | None = None,
) -> MultiHorizonForwardReturnCoverageRows:
    """Return ordered CSV-compatible coverage metadata for several horizons."""
    return [
        forward_return_label_coverage_row(labels, horizon, dataset_id=dataset_id)
        for horizon in _normalize_horizons(horizons)
    ]


def multi_dataset_forward_return_label_coverage_rows(
    datasets: Mapping[str, Sequence[dict[str, object]]] | Sequence[tuple[str, Sequence[dict[str, object]]]],
    horizons: Sequence[int],
) -> MultiDatasetForwardReturnCoverageRows:
    """Return ordered forward-return coverage rows for several label datasets."""
    rows: MultiDatasetForwardReturnCoverageRows = []
    seen_dataset_ids: set[str] = set()
    for dataset_id, labels in _iter_named_label_datasets(datasets):
        _validate_required_dataset_id(dataset_id)
        if dataset_id in seen_dataset_ids:
            raise ValueError("dataset IDs must be unique")
        seen_dataset_ids.add(dataset_id)
        rows.extend(multi_horizon_forward_return_label_coverage_rows(labels, horizons, dataset_id=dataset_id))
    return rows


def forward_return_label_group_rows(
    datasets: Mapping[str, Sequence[dict[str, object]]] | Sequence[tuple[str, Sequence[dict[str, object]]]],
) -> ForwardReturnLabelGroupRows:
    """Return ordered raw forward-return label rows for several datasets."""
    rows: ForwardReturnLabelGroupRows = []
    seen_dataset_ids: set[str] = set()
    for dataset_id, labels in _iter_named_label_datasets(datasets):
        _validate_required_dataset_id(dataset_id)
        if dataset_id in seen_dataset_ids:
            raise ValueError("dataset IDs must be unique")
        seen_dataset_ids.add(dataset_id)
        rows.extend({"dataset_id": dataset_id, **label} for label in labels)
    return rows


def local_extrema_label_coverage_row(
    labels: Sequence[dict[str, object]],
    window: int,
    *,
    dataset_id: str | None = None,
) -> LocalExtremaCoverageRow:
    """Return compact CSV-compatible coverage metadata for local-extrema labels."""
    if window <= 0:
        raise ValueError("window must be a positive integer")
    _validate_dataset_id(dataset_id)

    top_key = f"local_top_{window}d"
    bottom_key = f"local_bottom_{window}d"
    row_count = len(labels)
    labeled_count = sum(
        1 for row in labels if row.get(top_key) is not None and row.get(bottom_key) is not None
    )
    local_top_count = sum(1 for row in labels if row.get(top_key) is True)
    local_bottom_count = sum(1 for row in labels if row.get(bottom_key) is True)
    assets = {row.get("asset") for row in labels if row.get("asset") is not None}

    return {
        "dataset_id": dataset_id,
        "window": window,
        "row_count": row_count,
        "labeled_count": labeled_count,
        "missing_label_count": row_count - labeled_count,
        "local_top_count": local_top_count,
        "local_bottom_count": local_bottom_count,
        "asset": next(iter(assets)) if len(assets) == 1 else None,
        "first_timestamp": labels[0].get("timestamp") if labels else None,
        "last_timestamp": labels[-1].get("timestamp") if labels else None,
    }


def multi_window_local_extrema_label_coverage_rows(
    labels: Sequence[dict[str, object]],
    windows: int | Sequence[int],
    *,
    dataset_id: str | None = None,
) -> MultiWindowLocalExtremaCoverageRows:
    """Return ordered CSV-compatible coverage metadata for several windows."""
    return [
        local_extrema_label_coverage_row(labels, window, dataset_id=dataset_id)
        for window in _normalize_windows(windows)
    ]


def multi_dataset_local_extrema_label_coverage_rows(
    datasets: Mapping[str, Sequence[dict[str, object]]] | Sequence[tuple[str, Sequence[dict[str, object]]]],
    windows: int | Sequence[int],
) -> MultiDatasetLocalExtremaCoverageRows:
    """Return ordered local-extrema coverage rows for several label datasets."""
    rows: MultiDatasetLocalExtremaCoverageRows = []
    seen_dataset_ids: set[str] = set()
    for dataset_id, labels in _iter_named_label_datasets(datasets):
        _validate_required_dataset_id(dataset_id)
        if dataset_id in seen_dataset_ids:
            raise ValueError("dataset IDs must be unique")
        seen_dataset_ids.add(dataset_id)
        rows.extend(multi_window_local_extrema_label_coverage_rows(labels, windows, dataset_id=dataset_id))
    return rows


def local_extrema_label_group_rows(
    datasets: Mapping[str, Sequence[dict[str, object]]] | Sequence[tuple[str, Sequence[dict[str, object]]]],
) -> LocalExtremaLabelGroupRows:
    """Return ordered raw local-extrema label rows for several datasets."""
    rows: LocalExtremaLabelGroupRows = []
    seen_dataset_ids: set[str] = set()
    for dataset_id, labels in _iter_named_label_datasets(datasets):
        _validate_required_dataset_id(dataset_id)
        if dataset_id in seen_dataset_ids:
            raise ValueError("dataset IDs must be unique")
        seen_dataset_ids.add(dataset_id)
        rows.extend({"dataset_id": dataset_id, **label} for label in labels)
    return rows


def _validate_dataset_id(dataset_id: str | None) -> None:
    if dataset_id is None:
        return
    if not isinstance(dataset_id, str):
        raise ValueError("dataset ID must be a string")
    if not dataset_id.strip():
        raise ValueError("dataset ID must not be blank")


def _validate_required_dataset_id(dataset_id: str) -> None:
    if not isinstance(dataset_id, str):
        raise ValueError("dataset ID must be a string")
    if not dataset_id.strip():
        raise ValueError("dataset ID must not be blank")


def _iter_named_label_datasets(
    datasets: Mapping[str, Sequence[dict[str, object]]] | Sequence[tuple[str, Sequence[dict[str, object]]]],
) -> Iterable[tuple[str, Sequence[dict[str, object]]]]:
    if isinstance(datasets, Mapping):
        yield from datasets.items()
        return
    yield from datasets
