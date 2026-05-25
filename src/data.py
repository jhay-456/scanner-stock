"""Load the ticker universe and fetch daily OHLCV from Yahoo Finance.

SET symbols use the `.BK` suffix (e.g. PTT.BK). For large scans, use
fetch_batch() which downloads all tickers in one network call (much faster
than one-by-one). fetch_history() is kept for single-ticker testing.
"""
from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf

from . import config


def load_tickers(path: Optional[str] = None) -> List[str]:
    path = path or config.TICKERS_FILE
    tickers: List[str] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            tickers.append(line)
    return tickers


def fetch_history(ticker: str, period: Optional[str] = None) -> Optional[pd.DataFrame]:
    """Single-ticker fetch. Useful for --limit testing."""
    period = period or config.HISTORY_PERIOD
    try:
        df = yf.Ticker(ticker).history(period=period, interval="1d", auto_adjust=False)
    except Exception:
        return None
    return df if (df is not None and not df.empty) else None


def fetch_batch(tickers: List[str], period: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    """Batch-fetch all tickers in one call. Returns {ticker: OHLCV DataFrame}.
    Tickers with no data or errors are silently omitted from the result."""
    period = period or config.HISTORY_PERIOD
    if not tickers:
        return {}

    raw = yf.download(
        tickers,
        period=period,
        interval="1d",
        auto_adjust=False,
        group_by="ticker",
        threads=True,
        progress=False,
    )

    result: Dict[str, pd.DataFrame] = {}

    if len(tickers) == 1:
        # yfinance returns a flat DataFrame (no MultiIndex) for a single ticker.
        df = raw.dropna(how="all")
        if not df.empty:
            result[tickers[0]] = df
        return result

    for t in tickers:
        try:
            df = raw[t].dropna(how="all")
            if not df.empty:
                result[t] = df
        except (KeyError, TypeError):
            pass
    return result
