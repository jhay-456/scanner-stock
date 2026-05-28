"""Show OHLCV + indicator values for one stock to compare with TradingView.

Usage:
    python scripts/check_stock.py SCC
    python scripts/check_stock.py PTT --rows 10
    python scripts/check_stock.py SCC --ema   # use EMA200 in screener check

TradingView comparison guide
─────────────────────────────
1. Open TradingView → search the ticker (e.g. SET:SCC) → Daily chart.
2. Add indicators: RSI(14), Stochastic(14,3,3), MA(200, SMA) and MA(200, EMA).
3. Compare the LAST row here with today's TradingView values.

   If Open/High/Low/Close DIFFER  → data-source mismatch (Yahoo vs TradingView/SET).
                                     Switch provider or accept the delta.
   If OHLCV match but RSI differs → indicator formula issue (rare after 500+ bars).
   If OHLCV match but Stoch differs → same; also check %K vs %D setting.
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from src import config, data, indicators, swings

pd.set_option("display.float_format", "{:.2f}".format)
pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 140)

_SEPARATOR = "─" * 80


def check(ticker: str, rows: int = 5, use_ema: bool = False) -> None:
    symbol = ticker.upper()
    if not symbol.endswith(".BK"):
        symbol += ".BK"

    print(f"\n{_SEPARATOR}")
    print(f"  {symbol}  |  source: Yahoo Finance (auto_adjust=False = raw prices)")
    print(f"  MA200: {config.MA_TYPE.upper()}  |  RSI smooth: {config.RSI_SMOOTH.upper()}  |  Stoch K: {config.STOCH_K_PERIOD}")
    print(_SEPARATOR)

    df = data.fetch_history(symbol)
    if df is None:
        print("No data returned — ticker may be delisted or unavailable on Yahoo.")
        return

    print(f"  Total bars fetched: {len(df)}  "
          f"({df.index[0].strftime('%Y-%m-%d')} → {df.index[-1].strftime('%Y-%m-%d')})\n")

    close, high, low, open_ = df["Close"], df["High"], df["Low"], df["Open"]

    sma200 = indicators.sma(close, config.MA_PERIOD)
    ema200 = indicators.ema(close, config.MA_PERIOD)
    rsi_   = indicators.rsi(close, config.RSI_PERIOD, config.RSI_SMOOTH)
    k, d   = indicators.stochastic(
        high, low, close,
        config.STOCH_K_PERIOD, config.STOCH_K_SMOOTH, config.STOCH_D_PERIOD,
    )

    ma_used = ema200 if (use_ema or config.MA_TYPE == "ema") else sma200
    ma_label = "EMA200" if (use_ema or config.MA_TYPE == "ema") else "SMA200"

    out = pd.DataFrame({
        "Open":         open_,
        "High":         high,
        "Low":          low,
        "Close":        close,
        "SMA200":       sma200,
        "EMA200":       ema200,
        "RSI(14)":      rsi_,
        f"Stoch%K({config.STOCH_K_PERIOD},3)": k,
        "Stoch%D(3)":                         d,
    }).tail(rows)

    out.index = out.index.strftime("%Y-%m-%d")
    out.index.name = "Date"

    print(out.to_string())

    # Screener verdict on the latest bar
    last = out.iloc[-1]
    active_ma = last["EMA200"] if (use_ema or config.MA_TYPE == "ema") else last["SMA200"]
    print(f"\n── Screener check (last bar, {ma_label}) ──────────────────────────────")
    checks = {
        f"Close({last['Close']:.2f}) > {ma_label}({active_ma:.2f})":
            last["Close"] > active_ma,
        f"50 < RSI({last['RSI(14)']:.1f}) < 80":
            config.RSI_LOWER < last["RSI(14)"] < config.RSI_UPPER,
        f"Stoch%K({last[f'Stoch%K({config.STOCH_K_PERIOD},3)']:.1f}) < {config.STOCH_THRESHOLD}":
            last[f"Stoch%K({config.STOCH_K_PERIOD},3)"] < config.STOCH_THRESHOLD,
    }
    for label, result in checks.items():
        print(f"  {'✓' if result else '✗'}  {label}")

    # Swing analysis
    sh = swings.swing_highs(high.to_numpy(), config.SWING_WINDOW)
    sl = swings.swing_lows(low.to_numpy(),  config.SWING_WINDOW)
    hh = sh[-1][1] > sh[-2][1] if len(sh) >= 2 else None
    hl = sl[-1][1] > sl[-2][1] if len(sl) >= 2 else None
    print(f"  {'✓' if hh else ('✗' if hh is False else '?')}  "
          f"Higher high: {[round(v,2) for _,v in sh[-2:]]}")
    print(f"  {'✓' if hl else ('✗' if hl is False else '?')}  "
          f"Higher low:  {[round(v,2) for _,v in sl[-2:]]}")

    all_pass = all(checks.values()) and hh and hl
    verdict = "PASS — would appear in today's scan" if all_pass else "FAIL"
    print(f"\n  Result: {verdict}")
    print(_SEPARATOR + "\n")
    print("Compare the OHLCV columns with TradingView for the same dates.")
    print("  Mismatch in Close/High/Low → Yahoo data differs from TradingView SET feed.")
    print("  Indicator mismatch with matching OHLCV → formula issue (report it).")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify indicator values vs TradingView")
    parser.add_argument("ticker", help="Stock symbol e.g. SCC or SCC.BK")
    parser.add_argument("--rows", type=int, default=5,
                        help="Number of recent rows to show (default 5)")
    parser.add_argument("--ema", action="store_true",
                        help="Force EMA200 for the screener check (overrides config MA_TYPE)")
    args = parser.parse_args()
    check(args.ticker, args.rows, use_ema=args.ema)
