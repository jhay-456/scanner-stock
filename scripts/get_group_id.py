"""One-time helper to capture your LINE group ID.

Steps:
1. pip install flask
2. python scripts/get_group_id.py
3. In a second terminal: ngrok http 5000
4. Copy the https://xxxx.ngrok-free.app URL
5. Paste it + "/webhook" into LINE Developers Console → Messaging API → Webhook URL
6. Send any message in the group
7. Group ID is printed here → copy it into .env as LINE_TARGET
"""
import json
from flask import Flask, request

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_json(silent=True) or {}
    for event in body.get("events", []):
        source = event.get("source", {})
        src_type = source.get("type")
        if src_type == "group":
            group_id = source.get("groupId")
            print(f"\n✅  GROUP ID: {group_id}")
            print(f"    Set in .env:  LINE_TARGET={group_id}\n")
        elif src_type == "room":
            print(f"\n✅  ROOM ID: {source.get('roomId')}\n")
        elif src_type == "user":
            print(f"\n   (message from user, not a group: {source.get('userId')})\n")
    return "OK", 200

if __name__ == "__main__":
    print("Webhook listening on http://localhost:5000/webhook")
    print("Now run:  ngrok http 5000")
    app.run(port=5000, debug=False)
