"""Entry point: load tickers -> fetch -> screen -> notify.

Run the daily scan:        python -m src.main
Preview without sending:   python -m src.main --dry-run
Test a few tickers:        python -m src.main --dry-run --limit 5
Test LINE token only:      python -m src.main --test-line
"""
import argparse
import datetime
from typing import List

from . import config, data, screener, notify
from .screener import ScreenResult


def format_message(results: List[ScreenResult], scanned: int, skipped: int) -> str:
    today = datetime.date.today().isoformat()
    matches = [r for r in results if r.passed]
    lines = [
        f"📈 Thai Stock Scan — {today}",
        f"Scanned {scanned} | matched {len(matches)} | skipped {skipped}",
        "",
    ]
    if not matches:
        lines.append("วันนี้ไม่มีหุ้นผ่านเงื่อนไข 📭")
        lines.append("(No stocks matched today's criteria)")
    else:
        for r in sorted(matches, key=lambda r: r.ticker):
            sym = r.ticker.replace(".BK", "")
            lines.append(
                f"• {sym}  {r.close:.2f}  | RSI {r.rsi:.0f} | Stoch {r.stoch:.0f}"
            )
    return "\n".join(lines)


def run(limit: int | None = None) -> List[ScreenResult]:
    tickers = data.load_tickers()
    if limit:
        tickers = tickers[:limit]

    print(f"Fetching {len(tickers)} tickers...")
    batch = data.fetch_batch(tickers)

    results: List[ScreenResult] = []
    skipped = 0
    for t in tickers:
        df = batch.get(t)
        res = screener.evaluate(t, df) if df is not None else None
        if res is None:
            skipped += 1
            continue
        results.append(res)

    message = format_message(results, len(tickers), skipped)
    print(message)
    notify.send(message)
    return results


def test_line_connection() -> None:
    """Ping the LINE API to verify the token is valid — does not send a message."""
    import requests
    if not config.LINE_CHANNEL_ACCESS_TOKEN:
        print("ERROR: LINE_CHANNEL_ACCESS_TOKEN is not set. Check your .env file.")
        return
    resp = requests.get(
        "https://api.line.me/v2/bot/info",
        headers={"Authorization": f"Bearer {config.LINE_CHANNEL_ACCESS_TOKEN}"},
        timeout=10,
    )
    if resp.status_code == 200:
        info = resp.json()
        print(f"LINE token OK — bot name: {info.get('displayName', '?')}")
    else:
        print(f"LINE token FAILED — HTTP {resp.status_code}: {resp.text}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily Thai stock scanner")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print results instead of sending to LINE")
    parser.add_argument("--limit", type=int, default=None,
                        help="Only scan the first N tickers (for testing)")
    parser.add_argument("--test-line", action="store_true",
                        help="Test LINE token without running the scan")
    args = parser.parse_args()

    if args.test_line:
        test_line_connection()
        return

    if args.dry_run:
        config.DRY_RUN = True
    run(limit=args.limit)


if __name__ == "__main__":
    main()
