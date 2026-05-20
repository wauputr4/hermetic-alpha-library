from datetime import datetime, timezone, timedelta

import pytest

from hermetic_alpha.market import CandleStorageError, candle_dataset_summary_row, read_candles_json, write_candles_json
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


def test_candle_dataset_summary_row_reports_ordered_boundaries_and_dataset_id():
    first = datetime(2024, 5, 8, tzinfo=timezone.utc)
    last = datetime(2024, 5, 10, tzinfo=timezone.utc)
    candles = [
        MarketCandle(last, "BTC-USD", 110, 115, 105, 112, interval="1d", source="yahoo_finance"),
        MarketCandle(first, "BTC-USD", 100, 105, 95, 102, interval="1d", source="yahoo_finance"),
    ]

    row = candle_dataset_summary_row(candles, dataset_id="btc-may")

    assert row == {
        "dataset_id": "btc-may",
        "candle_count": 2,
        "asset": "BTC-USD",
        "interval": "1d",
        "source": "yahoo_finance",
        "first_timestamp": first,
        "last_timestamp": last,
    }


def test_candle_dataset_summary_row_uses_none_for_mixed_sources():
    candles = [
        MarketCandle(datetime(2024, 5, 8, tzinfo=timezone.utc), "BTC-USD", 100, 105, 95, 102, source="a"),
        MarketCandle(datetime(2024, 5, 9, tzinfo=timezone.utc), "BTC-USD", 101, 106, 96, 103, source="b"),
    ]

    row = candle_dataset_summary_row(candles)

    assert row["dataset_id"] is None
    assert row["source"] is None


def test_candle_dataset_summary_row_rejects_empty_input():
    with pytest.raises(CandleStorageError, match="empty candle dataset"):
        candle_dataset_summary_row([])


def test_candle_dataset_summary_row_rejects_mixed_assets_and_intervals():
    ts = datetime(2024, 5, 8, tzinfo=timezone.utc)

    with pytest.raises(CandleStorageError, match="single asset"):
        candle_dataset_summary_row(
            [
                MarketCandle(ts, "BTC-USD", 100, 105, 95, 102),
                MarketCandle(ts, "ETH-USD", 100, 105, 95, 102),
            ]
        )

    with pytest.raises(CandleStorageError, match="single interval"):
        candle_dataset_summary_row(
            [
                MarketCandle(ts, "BTC-USD", 100, 105, 95, 102, interval="1d"),
                MarketCandle(ts, "BTC-USD", 100, 105, 95, 102, interval="1h"),
            ]
        )
