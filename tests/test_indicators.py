import numpy as np
import pandas as pd
import pytest

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


def test_ema_seeded_with_sma():
    # First non-NaN value must equal SMA of first `period` values.
    s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    out = indicators.ema(s, 3)
    assert np.isnan(out.iloc[1])            # warm-up
    assert out.iloc[2] == pytest.approx(2.0)   # seed = mean(1,2,3)
    assert not np.isnan(out.iloc[5])        # converges after seed


def test_rsi_ema_smooth_bounds():
    # EMA-smoothed RSI must stay in [0, 100] and behave directionally.
    close_up = pd.Series(np.arange(1, 50, dtype=float))
    r_up = indicators.rsi(close_up, 14, smooth="ema")
    assert r_up.iloc[-1] > 99              # all gains -> near 100

    close_down = pd.Series(np.arange(50, 1, -1, dtype=float))
    r_down = indicators.rsi(close_down, 14, smooth="ema")
    assert r_down.iloc[-1] < 1             # all losses -> near 0


def test_rsi_ema_lower_than_rma_on_recent_drop():
    # EMA reacts faster to recent losses, so RSI_EMA < RSI_RMA after a sharp drop.
    prices = list(np.linspace(1, 5, 50)) + list(np.linspace(5, 2, 20))
    close = pd.Series(prices, dtype=float)
    rma_val = indicators.rsi(close, 14, smooth="rma").iloc[-1]
    ema_val = indicators.rsi(close, 14, smooth="ema").iloc[-1]
    assert ema_val < rma_val               # EMA RSI reacts faster to the drop
