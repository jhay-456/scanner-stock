import numpy as np
import pandas as pd

from src import indicators


def test_sma_basic():
    s = pd.Series([1, 2, 3, 4, 5], dtype=float)
    out = indicators.sma(s, 3)
    assert np.isnan(out.iloc[1])          # warm-up
    assert out.iloc[2] == 2.0             # mean(1,2,3)
    assert out.iloc[4] == 4.0             # mean(3,4,5)


def test_rsi_bounds_and_strong_uptrend():
    close = pd.Series(np.arange(1, 50, dtype=float))   # strictly rising
    r = indicators.rsi(close, 14)
    last = r.iloc[-1]
    assert 0 <= last <= 100
    assert last > 99                       # no losses -> RSI pinned near 100


def test_rsi_strong_downtrend_is_low():
    close = pd.Series(np.arange(50, 1, -1, dtype=float))  # strictly falling
    r = indicators.rsi(close, 14)
    assert r.iloc[-1] < 1                   # no gains -> RSI near 0


def test_stochastic_bounds_and_at_high():
    n = 30
    high = pd.Series(np.linspace(10, 20, n))
    low = high - 1
    close = high.copy()                     # closing at the period high
    k, d = indicators.stochastic(high, low, close)
    assert 0 <= k.iloc[-1] <= 100
    assert k.iloc[-1] > 90                  # close at top of range -> high %K
