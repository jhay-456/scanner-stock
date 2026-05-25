"""Send the daily result to a LINE Official Account via the Messaging API.

Uses broadcast (all OA followers) or push (a specific userId/groupId). When
DRY_RUN is set or no token is configured, the message is printed instead.
"""
import requests

from . import config

BROADCAST_URL = "https://api.line.me/v2/bot/message/broadcast"
PUSH_URL = "https://api.line.me/v2/bot/message/push"
MAX_LEN = 4900  # LINE text limit is 5000; leave headroom.


def _chunks(text: str, size: int = MAX_LEN):
    """Split on line boundaries so a long match list stays under the limit."""
    lines = text.split("\n")
    buf = ""
    for line in lines:
        if len(buf) + len(line) + 1 > size and buf:
            yield buf
            buf = ""
        buf += (line + "\n")
    if buf.strip():
        yield buf


def send(text: str) -> None:
    if config.DRY_RUN or not config.LINE_CHANNEL_ACCESS_TOKEN:
        print("[DRY-RUN] Would send to LINE:\n" + text)
        return

    headers = {
        "Authorization": f"Bearer {config.LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    for chunk in _chunks(text):
        message = {"type": "text", "text": chunk}
        if config.LINE_TARGET == "broadcast":
            url, payload = BROADCAST_URL, {"messages": [message]}
        else:
            url, payload = PUSH_URL, {"to": config.LINE_TARGET, "messages": [message]}
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
