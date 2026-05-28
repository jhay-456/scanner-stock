"""Show OHLCV + indicator values for one stock to compare with your streaming platform.

Data sources:
  Settrade (default) — official SET data via www.settrade.com, ~117 bars.
                       RSI and Stoch values match Thai broker streaming platforms.
  Yahoo Finance      — used for MA200 only (needs 200+ bars).

Usage:
    python scripts/check_stock.py TTB
    python scripts/check_stock.py TOP --rows 10
    python scripts/check_stock.py SCC --yahoo     # force Yahoo for all indicators
    python scripts/check_stock.py SCC --ema       # use EMA200 in screener check

TradingView / Streaming comparison guide
─────────────────────────────────────────
1. Open your streaming platform → search the ticker → Daily chart.
2. Add: RSI(14), Stochastic(9,3,3), MA(200 SMA) and MA(200 EMA).
3. Compare the LAST row here with today's platform values.

   OHLCV differs       → data-source mismatch (Yahoo vs platform)
   OHLCV match, RSI differs  → indicator formula issue
   OHLCV match, Stoch differs → same; also check %K vs %D setting
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from src import config, data, data_settrade, indicators, swings

pd.set_option("display.float_format", "{:.2f}".format)
pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 150)

_SEP = "─" * 82


def check(ticker: str, rows: int = 5, use_yahoo: bool = False, use_ema: bool = False) -> None:
    symbol = ticker.upper()
    if not symbol.endswith(".BK"):
        symbol += ".BK"

    # ── Settrade data (RSI + Stoch) ───────────────────────────────────────────
    if not use_yahoo:
        print(f"\n{_SEP}")
        print(f"  {symbol}  |  Fetching from Settrade (official SET data)...")
        st_df = data_settrade.fetch_history(symbol)
    else:
        st_df = None

    if st_df is None:
        print(f"  Settrade unavailable — falling back to Yahoo Finance.")
        use_yahoo = True

    # ── Yahoo Finance data (MA200 + fallback) ─────────────────────────────────
    print(f"  Fetching from Yahoo Finance (needed for MA200)..." if not use_yahoo
          else f"\n{_SEP}\n  {symbol}  |  source: Yahoo Finance")
    yf_df = data.fetch_history(symbol)

    if yf_df is None and st_df is None:
        print("No data returned from either source.")
        return

    # Decide which price series to use for RSI / Stoch
    price_df = st_df if (st_df is not None and not use_yahoo) else yf_df
    src_label = "Settrade" if (st_df is not None and not use_yahoo) else "Yahoo Finance"

    close_p = price_df["Close"]
    high_p  = price_df["High"]
    low_p   = price_df["Low"]

    rsi_s = indicators.rsi(close_p, config.RSI_PERIOD, config.RSI_SMOOTH)
    k, d  = indicators.stochastic(
        high_p, low_p, close_p,
        config.STOCH_K_PERIOD, config.STOCH_K_SMOOTH, config.STOCH_D_PERIOD,
    )

    # MA200 always from Yahoo (needs 200+ bars)
    ma_src = yf_df if yf_df is not None else price_df
    close_y = ma_src["Close"]
    sma200  = indicators.sma(close_y, config.MA_PERIOD)
    ema200  = indicators.ema(close_y, config.MA_PERIOD)

    # ── Build display table ───────────────────────────────────────────────────
    # Align MA200 to the price_df index (last N rows of Settrade may not be in Yahoo)
    sma_aligned = sma200.reindex(close_p.index, method="ffill")
    ema_aligned = ema200.reindex(close_p.index, method="ffill")

    out = pd.DataFrame({
        "Open":    price_df["Open"],
        "High":    high_p,
        "Low":     low_p,
        "Close":   close_p,
        f"SMA200({'YF' if yf_df is not None else '?'})": sma_aligned,
        f"EMA200({'YF' if yf_df is not None else '?'})": ema_aligned,
        f"RSI(14)[{src_label[:2]}]":                     rsi_s,
        f"Stoch%K({config.STOCH_K_PERIOD},3)[{src_label[:2]}]": k,
        "Stoch%D(3)": d,
    }).tail(rows)

    out.index = out.index.strftime("%Y-%m-%d")
    out.index.name = "Date"

    print(f"\n{_SEP}")
    print(f"  {symbol}  |  RSI+Stoch: {src_label} ({len(price_df)} bars)  |  "
          f"MA200: Yahoo Finance ({len(ma_src)} bars)")
    print(f"  Config: MA={config.MA_TYPE.upper()}  RSI_smooth={config.RSI_SMOOTH.upper()}  "
          f"Stoch_K={config.STOCH_K_PERIOD}")
    print(_SEP)
    print(out.to_string())

    # ── Live screener verdict ─────────────────────────────────────────────────
    last = out.iloc[-1]
    ma_col  = f"EMA200({'YF' if yf_df is not None else '?'})" if (use_ema or config.MA_TYPE == "ema") \
              else f"SMA200({'YF' if yf_df is not None else '?'})"
    rsi_col = f"RSI(14)[{src_label[:2]}]"
    stoch_col = f"Stoch%K({config.STOCH_K_PERIOD},3)[{src_label[:2]}]"

    active_ma = last[ma_col]
    ma_label  = "EMA200" if (use_ema or config.MA_TYPE == "ema") else "SMA200"

    checks = {
        f"Close({last['Close']:.2f}) > {ma_label}({active_ma:.2f})":
            last["Close"] > active_ma,
        f"50 < RSI({last[rsi_col]:.1f}) < 80":
            config.RSI_LOWER < last[rsi_col] < config.RSI_UPPER,
        f"Stoch%K({last[stoch_col]:.1f}) < {config.STOCH_THRESHOLD}":
            last[stoch_col] < config.STOCH_THRESHOLD,
    }
    print(f"\n── Screener check (last bar, {ma_label} from Yahoo) ──────────────────────")
    for label, result in checks.items():
        print(f"  {'✓' if result else '✗'}  {label}")

    # Swing analysis (always from Yahoo for full history)
    if yf_df is not None:
        sh = swings.swing_highs(yf_df["High"].to_numpy(), config.SWING_WINDOW)
        sl = swings.swing_lows(yf_df["Low"].to_numpy(),  config.SWING_WINDOW)
        hh = sh[-1][1] > sh[-2][1] if len(sh) >= 2 else None
        hl = sl[-1][1] > sl[-2][1] if len(sl) >= 2 else None
        print(f"  {'✓' if hh else ('✗' if hh is False else '?')}  "
              f"Higher high: {[round(v,2) for _,v in sh[-2:]]}")
        print(f"  {'✓' if hl else ('✗' if hl is False else '?')}  "
              f"Higher low:  {[round(v,2) for _,v in sl[-2:]]}")
        all_pass = all(checks.values()) and bool(hh) and bool(hl)
    else:
        all_pass = all(checks.values())

    verdict = "PASS — would appear in today's scan" if all_pass else "FAIL"
    print(f"\n  Result: {verdict}")
    print(_SEP + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify indicator values vs streaming platform")
    parser.add_argument("ticker", help="Stock symbol e.g. TTB or TTB.BK")
    parser.add_argument("--rows",  type=int, default=5,
                        help="Number of recent rows to show (default 5)")
    parser.add_argument("--yahoo", action="store_true",
                        help="Use Yahoo Finance for all data (skip Settrade)")
    parser.add_argument("--ema",   action="store_true",
                        help="Force EMA200 for the screener check")
    args = parser.parse_args()
    check(args.ticker, args.rows, use_yahoo=args.yahoo, use_ema=args.ema)
