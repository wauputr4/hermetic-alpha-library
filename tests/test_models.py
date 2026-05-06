from datetime import datetime, timezone

from hermetic_alpha.models import AspectEvent, MarketCandle, MarketLabel, PlanetPosition


def test_models_are_json_compatible_dicts():
    ts = datetime(2026, 5, 6, tzinfo=timezone.utc)
    assert PlanetPosition(ts, "sun", 42.0).to_dict()["timestamp"] == ts.isoformat()
    assert AspectEvent("sun", "jupiter", "conjunction", 0, 1, 1, 3, 0.66, ts).to_dict()["timestamp"] == ts.isoformat()
    assert MarketCandle(ts, "BTC-USD", 1, 2, 0.5, 1.5).to_dict()["asset"] == "BTC-USD"
    assert MarketLabel(ts, "BTC-USD", 7, 0.12, True).to_dict()["bullish"] is True
