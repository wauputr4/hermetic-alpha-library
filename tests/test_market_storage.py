import json
from datetime import datetime, timezone, timedelta

import pytest

from hermetic_alpha.market import (
    CandleStorageError,
    candle_dataset_group_rows,
    candle_dataset_summary_row,
    candle_dataset_summary_rows,
    read_candles_json,
    write_candles_json,
)
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


def test_candle_json_storage_rejects_malformed_candle_values(tmp_path):
    path = tmp_path / "malformed-candle-value.json"

    with pytest.raises(CandleStorageError, match="candle value 0 must be a MarketCandle"):
        write_candles_json(path, [object()])  # type: ignore[list-item]


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


@pytest.mark.parametrize("field", ["asset", "interval", "source"])
def test_candle_json_storage_rejects_blank_string_fields(tmp_path, field):
    path = tmp_path / f"blank-{field}.json"
    row = {
        "timestamp": "2024-05-08T00:00:00+00:00",
        "asset": "BTC-USD",
        "open": 1,
        "high": 2,
        "low": 0.5,
        "close": 1.5,
        "interval": "1d",
        "source": "unit_test",
    }
    row[field] = "   "
    path.write_text(json.dumps([row]), encoding="utf-8")

    with pytest.raises(CandleStorageError, match=f"field {field} must be a non-empty string"):
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


def test_candle_dataset_summary_row_rejects_malformed_candle_values():
    with pytest.raises(CandleStorageError, match="candle value 0 must be a MarketCandle"):
        candle_dataset_summary_row([object()])  # type: ignore[list-item]


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


def test_candle_dataset_summary_rows_preserves_ordered_mapping_order():
    btc = [MarketCandle(datetime(2024, 5, 8, tzinfo=timezone.utc), "BTC-USD", 100, 105, 95, 102)]
    eth = [MarketCandle(datetime(2024, 5, 9, tzinfo=timezone.utc), "ETH-USD", 200, 205, 195, 202)]

    rows = candle_dataset_summary_rows({"btc-daily": btc, "eth-daily": eth})

    assert [row["dataset_id"] for row in rows] == ["btc-daily", "eth-daily"]
    assert [row["asset"] for row in rows] == ["BTC-USD", "ETH-USD"]


def test_candle_dataset_summary_rows_accepts_ordered_pairs():
    btc = [MarketCandle(datetime(2024, 5, 8, tzinfo=timezone.utc), "BTC-USD", 100, 105, 95, 102)]
    eth = [MarketCandle(datetime(2024, 5, 9, tzinfo=timezone.utc), "ETH-USD", 200, 205, 195, 202)]

    rows = candle_dataset_summary_rows([("eth-daily", eth), ("btc-daily", btc)])

    assert [row["dataset_id"] for row in rows] == ["eth-daily", "btc-daily"]


def test_candle_dataset_summary_rows_rejects_duplicate_dataset_ids():
    candles = [MarketCandle(datetime(2024, 5, 8, tzinfo=timezone.utc), "BTC-USD", 100, 105, 95, 102)]

    with pytest.raises(CandleStorageError, match="dataset IDs must be unique"):
        candle_dataset_summary_rows([("btc-daily", candles), ("btc-daily", candles)])


def test_candle_dataset_summary_rows_rejects_blank_dataset_ids():
    candles = [MarketCandle(datetime(2024, 5, 8, tzinfo=timezone.utc), "BTC-USD", 100, 105, 95, 102)]

    with pytest.raises(CandleStorageError, match="dataset ID must not be blank"):
        candle_dataset_summary_rows([("   ", candles)])


def test_candle_dataset_summary_rows_rejects_whitespace_padded_dataset_ids():
    candles = [MarketCandle(datetime(2024, 5, 8, tzinfo=timezone.utc), "BTC-USD", 100, 105, 95, 102)]

    with pytest.raises(CandleStorageError, match="leading or trailing whitespace"):
        candle_dataset_summary_rows([(" btc-daily ", candles)])


def test_candle_dataset_summary_rows_rejects_non_string_mapping_dataset_ids():
    candles = [MarketCandle(datetime(2024, 5, 8, tzinfo=timezone.utc), "BTC-USD", 100, 105, 95, 102)]

    with pytest.raises(CandleStorageError, match="dataset ID must be a string"):
        candle_dataset_summary_rows({123: candles})  # type: ignore[dict-item]


def test_candle_dataset_summary_rows_rejects_non_string_pair_dataset_ids():
    candles = [MarketCandle(datetime(2024, 5, 8, tzinfo=timezone.utc), "BTC-USD", 100, 105, 95, 102)]

    with pytest.raises(CandleStorageError, match="dataset ID must be a string"):
        candle_dataset_summary_rows([(123, candles)])  # type: ignore[list-item]


def test_candle_dataset_summary_rows_rejects_malformed_ordered_pairs():
    candles = [MarketCandle(datetime(2024, 5, 8, tzinfo=timezone.utc), "BTC-USD", 100, 105, 95, 102)]

    with pytest.raises(CandleStorageError, match="two-item"):
        candle_dataset_summary_rows([("btc", candles, "extra")])  # type: ignore[list-item]


def test_candle_dataset_summary_rows_delegates_dataset_validation():
    candles = [
        MarketCandle(datetime(2024, 5, 8, tzinfo=timezone.utc), "BTC-USD", 100, 105, 95, 102),
        MarketCandle(datetime(2024, 5, 9, tzinfo=timezone.utc), "ETH-USD", 200, 205, 195, 202),
    ]

    with pytest.raises(CandleStorageError, match="single asset"):
        candle_dataset_summary_rows([("mixed", candles)])

    with pytest.raises(CandleStorageError, match="empty candle dataset"):
        candle_dataset_summary_rows([("empty", [])])


def test_candle_dataset_summary_rows_rejects_malformed_candle_values():
    with pytest.raises(CandleStorageError, match="candle value 0 must be a MarketCandle"):
        candle_dataset_summary_rows([("btc-daily", [object()])])  # type: ignore[list-item]


def test_candle_dataset_group_rows_preserves_dataset_and_candle_order():
    first = MarketCandle(datetime(2024, 5, 8, tzinfo=timezone.utc), "BTC-USD", 100, 105, 95, 102)
    second = MarketCandle(datetime(2024, 5, 9, tzinfo=timezone.utc), "BTC-USD", 102, 106, 99, 104)
    third = MarketCandle(datetime(2024, 5, 10, tzinfo=timezone.utc), "ETH-USD", 200, 205, 195, 202)

    rows = candle_dataset_group_rows({"btc-daily": [first, second], "eth-daily": [third]})

    assert [row["dataset_id"] for row in rows] == ["btc-daily", "btc-daily", "eth-daily"]
    assert [row["timestamp"] for row in rows] == [
        "2024-05-08T00:00:00+00:00",
        "2024-05-09T00:00:00+00:00",
        "2024-05-10T00:00:00+00:00",
    ]
    assert [row["asset"] for row in rows] == ["BTC-USD", "BTC-USD", "ETH-USD"]


def test_candle_dataset_group_rows_accepts_ordered_pairs_and_skips_empty_datasets():
    btc = [MarketCandle(datetime(2024, 5, 8, tzinfo=timezone.utc), "BTC-USD", 100, 105, 95, 102)]
    eth = [MarketCandle(datetime(2024, 5, 9, tzinfo=timezone.utc), "ETH-USD", 200, 205, 195, 202)]

    rows = candle_dataset_group_rows([("empty", []), ("eth-daily", eth), ("btc-daily", btc)])

    assert [row["dataset_id"] for row in rows] == ["eth-daily", "btc-daily"]


def test_candle_dataset_group_rows_rejects_duplicate_dataset_ids():
    candles = [MarketCandle(datetime(2024, 5, 8, tzinfo=timezone.utc), "BTC-USD", 100, 105, 95, 102)]

    with pytest.raises(CandleStorageError, match="dataset IDs must be unique"):
        candle_dataset_group_rows([("btc-daily", candles), ("btc-daily", candles)])


def test_candle_dataset_group_rows_rejects_blank_dataset_ids():
    candles = [MarketCandle(datetime(2024, 5, 8, tzinfo=timezone.utc), "BTC-USD", 100, 105, 95, 102)]

    with pytest.raises(CandleStorageError, match="dataset ID must not be blank"):
        candle_dataset_group_rows([("   ", candles)])


def test_candle_dataset_group_rows_rejects_whitespace_padded_dataset_ids():
    candles = [MarketCandle(datetime(2024, 5, 8, tzinfo=timezone.utc), "BTC-USD", 100, 105, 95, 102)]

    with pytest.raises(CandleStorageError, match="leading or trailing whitespace"):
        candle_dataset_group_rows([("btc-daily ", candles)])


def test_candle_dataset_group_rows_rejects_non_string_dataset_ids():
    candles = [MarketCandle(datetime(2024, 5, 8, tzinfo=timezone.utc), "BTC-USD", 100, 105, 95, 102)]

    with pytest.raises(CandleStorageError, match="dataset ID must be a string"):
        candle_dataset_group_rows({123: candles})  # type: ignore[dict-item]

    with pytest.raises(CandleStorageError, match="dataset ID must be a string"):
        candle_dataset_group_rows([(123, candles)])  # type: ignore[list-item]


def test_candle_dataset_group_rows_rejects_malformed_ordered_pairs():
    with pytest.raises(CandleStorageError, match="two-item"):
        candle_dataset_group_rows(["btc"])  # type: ignore[arg-type]


def test_candle_dataset_group_rows_rejects_malformed_candle_values():
    with pytest.raises(CandleStorageError, match="candle value 0 must be a MarketCandle"):
        candle_dataset_group_rows([("btc-daily", [object()])])  # type: ignore[list-item]
