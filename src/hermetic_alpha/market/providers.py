"""Market data providers for normalized OHLCV candles."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from hermetic_alpha.models import MarketCandle


UrlOpen = Callable[..., Any]


class MarketDataProviderError(RuntimeError):
    """Raised when a market data provider response cannot be used."""


class YahooFinanceProvider:
    """Fetch daily OHLCV candles from Yahoo Finance's chart endpoint."""

    source = "yahoo_finance"
    base_url = "https://query1.finance.yahoo.com/v8/finance/chart"

    def __init__(self, opener: UrlOpen | None = None, timeout: float = 20.0) -> None:
        self._opener = opener or urlopen
        self._timeout = timeout

    def fetch_daily_btc(self, start: date | datetime | str, end: date | datetime | str) -> list[MarketCandle]:
        """Return BTC-USD daily candles for an inclusive UTC date range."""
        return self.fetch_daily("BTC-USD", start, end)

    def fetch_daily(self, asset: str, start: date | datetime | str, end: date | datetime | str) -> list[MarketCandle]:
        """Return daily candles for an inclusive UTC date range."""
        asset = _validate_asset_symbol(asset)
        start_dt = _coerce_utc_midnight(start)
        end_dt = _coerce_utc_midnight(end)
        if end_dt < start_dt:
            raise ValueError("end must be on or after start")

        payload = self._request_chart(asset, start_dt, end_dt)
        result = _first_chart_result(payload)
        return _candles_from_chart_result(result, asset=asset, source=self.source, interval="1d")

    def _request_chart(self, asset: str, start: datetime, end: datetime) -> dict[str, Any]:
        params = urlencode(
            {
                "period1": int(start.timestamp()),
                "period2": int((end + timedelta(days=1)).timestamp()),
                "interval": "1d",
                "events": "history",
            }
        )
        request = Request(
            f"{self.base_url}/{asset}?{params}",
            headers={"User-Agent": "hermetic-alpha-library/0.1"},
        )
        try:
            with self._opener(request, timeout=self._timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except OSError as exc:
            raise MarketDataProviderError(f"Yahoo Finance request failed for {asset}") from exc
        except json.JSONDecodeError as exc:
            raise MarketDataProviderError(f"Yahoo Finance returned invalid JSON for {asset}") from exc


def _validate_asset_symbol(asset: str) -> str:
    if not isinstance(asset, str) or not asset.strip():
        raise ValueError("asset must be a non-blank string")
    return asset


def _coerce_utc_midnight(value: date | datetime | str) -> datetime:
    if isinstance(value, str):
        value = date.fromisoformat(value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime values must be timezone-aware")
        value = value.astimezone(timezone.utc).date()
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def _first_chart_result(payload: dict[str, Any]) -> dict[str, Any]:
    chart = payload.get("chart")
    if not isinstance(chart, dict):
        raise MarketDataProviderError("Yahoo Finance response is missing chart data")
    error = chart.get("error")
    if error:
        raise MarketDataProviderError(f"Yahoo Finance chart error: {error}")
    results = chart.get("result")
    if not isinstance(results, list) or not results:
        raise MarketDataProviderError("Yahoo Finance response contains no chart results")
    result = results[0]
    if not isinstance(result, dict):
        raise MarketDataProviderError("Yahoo Finance chart result has unexpected shape")
    return result


def _candles_from_chart_result(
    result: dict[str, Any],
    *,
    asset: str,
    source: str,
    interval: str,
) -> list[MarketCandle]:
    timestamps = result.get("timestamp")
    quotes = (result.get("indicators") or {}).get("quote") or []
    if not isinstance(timestamps, list) or not quotes or not isinstance(quotes[0], dict):
        raise MarketDataProviderError("Yahoo Finance chart result is missing timestamps or quotes")
    quote = quotes[0]

    opens = quote.get("open", [])
    highs = quote.get("high", [])
    lows = quote.get("low", [])
    closes = quote.get("close", [])
    volumes = quote.get("volume", [])
    candles: list[MarketCandle] = []

    for index, timestamp in enumerate(timestamps):
        open_value = _list_value(opens, index)
        high_value = _list_value(highs, index)
        low_value = _list_value(lows, index)
        close_value = _list_value(closes, index)
        if None in (open_value, high_value, low_value, close_value):
            continue

        candles.append(
            MarketCandle(
                timestamp=datetime.fromtimestamp(int(timestamp), tz=timezone.utc),
                asset=asset,
                open=float(open_value),
                high=float(high_value),
                low=float(low_value),
                close=float(close_value),
                volume=_optional_float(_list_value(volumes, index)),
                interval=interval,
                source=source,
            )
        )

    if not candles:
        raise MarketDataProviderError("Yahoo Finance chart result normalized to zero usable candles")

    return candles


def _list_value(values: Any, index: int) -> Any:
    if isinstance(values, list) and index < len(values):
        return values[index]
    return None


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
