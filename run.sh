#!/bin/bash
# Daily scan runner — called by crontab at 18:00 ICT Mon-Fri.
# Logs are written to logs/scan.log (auto-rotated to keep last 30 days).

cd "$(dirname "$0")"

# Activate venv
source .venv/bin/activate

# Run scan (loads .env.production automatically via python-dotenv)
python -m src.main

# Keep only the last 30 days of log lines (~30 runs)
if [ -f logs/scan.log ]; then
    tail -n 3000 logs/scan.log > logs/scan.log.tmp && mv logs/scan.log.tmp logs/scan.log
fi
