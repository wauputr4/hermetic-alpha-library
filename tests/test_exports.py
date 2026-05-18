from datetime import datetime, timezone

import pytest

from hermetic_alpha.analysis import summarize_validated_event_study, validated_event_study_report_row
from hermetic_alpha.exports import to_csv, to_json, write_csv, write_json
from hermetic_alpha.labels import add_forward_returns
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


def test_json_exports_native_dates():
    ts = datetime(2026, 5, 17, 1, 2, tzinfo=timezone.utc)

    text = to_json({"timestamp": ts, "date": ts.date()})

    assert '"timestamp": "2026-05-17T01:02:00+00:00"' in text
    assert '"date": "2026-05-17"' in text


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


def test_csv_exports_native_dates():
    ts = datetime(2026, 5, 17, 1, 2, tzinfo=timezone.utc)

    text = to_csv([{"timestamp": ts, "date": ts.date(), "asset": "BTC-USD"}])

    assert "2026-05-17T01:02:00+00:00,2026-05-17,BTC-USD\n" in text


def test_csv_empty_inputs_and_explicit_header():
    assert to_csv([]) == "\r\n" or to_csv([]) == "\n"
    assert to_csv([], fieldnames=["asset", "close"]) == "asset,close\n"


def test_csv_rejects_nested_values():
    with pytest.raises(TypeError, match="unsupported nested value"):
        to_csv([{"asset": "BTC-USD", "nested": {"close": 1.0}}])


def test_csv_rejects_extra_fields_with_explicit_header():
    with pytest.raises(ValueError, match="outside the configured header: extra"):
        to_csv([{"asset": "BTC-USD", "close": 1.0, "extra": "nope"}], fieldnames=["asset", "close"])


def test_csv_accepts_flat_validated_event_study_report_rows():
    labels = add_forward_returns([100, 110, 99, 120], [1])
    report = summarize_validated_event_study(labels, [0, 1], 1, bootstrap_samples=20, bootstrap_seed=3)

    text = to_csv([validated_event_study_report_row(report)])

    header = text.splitlines()[0]
    assert "events,horizon,baseline_bullish_probability" in header
    assert "return_confidence_interval_lower,return_confidence_interval_upper" in header
    assert "Low sample size: 2 observations" in text
