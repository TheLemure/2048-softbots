"""
Local server for the 2048 softbots.

Run from the repo root:

    python softbots/server.py

then open http://localhost:8000 in your browser.

It does two things:
  1. Serves the 2048 game files (index.html, js/, style/, ...).
  2. Answers POST /move: the browser sends {"bot": "<id>", "board": [[...]]}
     and gets back {"move": 0-3 or null} from the matching function in bots.py.
"""

import importlib
import json
import os
import sys
import traceback
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import game_rules
import bots

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PORT = 8000


class SoftbotHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=REPO_ROOT, **kwargs)

    def do_POST(self):
        if self.path != "/move":
            self.send_json(404, {"error": "Unknown endpoint " + self.path})
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            request = json.loads(self.rfile.read(length))
            bot_id = request["bot"]
            board = request["board"]
        except (ValueError, KeyError) as error:
            self.send_json(400, {"error": "Bad request: %s" % error})
            return

        try:
            # Pick up edits to the bot code without restarting the server
            importlib.reload(game_rules)
            importlib.reload(bots)

            bot = bots.BOTS.get(bot_id)
            if bot is None:
                self.send_json(404, {"error": "No softbot with id '%s' in bots.py" % bot_id})
                return

            direction = bot(board)
        except Exception:
            traceback.print_exc()
            self.send_json(500, {"error": "%s crashed:\n%s" % (bot_id, traceback.format_exc())})
            return

        self.send_json(200, {"move": direction})

    def send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        # Always load the latest JS/CSS while developing
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, format, *args):
        # Keep the terminal readable: only log errors, not every move
        if len(args) > 1 and str(args[1]).startswith(("4", "5")):
            super().log_message(format, *args)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    server = ThreadingHTTPServer(("127.0.0.1", port), SoftbotHandler)
    print("2048 softbots running at http://localhost:%d  (Ctrl+C to stop)" % port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
