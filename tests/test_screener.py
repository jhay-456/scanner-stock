from src import screener
from src.screener import passes_criteria


def _all_pass_kwargs():
    return dict(
        close=110.0, ma=100.0,       # above MA200
        rsi_val=60.0,                # 50 < 60 < 80
        stoch_val=20.0,              # < 30
        higher_low=True, higher_high=True,
    )


def test_all_criteria_pass():
    reasons = passes_criteria(**_all_pass_kwargs())
    assert all(reasons.values())


def test_close_below_ma_fails():
    kw = _all_pass_kwargs()
    kw["close"] = 90.0
    reasons = passes_criteria(**kw)
    assert reasons["close_above_ma200"] is False
    assert not all(reasons.values())


def test_rsi_band_is_exclusive():
    kw = _all_pass_kwargs()
    kw["rsi_val"] = 50.0             # boundary -> excluded
    assert passes_criteria(**kw)["rsi_in_band"] is False
    kw["rsi_val"] = 80.0
    assert passes_criteria(**kw)["rsi_in_band"] is False
    kw["rsi_val"] = 50.1
    assert passes_criteria(**kw)["rsi_in_band"] is True


def test_stoch_threshold_is_exclusive():
    kw = _all_pass_kwargs()
    kw["stoch_val"] = 30.0           # boundary -> excluded
    assert passes_criteria(**kw)["stoch_below_threshold"] is False
    kw["stoch_val"] = 29.9
    assert passes_criteria(**kw)["stoch_below_threshold"] is True


def test_missing_swing_structure_fails():
    kw = _all_pass_kwargs()
    kw["higher_high"] = False
    assert not all(passes_criteria(**kw).values())


def test_evaluate_returns_none_on_short_history():
    import pandas as pd
    df = pd.DataFrame({"Open": [1], "High": [1], "Low": [1], "Close": [1]})
    assert screener.evaluate("X.BK", df) is None
