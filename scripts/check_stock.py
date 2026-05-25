"""Show indicator values for one stock so you can compare with TradingView.

Usage:
    python scripts/check_stock.py SCC
    python scripts/check_stock.py PTT --rows 10
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from src import config, data, indicators, swings

pd.set_option("display.float_format", "{:.2f}".format)


def check(ticker: str, rows: int = 5) -> None:
    symbol = ticker.upper()
    if not symbol.endswith(".BK"):
        symbol += ".BK"

    print(f"\nFetching {symbol}  (auto_adjust=False = raw prices like TradingView)...")
    df = data.fetch_history(symbol)
    if df is None:
        print("No data returned.")
        return

    close, high, low = df["Close"], df["High"], df["Low"]
    ma  = indicators.sma(close, config.MA_PERIOD)
    rsi = indicators.rsi(close, config.RSI_PERIOD)
    k, d = indicators.stochastic(
        high, low, close,
        config.STOCH_K_PERIOD, config.STOCH_K_SMOOTH, config.STOCH_D_PERIOD,
    )

    out = pd.DataFrame({
        "Close":  close,
        "MA200":  ma,
        "RSI14":  rsi,
        "Stoch%K": k,
        "Stoch%D": d,
    }).tail(rows)

    print(out.to_string())

    # Swing summary
    sh = swings.swing_highs(high.to_numpy(), config.SWING_WINDOW)
    sl = swings.swing_lows(low.to_numpy(),  config.SWING_WINDOW)
    print(f"\nLast 2 swing highs: {[round(v,2) for _,v in sh[-2:]]}"
          f"  → higher high: {sh[-1][1] > sh[-2][1] if len(sh)>=2 else 'n/a'}")
    print(f"Last 2 swing lows:  {[round(v,2) for _,v in sl[-2:]]}"
          f"  → higher low:  {sl[-1][1] > sl[-2][1] if len(sl)>=2 else 'n/a'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("ticker", help="Stock symbol, e.g. SCC or SCC.BK")
    parser.add_argument("--rows", type=int, default=5,
                        help="Number of recent rows to show (default 5)")
    args = parser.parse_args()
    check(args.ticker, args.rows)
