"""Central configuration for the Thai stock scanner.

All screening parameters live here so the strategy can be tuned in one place.
The two values the project owner did not specify are marked DEFAULT — confirm
them before relying on live results.
"""
import os
from dotenv import load_dotenv

# Load .env first (dev defaults), then .env.production (production overrides).
# Both files are git-ignored. .env.production takes precedence when present.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_ROOT, ".env"))
load_dotenv(os.path.join(_ROOT, ".env.production"), override=True)

# --- Indicator parameters --------------------------------------------------
MA_PERIOD = 200          # Close must be above the 200-period SMA (daily)
RSI_PERIOD = 14
RSI_LOWER = 50           # exclusive: 50 < RSI < 80
RSI_UPPER = 80
STOCH_K_PERIOD = 14      # %K lookback
STOCH_K_SMOOTH = 3       # %K smoothing (slow stochastic)
STOCH_D_PERIOD = 3       # %D smoothing
STOCH_THRESHOLD = 30     # Stoch must be below this
STOCH_LINE = "k"         # DEFAULT: test the "k" line (%K). Set to "d" for %D.

# Swing detection: a pivot is confirmed when it is the extreme over this many
# bars on each side. DEFAULT = 5. Larger = fewer, more significant swings.
SWING_WINDOW = 5

# --- Data ------------------------------------------------------------------
HISTORY_PERIOD = "2y"    # enough bars for MA200 + swing context
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TICKERS_FILE = os.path.join(_ROOT, "data", "tickers.txt")

# --- LINE Messaging API ----------------------------------------------------
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
# "broadcast" sends to all OA followers; otherwise set a userId/groupId to push.
LINE_TARGET = os.environ.get("LINE_TARGET", "broadcast")

# --- Behaviour -------------------------------------------------------------
# When DRY_RUN is on (or no token is set), results are printed, not sent.
DRY_RUN = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")
