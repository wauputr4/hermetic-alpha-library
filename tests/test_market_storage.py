from datetime import datetime, timezone, timedelta

import pytest

from hermetic_alpha.market import CandleStorageError, read_candles_json, write_candles_json
from hermetic_alpha.models import MarketCandle


def test_candle_json_storage_round_trips_market_candles(tmp_path):
    path = tmp_path / "btc-daily.json"
    timestamp = datetime(2024, 5, 8, 7, 0, tzinfo=timezone(timedelta(hours=7)))
    candles = [
        MarketCandle(
            timestamp=timestamp,
            asset="BTC-USD",
            open=62300.0,
            high=63200.0,
            low=61000.0,
            close=62900.0,
            volume=25000000000.0,
            interval="1d",
            source="yahoo_finance",
        )
    ]

    write_candles_json(path, candles)

    assert read_candles_json(path) == candles


def test_candle_json_storage_rejects_empty_datasets(tmp_path):
    path = tmp_path / "empty.json"

    with pytest.raises(CandleStorageError, match="empty candle dataset"):
        write_candles_json(path, [])

    path.write_text("[]", encoding="utf-8")

    with pytest.raises(CandleStorageError, match="at least one row"):
        read_candles_json(path)


def test_candle_json_storage_rejects_missing_required_fields(tmp_path):
    path = tmp_path / "missing.json"
    path.write_text('[{"timestamp": "2024-05-08T00:00:00+00:00", "asset": "BTC-USD"}]', encoding="utf-8")

    with pytest.raises(CandleStorageError, match="missing required field"):
        read_candles_json(path)


def test_candle_json_storage_rejects_invalid_timestamps(tmp_path):
    path = tmp_path / "bad-timestamp.json"
    path.write_text(
        """
        [
          {
            "timestamp": "2024-05-08T00:00:00",
            "asset": "BTC-USD",
            "open": 1,
            "high": 2,
            "low": 0.5,
            "close": 1.5,
            "interval": "1d"
          }
        ]
        """,
        encoding="utf-8",
    )

    with pytest.raises(CandleStorageError, match="timezone information"):
        read_candles_json(path)


def test_candle_json_storage_rejects_malformed_rows(tmp_path):
    path = tmp_path / "malformed.json"
    path.write_text('["not-a-row"]', encoding="utf-8")

    with pytest.raises(CandleStorageError, match="row 0 must be an object"):
        read_candles_json(path)
