from hermetic_alpha.analysis import summarize_event_study, summarize_multi_horizon_event_study
from hermetic_alpha.labels import add_forward_returns, bullish_probability


def test_forward_returns_and_bullish_probability():
    labels = add_forward_returns([100, 110, 99, 120], [1])
    assert round(labels[0]["return_1d"], 4) == 0.1
    assert labels[-1]["return_1d"] is None
    assert bullish_probability(labels, 1) == 2 / 3


def test_event_study_summary():
    labels = add_forward_returns([100, 110, 99, 120], [1])
    result = summarize_event_study(labels, [0, 1], 1)
    assert result.events == 2
    assert result.baseline_bullish_probability == 2 / 3
    assert result.conditional_bullish_probability == 1 / 2


def test_multi_horizon_event_study_summary():
    labels = add_forward_returns([100, 110, 121, 90], [1, 2])
    results = summarize_multi_horizon_event_study(labels, [0, 1, 99], [1, 2, 1])

    assert list(results.keys()) == [1, 2]
    assert results[1].events == 2
    assert results[1].conditional_bullish_probability == 1.0
    assert results[2].events == 2
    assert results[2].conditional_bullish_probability == 1 / 2
    assert round(results[2].average_return, 4) == 0.0141
