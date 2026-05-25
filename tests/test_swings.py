from src import swings


def test_swing_highs_and_lows_detected_with_window_1():
    # index:   0  1  2  3  4  5
    values = [1, 2, 1, 1, 4, 1]
    highs = swings.swing_highs(values, window=1)
    assert highs == [(1, 2.0), (4, 4.0)]


def test_higher_high_true():
    values = [1, 2, 1, 1, 4, 1]   # swing highs 2 then 4
    assert swings.is_higher_high(values, window=1) is True


def test_higher_high_false_when_lower_high():
    values = [1, 4, 1, 1, 2, 1]   # swing highs 4 then 2
    assert swings.is_higher_high(values, window=1) is False


def test_higher_low_true():
    values = [5, 1, 5, 5, 2, 5]   # swing lows 1 then 2
    assert swings.is_higher_low(values, window=1) is True


def test_higher_low_false_when_lower_low():
    values = [5, 2, 5, 5, 1, 5]   # swing lows 2 then 1
    assert swings.is_higher_low(values, window=1) is False


def test_requires_two_swings():
    values = [1, 2, 1]            # only one swing high
    assert swings.is_higher_high(values, window=1) is False
