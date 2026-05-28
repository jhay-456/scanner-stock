
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Fully working and live-tested:
- `pytest` passes (19 tests, no network required)
- Batch-fetches **931 SET+mai tickers** from Yahoo Finance
- Screens against all 5 criteria and prints matches
- LINE Messaging API push confirmed working (token verified, pushing to group)
- Git repo live on GitHub; GitHub Actions cron active

## What this project does

A daily scanner for **Thai stocks (SET + mai)**. After market close, it batch-fetches EOD OHLCV for all 931 listed tickers, screens each one against 5 technical criteria, and pushes the match list to a **LINE Official Account group** once per day.

Strategy: **pullback-within-an-uptrend** — stock is in a structural uptrend, momentarily pulling back, as a potential entry.

## Screening logic

A ticker matches only when **all five** are true:

| # | Rule (Thai) | Implemented as |
|---|---|---|
| 1 | ราคาปิดมากกว่า เส้น 200 | `Close > MA(200)` — SMA or EMA, set via `MA_TYPE` |
| 2 | RSI อยู่ระหว่าง > 50–80 | `50 < RSI(14) < 80` (exclusive) |
| 3 | stoch ต่ำกว่า 30 | `Stoch %K(9,3,3) < 30` |
| 4 | ราคาต้องยก low | current swing low > previous swing low |
| 5 | (higher high, confirmed) | current swing high > previous swing high |

All parameters are in [`src/config.py`](src/config.py). Key settings:
- **`MA_TYPE`** = `"sma"` — change to `"ema"` to use EMA(200) instead of SMA(200)
- **`RSI_SMOOTH`** = `"ema"` — EMA-based smoothing (closer to Thai broker platforms). Set to `"rma"` for Wilder/TradingView style
- **`STOCH_K_PERIOD`** = `9` — matches Thai streaming platform settings
- **`STOCH_LINE`** = `"k"` — test against %K; change to `"d"` for %D
- **`SWING_WINDOW`** = `5` — pivot confirmed when extreme over 5 bars on each side

## Architecture

```
data/tickers.txt (931 symbols)
    → fetch_batch() — one yfinance batch call, auto_adjust=False (raw prices)
    → screener.evaluate() per ticker — computes MA200, RSI, Stoch, swings
    → notify.send() — LINE Messaging API push to group
```

Modules under `src/`:
- [`config.py`](src/config.py) — all tunable parameters (indicator periods, LINE env vars, DRY_RUN)
- [`data.py`](src/data.py) — `load_tickers()` + `fetch_batch()` (batch) / `fetch_history()` (single)
- [`indicators.py`](src/indicators.py) — SMA, EMA, RMA, RSI (RMA or EMA smooth), Stochastic — hand-written, no TA-Lib
- [`swings.py`](src/swings.py) — `swing_highs()` / `swing_lows()` → `is_higher_high()` / `is_higher_low()`
- [`screener.py`](src/screener.py) — `passes_criteria()` (pure, testable) + `evaluate()` (full pipeline)
- [`notify.py`](src/notify.py) — LINE Messaging API, broadcast or push, with message chunking
- [`main.py`](src/main.py) — CLI entrypoint with `--dry-run`, `--limit`, `--test-line`

## Data

- **Source**: Yahoo Finance via `yfinance`, tickers with `.BK` suffix (e.g. `PTT.BK`)
- **Prices**: `auto_adjust=False` — raw unadjusted prices. Do **not** change to `auto_adjust=True`.
- **Universe**: 931 tickers fetched from SET's API — refresh with `python scripts/fetch_tickers.py`
- **History period**: `HISTORY_PERIOD = "2y"` — needed for MA200 warm-up + swing context
- **Data source note**: Yahoo Finance and SET's own historical API return identical OHLCV for most stocks. Differences vs Thai broker streaming platforms (e.g. Stochastic diverging by >10 points) are caused by the streaming platform using different data or settings — not a code bug.

## Indicator implementation notes

- **RSI**: uses SMA-seeded RMA or EMA (controlled by `RSI_SMOOTH`). The SMA-seed matches TradingView's `ta.rma()` exactly. EMA-smooth is closer to what some Thai broker platforms display.
- **EMA / RMA**: both are SMA-seeded (first value = SMA of first `period` bars) matching TradingView's `ta.ema()` / `ta.rma()`.
- **Stochastic**: standard slow Stoch — raw_%K → SMA(k_smooth) → SMA(d_period). Formula is identical to TradingView.
- **MA200**: configurable SMA or EMA via `MA_TYPE`. Default is SMA.

## LINE integration

- **OA bot name**: Punchy
- **Token**: `LINE_CHANNEL_ACCESS_TOKEN` in `.env` (git-ignored) or GitHub Actions secret
- **Target**: `LINE_TARGET` — currently set to a group ID (`C09f...`). Set to `broadcast` to reach all followers, or a `U...` userId for a single user.
- **Message format**: plain text (v1), one message per day, chunked if > 4900 chars
- `.env` is loaded automatically via `python-dotenv`

## Deployment

Two triggers run the scan — make sure you want both active to avoid double-sends:

| Trigger | Schedule | Notes |
|---|---|---|
| Local Mac crontab | `0 18 * * 1-5` | 18:00 ICT Mon–Fri, reliable |
| GitHub Actions | `0 11 * * 1-5` (UTC) | Nominally 18:00 ICT, but GitHub delays up to ~4 h under load |

Workflow: [`.github/workflows/scan.yml`](.github/workflows/scan.yml)
- Secrets in GitHub: `LINE_CHANNEL_ACCESS_TOKEN`, `LINE_TARGET`
- To disable local cron: `crontab -r`
- To disable GitHub Actions cron: remove the `schedule:` block from `scan.yml`

## Commands

```bash
# Environment setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Daily scan + send to LINE
python -m src.main

# Preview without sending
python -m src.main --dry-run

# Test first N tickers only
python -m src.main --dry-run --limit 10

# Verify LINE token is valid (no message sent)
python -m src.main --test-line

# Verify indicator values for one stock (compare vs streaming platform)
python scripts/check_stock.py SCC
python scripts/check_stock.py TTB --rows 10
python scripts/check_stock.py TOP --ema   # force EMA200 check

# Refresh ticker universe from SET's API (931 symbols)
python scripts/fetch_tickers.py

# Get a LINE group ID (one-time setup, requires ngrok)
python scripts/get_group_id.py

# Run tests (no network needed)
pytest
pytest tests/test_indicators.py -v
```

## Key rules for future changes

- **`auto_adjust=False` must stay** — changing it breaks Stochastic parity with real platforms.
- **Indicator correctness is the whole product.** Any change to RSI/Stoch/EMA/swing logic needs a test with known input→output values first.
- **`passes_criteria()` in `screener.py` is the single source of truth** for the strategy rules — all 5 criteria live there as a pure function; test it directly, not via `evaluate()`.
- **`RSI_SMOOTH = "ema"`** is intentional — it gives values closer to Thai broker platforms than Wilder's RMA. Don't revert to `"rma"` without re-verifying against the streaming platform.
- yfinance returns empty/short frames for delisted or thinly-traded names — always guard with `None` checks; never crash on missing data.
