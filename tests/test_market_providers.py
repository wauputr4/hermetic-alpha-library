import json
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

import pytest

from hermetic_alpha.market import MarketDataProviderError, YahooFinanceProvider


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def chart_payload():
    return {
        "chart": {
            "result": [
                {
                    "timestamp": [1715126400, 1715212800],
                    "indicators": {
                        "quote": [
                            {
                                "open": [62300.0, None],
                                "high": [63200.0, 64000.0],
                                "low": [61000.0, 62000.0],
                                "close": [62900.0, 63500.0],
                                "volume": [25000000000, 26000000000],
                            }
                        ]
                    },
                }
            ],
            "error": None,
        }
    }


def test_yahoo_finance_provider_fetches_normalized_btc_daily_candles():
    requests = []

    def opener(request, *, timeout):
        requests.append((request, timeout))
        return FakeResponse(chart_payload())

    provider = YahooFinanceProvider(opener=opener, timeout=3.0)
    candles = provider.fetch_daily_btc("2024-05-08", "2024-05-09")

    assert len(candles) == 1
    assert candles[0].timestamp == datetime(2024, 5, 8, tzinfo=timezone.utc)
    assert candles[0].asset == "BTC-USD"
    assert candles[0].open == 62300.0
    assert candles[0].high == 63200.0
    assert candles[0].low == 61000.0
    assert candles[0].close == 62900.0
    assert candles[0].volume == 25000000000.0
    assert candles[0].interval == "1d"
    assert candles[0].source == "yahoo_finance"

    request, timeout = requests[0]
    assert timeout == 3.0
    assert request.get_header("User-agent") == "hermetic-alpha-library/0.1"
    parsed = urlparse(request.full_url)
    params = parse_qs(parsed.query)
    assert parsed.path.endswith("/BTC-USD")
    assert params["interval"] == ["1d"]
    assert params["events"] == ["history"]


def test_yahoo_finance_provider_passes_timeout_by_keyword():
    def opener(request, data=None, timeout=None):
        assert data is None
        assert timeout == 7.0
        return FakeResponse(chart_payload())

    provider = YahooFinanceProvider(opener=opener, timeout=7.0)

    assert provider.fetch_daily_btc("2024-05-08", "2024-05-09")


def test_yahoo_finance_provider_requires_aware_datetimes():
    provider = YahooFinanceProvider(opener=lambda request, *, timeout: FakeResponse(chart_payload()))

    with pytest.raises(ValueError, match="timezone-aware"):
        provider.fetch_daily_btc(datetime(2024, 5, 8), "2024-05-09")


def test_yahoo_finance_provider_reports_chart_errors():
    payload = {"chart": {"result": None, "error": {"code": "Not Found", "description": "No data"}}}
    provider = YahooFinanceProvider(opener=lambda request, *, timeout: FakeResponse(payload))

    with pytest.raises(MarketDataProviderError, match="Yahoo Finance chart error"):
        provider.fetch_daily_btc("2024-05-08", "2024-05-09")


def test_yahoo_finance_provider_reports_empty_quote_arrays():
    payload = {"chart": {"result": [{"timestamp": [1715126400], "indicators": {"quote": []}}], "error": None}}
    provider = YahooFinanceProvider(opener=lambda request, *, timeout: FakeResponse(payload))

    with pytest.raises(MarketDataProviderError, match="missing timestamps or quotes"):
        provider.fetch_daily_btc("2024-05-08", "2024-05-09")
