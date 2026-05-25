"""Technical indicators implemented directly on pandas Series.

Implemented by hand (no TA-Lib / pandas-ta) to keep dependencies minimal and
CI-friendly, and so the exact formulas are testable and unambiguous.
"""
import numpy as np
import pandas as pd


def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple moving average. NaN until `period` bars exist."""
    return series.rolling(window=period, min_periods=period).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index using Wilder's smoothing (RMA)."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss
    out = 100 - (100 / (1 + rs))
    # When there are no losses, RS is +inf -> RSI = 100.
    out = out.where(avg_loss != 0, 100.0)
    # Keep NaN during the warm-up window.
    out[avg_gain.isna()] = np.nan
    return out


def stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 14,
    k_smooth: int = 3,
    d_period: int = 3,
):
    """Slow stochastic. Returns (%K, %D) as a tuple of Series."""
    lowest = low.rolling(k_period, min_periods=k_period).min()
    highest = high.rolling(k_period, min_periods=k_period).max()
    raw_k = 100 * (close - lowest) / (highest - lowest)
    raw_k = raw_k.replace([np.inf, -np.inf], np.nan)  # flat range -> undefined
    k = raw_k.rolling(k_smooth, min_periods=k_smooth).mean()
    d = k.rolling(d_period, min_periods=d_period).mean()
    return k, d
