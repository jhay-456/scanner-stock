"""Apply the five screening criteria to one ticker's OHLCV history."""
from dataclasses import dataclass
from typing import Dict, Optional

import pandas as pd

from . import config, indicators, swings


@dataclass
class ScreenResult:
    ticker: str
    close: float
    ma200: float
    rsi: float
    stoch: float
    reasons: Dict[str, bool]

    @property
    def passed(self) -> bool:
        return all(self.reasons.values())


def passes_criteria(
    close: float,
    ma: float,
    rsi_val: float,
    stoch_val: float,
    higher_low: bool,
    higher_high: bool,
) -> Dict[str, bool]:
    """Pure decision function — the heart of the strategy, easy to unit test."""
    return {
        "close_above_ma200": close > ma,
        "rsi_in_band": config.RSI_LOWER < rsi_val < config.RSI_UPPER,
        "stoch_below_threshold": stoch_val < config.STOCH_THRESHOLD,
        "higher_low": higher_low,
        "higher_high": higher_high,
    }


def evaluate(ticker: str, df: pd.DataFrame) -> Optional[ScreenResult]:
    """Compute indicators and evaluate criteria. Returns None if data is
    insufficient (too few bars, or NaN indicators at the latest bar)."""
    if df is None or len(df) < config.MA_PERIOD + config.SWING_WINDOW + 1:
        return None

    close, high, low = df["Close"], df["High"], df["Low"]

    ma_fn = indicators.ema if config.MA_TYPE == "ema" else indicators.sma
    ma = ma_fn(close, config.MA_PERIOD)
    rsi_s = indicators.rsi(close, config.RSI_PERIOD, config.RSI_SMOOTH)
    k, d = indicators.stochastic(
        high, low, close,
        config.STOCH_K_PERIOD, config.STOCH_K_SMOOTH, config.STOCH_D_PERIOD,
    )
    stoch_s = k if config.STOCH_LINE == "k" else d

    last_close = close.iloc[-1]
    last_ma = ma.iloc[-1]
    last_rsi = rsi_s.iloc[-1]
    last_stoch = stoch_s.iloc[-1]

    if pd.isna(last_ma) or pd.isna(last_rsi) or pd.isna(last_stoch):
        return None

    higher_low = swings.is_higher_low(low.to_numpy(), config.SWING_WINDOW)
    higher_high = swings.is_higher_high(high.to_numpy(), config.SWING_WINDOW)

    reasons = passes_criteria(
        last_close, last_ma, last_rsi, last_stoch, higher_low, higher_high
    )
    return ScreenResult(
        ticker=ticker,
        close=float(last_close),
        ma200=float(last_ma),
        rsi=float(last_rsi),
        stoch=float(last_stoch),
        reasons=reasons,
    )
