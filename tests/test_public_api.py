from datetime import datetime, timezone

from hermetic_alpha import AspectDefinition, EventStudyResult, MarketCandle, PlanetPosition
from hermetic_alpha.analysis import aspect_event_study
from hermetic_alpha.astro import AspectDefinition as AstroAspectDefinition


def test_public_api_exports_match_documented_entrypoints():
    assert AspectDefinition is AstroAspectDefinition
    assert callable(aspect_event_study)

    ts = datetime(2026, 5, 6, tzinfo=timezone.utc)
    labels = [{"return_1d": 0.1, "bullish_1d": True}, {"return_1d": -0.05, "bullish_1d": False}]
    result = aspect_event_study(labels, event_indexes=[0], horizon=1)

    assert isinstance(result, EventStudyResult)
    assert result.horizon == 1
    assert result.events == 1
    assert MarketCandle(ts, "BTC-USD", 1.0, 2.0, 0.5, 1.5).asset == "BTC-USD"
    assert PlanetPosition(ts, "sun", 10.0).to_dict()["timestamp"] == ts.isoformat()
