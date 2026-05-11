import pytest

from hermetic_alpha.analysis import summarize_event_study, summarize_multi_horizon_event_study
from hermetic_alpha.labels import add_forward_returns, add_local_extrema_labels, bullish_probability


def test_forward_returns_and_bullish_probability():
    labels = add_forward_returns([100, 110, 99, 120], [1])
    assert round(labels[0]["return_1d"], 4) == 0.1
    assert labels[-1]["return_1d"] is None
    assert bullish_probability(labels, 1) == 2 / 3


def test_forward_returns_with_zero_close_is_safe():
    labels = add_forward_returns([100, 0, 110], [1])

    assert labels[0]["return_1d"] == -1.0
    assert labels[0]["bullish_1d"] is False
    assert labels[1]["return_1d"] is None
    assert labels[1]["bullish_1d"] is None


def test_local_extrema_labels_mark_top_bottom_and_neutral_cases():
    labels = add_local_extrema_labels([100, 90, 110, 105, 95, 115, 108], 1)

    assert labels[0] == {"local_top_1d": None, "local_bottom_1d": None}
    assert labels[1]["local_bottom_1d"] is True
    assert labels[2]["local_top_1d"] is True
    assert labels[3]["local_top_1d"] is False
    assert labels[3]["local_bottom_1d"] is False
    assert labels[-1] == {"local_top_1d": None, "local_bottom_1d": None}


def test_local_extrema_labels_support_multiple_windows():
    labels = add_local_extrema_labels([100, 90, 110, 105, 95, 115, 108], [1, 2, 1])

    assert list(labels[0].keys()) == ["local_top_1d", "local_bottom_1d", "local_top_2d", "local_bottom_2d"]
    assert labels[2]["local_top_1d"] is True
    assert labels[2]["local_top_2d"] is True
    assert labels[4]["local_bottom_1d"] is True
    assert labels[4]["local_bottom_2d"] is True
    assert labels[1]["local_top_2d"] is None
    assert labels[-2]["local_bottom_2d"] is None


def test_local_extrema_labels_validate_window_size():
    with pytest.raises(ValueError, match="windows must be positive integers"):
        add_local_extrema_labels([100, 90, 110], 0)

    with pytest.raises(ValueError, match="windows must be positive integers"):
        add_local_extrema_labels([100, 90, 110], [1, -2])


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
