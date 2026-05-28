import json
import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from hermetic_alpha.market import MarketDataProviderError, YahooFinanceProvider, read_candles_json


EXAMPLE_PATH = Path(__file__).resolve().parents[1] / "examples" / "provider_to_cache.py"


def load_provider_to_cache_example():
    spec = importlib.util.spec_from_file_location("provider_to_cache_example", EXAMPLE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def test_provider_to_cache_example_writes_candles_without_live_network(tmp_path):
    example = load_provider_to_cache_example()
    provider = YahooFinanceProvider(opener=lambda request, *, timeout: FakeResponse(chart_payload()))
    path = tmp_path / "btc-daily.json"

    result = example.write_btc_daily_cache(path, start="2024-05-08", end="2024-05-09", provider=provider)

    assert result == path
    candles = read_candles_json(path)
    assert len(candles) == 1
    assert candles[0].asset == "BTC-USD"
    assert candles[0].source == "yahoo_finance"
    assert candles[0].interval == "1d"


def test_yahoo_finance_provider_passes_timeout_by_keyword():
    def opener(request, data=None, timeout=None):
        assert data is None
        assert timeout == 7.0
        return FakeResponse(chart_payload())

    provider = YahooFinanceProvider(opener=opener, timeout=7.0)

    assert provider.fetch_daily_btc("2024-05-08", "2024-05-09")


@pytest.mark.parametrize("asset", ["", "   ", "\t\n"])
def test_yahoo_finance_provider_rejects_blank_asset_symbols_before_network(asset):
    requests = []
    provider = YahooFinanceProvider(opener=lambda request, *, timeout: requests.append(request))

    with pytest.raises(ValueError, match="asset must be a non-blank string"):
        provider.fetch_daily(asset, "2024-05-08", "2024-05-09")

    assert requests == []


@pytest.mark.parametrize("asset", [" BTC-USD", "BTC-USD ", "\tBTC-USD\n"])
def test_yahoo_finance_provider_rejects_whitespace_padded_asset_symbols_before_network(asset):
    requests = []
    provider = YahooFinanceProvider(opener=lambda request, *, timeout: requests.append(request))

    with pytest.raises(ValueError, match="leading or trailing whitespace"):
        provider.fetch_daily(asset, "2024-05-08", "2024-05-09")

    assert requests == []


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


def test_yahoo_finance_provider_reports_all_incomplete_quote_rows():
    payload = {
        "chart": {
            "result": [
                {
                    "timestamp": [1715126400, 1715212800],
                    "indicators": {
                        "quote": [
                            {
                                "open": [None, 63100.0],
                                "high": [63200.0, None],
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
    provider = YahooFinanceProvider(opener=lambda request, *, timeout: FakeResponse(payload))

    with pytest.raises(MarketDataProviderError, match="zero usable candles"):
        provider.fetch_daily_btc("2024-05-08", "2024-05-09")


def test_yahoo_finance_provider_wraps_malformed_timestamp_values():
    payload = chart_payload()
    payload["chart"]["result"][0]["timestamp"][0] = "not-a-timestamp"
    provider = YahooFinanceProvider(opener=lambda request, *, timeout: FakeResponse(payload))

    with pytest.raises(MarketDataProviderError, match="row 0 has malformed timestamp"):
        provider.fetch_daily_btc("2024-05-08", "2024-05-09")


def test_yahoo_finance_provider_wraps_malformed_volume_values():
    payload = chart_payload()
    payload["chart"]["result"][0]["indicators"]["quote"][0]["volume"][0] = "not-volume"
    provider = YahooFinanceProvider(opener=lambda request, *, timeout: FakeResponse(payload))

    with pytest.raises(MarketDataProviderError, match="row 0 has malformed volume value"):
        provider.fetch_daily_btc("2024-05-08", "2024-05-09")
