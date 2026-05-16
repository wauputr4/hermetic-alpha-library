from datetime import datetime, timezone

import pytest

from hermetic_alpha.exports import to_csv, to_json, write_csv, write_json
from hermetic_alpha.models import EventStudyResult, MarketCandle


def test_json_exports_model_objects_and_mappings(tmp_path):
    result = EventStudyResult(
        events=2,
        horizon=7,
        baseline_bullish_probability=0.5,
        conditional_bullish_probability=0.75,
        average_return=0.04,
        median_return=0.03,
    )

    text = to_json({"result": result, "source": "unit"})
    assert '"average_return": 0.04' in text
    assert text.index('"result"') < text.index('"source"')

    path = tmp_path / "result.json"
    write_json(result, path)
    assert path.read_text(encoding="utf-8").endswith("\n")
    assert '"events": 2' in path.read_text(encoding="utf-8")


def test_csv_exports_model_rows_with_stable_header(tmp_path):
    ts = datetime(2026, 5, 6, tzinfo=timezone.utc)
    rows = [
        MarketCandle(ts, "BTC-USD", 1.0, 2.0, 0.5, 1.5, volume=10.0),
        {"timestamp": ts.isoformat(), "asset": "ETH-USD", "close": 3.0, "extra": "ok"},
    ]

    text = to_csv(rows)
    assert text.splitlines()[0] == "timestamp,asset,open,high,low,close,volume,interval,source,extra"
    assert "BTC-USD" in text
    assert "ETH-USD" in text

    path = tmp_path / "rows.csv"
    write_csv(rows, path)
    assert path.read_text(encoding="utf-8") == text


def test_csv_empty_inputs_and_explicit_header():
    assert to_csv([]) == "\r\n" or to_csv([]) == "\n"
    assert to_csv([], fieldnames=["asset", "close"]) == "asset,close\n"


def test_csv_rejects_nested_values():
    with pytest.raises(TypeError, match="unsupported nested value"):
        to_csv([{"asset": "BTC-USD", "nested": {"close": 1.0}}])
