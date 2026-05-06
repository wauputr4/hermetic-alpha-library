from hermetic_alpha.analysis import summarize_event_study
from hermetic_alpha.labels import add_forward_returns, bullish_probability


def test_forward_returns_and_bullish_probability():
    labels = add_forward_returns([100, 110, 99, 120], [1])
    assert labels[0]["return_1d"] == 0.1
    assert labels[-1]["return_1d"] is None
    assert bullish_probability(labels, 1) == 2 / 3


def test_event_study_summary():
    labels = add_forward_returns([100, 110, 99, 120], [1])
    result = summarize_event_study(labels, [0, 1], 1)
    assert result.events == 2
    assert result.baseline_bullish_probability == 2 / 3
    assert result.conditional_bullish_probability == 1 / 2
