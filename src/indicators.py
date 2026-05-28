"""Technical indicators implemented directly on pandas Series.

Implemented by hand (no TA-Lib / pandas-ta) to keep dependencies minimal and
CI-friendly, and so the exact formulas are testable and unambiguous.
"""
import numpy as np
import pandas as pd


def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple moving average. NaN until `period` bars exist."""
    return series.rolling(window=period, min_periods=period).mean()


def _rma(series: pd.Series, period: int) -> pd.Series:
    """Wilder's RMA seeded with SMA — matches TradingView ta.rma() exactly.

    pandas ewm(adjust=False) seeds from the first value, which diverges from
    TradingView's formula for the warm-up window. With 2 years of data the
    difference converges to zero, but this implementation is exact from bar 1.
    """
    values = series.to_numpy(dtype=float)
    result = np.full(len(values), np.nan)
    alpha = 1.0 / period

    for start in range(len(values) - period + 1):
        window = values[start : start + period]
        if not np.any(np.isnan(window)):
            seed_idx = start + period - 1
            result[seed_idx] = window.mean()
            prev = result[seed_idx]
            for j in range(seed_idx + 1, len(values)):
                v = values[j]
                if not np.isnan(v):
                    prev = alpha * v + (1 - alpha) * prev
                    result[j] = prev
                else:
                    result[j] = np.nan
            break

    return pd.Series(result, index=series.index)


def ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average seeded with SMA — matches TradingView ta.ema()."""
    values = series.to_numpy(dtype=float)
    result = np.full(len(values), np.nan)
    alpha = 2.0 / (period + 1)

    for start in range(len(values) - period + 1):
        window = values[start : start + period]
        if not np.any(np.isnan(window)):
            seed_idx = start + period - 1
            result[seed_idx] = window.mean()
            prev = result[seed_idx]
            for j in range(seed_idx + 1, len(values)):
                v = values[j]
                if not np.isnan(v):
                    prev = alpha * v + (1 - alpha) * prev
                    result[j] = prev
                else:
                    result[j] = np.nan
            break

    return pd.Series(result, index=series.index)


def rsi(close: pd.Series, period: int = 14, smooth: str = "rma") -> pd.Series:
    """Relative Strength Index.

    smooth="rma"  → Wilder's smoothing (TradingView ta.rsi default)
    smooth="ema"  → EMA-based smoothing (used by some Thai broker platforms)
    """
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    smooth_fn = ema if smooth == "ema" else _rma
    avg_gain = smooth_fn(gain, period)
    avg_loss = smooth_fn(loss, period)
    rs = avg_gain / avg_loss
    out = 100 - (100 / (1 + rs))
    out = out.where(avg_loss != 0, 100.0)
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
