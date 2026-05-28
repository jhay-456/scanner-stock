"""Fetch daily OHLCV from Settrade (www.settrade.com) REST API.

Inspired by UncleEngineer/ThaiStock — updated for the new Settrade website
which replaced classic.settrade.com.

Limitation: the public API returns ~117 bars (≈6 months) regardless of the
date range requested. Sufficient for RSI(14) and Stoch(9,3,3) but NOT for
SMA/EMA(200).  Use data.py (Yahoo Finance) when you need 2-year history.

Usage:
    from src.data_settrade import fetch_history
    df = fetch_history("TTB")   # or "TTB.BK" — .BK suffix is stripped
"""
import time
from datetime import date
from typing import Optional

import pandas as pd
import requests

# Column mapping: Settrade API field → standard DataFrame column name
# Index:  [0]Date  [1]Open  [2]High  [3]Low  [4]Avg  [5]Close
#         [6]Change  [7]%Change  [8]Volume  [9]Value
_COL_MAP = {
    "open":        "Open",
    "high":        "High",
    "low":         "Low",
    "close":       "Close",
    "totalVolume": "Volume",
    "average":     "Average",
}

_BASE_URL = "https://www.settrade.com/api/set/stock/{code}/historical-trading"
_SET_INFO  = "https://www.set.or.th/api/set/stock/{code}/info"

# Shared session — warm up once, reuse for all subsequent calls
_session: Optional[requests.Session] = None


def _make_session(code: str) -> requests.Session:
    """Create and warm up a session for the Settrade API."""
    s = requests.Session()
    s.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://www.settrade.com",
        "Referer": f"https://www.settrade.com/th/equities/quote/{code}/historical-data",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
    })
    # Visit the page to pick up Imperva session cookies
    try:
        s.get(
            f"https://www.settrade.com/th/equities/quote/{code}/historical-data",
            timeout=12,
        )
        time.sleep(0.3)
    except Exception:
        pass
    return s


def fetch_history(symbol: str) -> Optional[pd.DataFrame]:
    """Return ~117 bars of daily OHLCV from Settrade for *symbol*.

    *symbol* can be bare (``TTB``) or with the Yahoo suffix (``TTB.BK``).
    Returns a DataFrame indexed by timezone-aware Bangkok dates with columns
    Open / High / Low / Close / Volume, sorted oldest-first.
    Returns ``None`` if the ticker is not found or the request fails.
    """
    code = symbol.upper().replace(".BK", "")
    s = _make_session(code)

    today = date.today()
    params = {
        "start":    "2020-01-01",   # API ignores this; included for clarity
        "end":      today.strftime("%Y-%m-%d"),
        "language": "en",
    }
    try:
        r = s.get(_BASE_URL.format(code=code), params=params, timeout=15)
        if r.status_code != 200:
            return None
        rows = r.json()
        if not rows:
            return None
    except Exception:
        return None

    df = pd.DataFrame(rows)
    df["date"] = (
        pd.to_datetime(df["date"])
        .dt.tz_convert("Asia/Bangkok")
        .dt.normalize()
    )
    df = df.sort_values("date").drop_duplicates("date").set_index("date")
    df = df.rename(columns=_COL_MAP)

    # Append today's bar if the historical endpoint hasn't published it yet
    today_ts = pd.Timestamp(today, tz="Asia/Bangkok")
    if today_ts not in df.index:
        today_bar = _fetch_today_bar(code)
        if today_bar is not None:
            df.loc[today_ts] = today_bar
            df = df.sort_index()

    keep = [c for c in ("Open", "High", "Low", "Close", "Volume") if c in df.columns]
    return df[keep].astype(float, errors="ignore") if not df.empty else None


def _fetch_today_bar(code: str) -> Optional[dict]:
    """Fetch today's intraday snapshot from SET /info endpoint."""
    try:
        s2 = requests.Session()
        s2.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, */*",
            "Referer": "https://www.set.or.th/",
        })
        s2.get(
            "https://www.set.or.th/en/market/product/stock/quote/overview.html",
            timeout=8,
        )
        r = s2.get(_SET_INFO.format(code=code), timeout=8)
        if r.status_code == 200:
            info = r.json()
            return {
                "Open":   info.get("open"),
                "High":   info.get("high"),
                "Low":    info.get("low"),
                "Close":  info.get("last"),
                "Volume": info.get("totalVolume"),
            }
    except Exception:
        pass
    return None
