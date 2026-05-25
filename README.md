# Thai Stock Scanner

Daily screener for SET (Stock Exchange of Thailand) stocks. After market close
it pulls end-of-day data, applies a fixed set of technical criteria to every
ticker, and pushes the matches to a **LINE Official Account** once per day.

## Strategy

A stock matches only when **all** of these hold (a pullback-within-an-uptrend setup):

1. **Close > MA200** — above the 200-day simple moving average.
2. **50 < RSI(14) < 80** — bullish momentum, not overbought.
3. **Stochastic(14,3,3) %K < 30** — short-term pullback.
4. **Higher low** — latest swing low above the previous one.
5. **Higher high** — latest swing high above the previous one.

All parameters live in [`src/config.py`](src/config.py).

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Preview without sending to LINE (recommended while developing)
python -m src.main --dry-run --limit 5

# Full scan + send (needs LINE_CHANNEL_ACCESS_TOKEN)
python -m src.main

# Tests (no network needed)
pytest
```

## Configuration

Set via environment variables (see [`.env.example`](.env.example)):

| Variable | Purpose |
| --- | --- |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Messaging API token for the OA |
| `LINE_TARGET` | `broadcast` (all followers) or a userId/groupId |
| `DRY_RUN` | `1`/`true` to print instead of send |

The ticker universe is [`data/tickers.txt`](data/tickers.txt) (seeded with SET50; `.BK` suffix).

## Deployment

A scheduled GitHub Actions workflow ([`.github/workflows/scan.yml`](.github/workflows/scan.yml))
runs at 11:00 UTC (18:00 ICT) on weekdays. Add `LINE_CHANNEL_ACCESS_TOKEN`
(and optionally `LINE_TARGET`) as repository **Actions secrets**, then push to
GitHub. Trigger a manual run from the Actions tab via *Run workflow*.

> Data is from Yahoo Finance via `yfinance`; quality varies for thinly-traded
> SET names. Verify against an official source before trading on it.
