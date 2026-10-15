"""
Stats for the softbots: plays each bot against the game headlessly (no
browser, no animation) and records how it did.

For every bot it plays GAMES_PER_BOT games, following the same rules as the
browser game (two starting tiles, a 2 or 4 spawns after every move, the game
ends when there are no moves left or a 2048 tile is made) and reports:

    avg_score  - average final score
    avg_time   - average seconds the bot spent thinking per game
    wins       - number of games that reached 2048
    avg_moves  - average number of moves per game (wins and losses)

Nothing here needs to change when you add a softbot: any id in BOTS (bots.py)
can be benchmarked. The server (server.py) exposes this to the stats table
in the browser.
"""

import importlib
import json
import os
import queue
import random
import threading
import time
import traceback

import game_rules
import bots

GAMES_PER_BOT     = 100
WIN_TILE          = 2048
MAX_STALLED_MOVES = 50      # same idea as the browser: give up on a bot that only picks no-op moves
RESULTS_FILE      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stats_results.json")

_lock    = threading.Lock()
_queue   = queue.Queue()
_cancel  = threading.Event()
_worker  = None
_current = None             # id of the bot being benchmarked right now
_stats   = {}               # bot id -> raw totals (see _new_entry)


# ---------------------------------------------------------------- one game --

def _spawn(board):
    """Add a random 2 (90%) or 4 (10%) to a random empty cell."""
    row, col = random.choice(game_rules.empty_cells(board))
    probs = game_rules.NEW_TILE_PROBABILITIES
    value = random.choices(list(probs), weights=list(probs.values()))[0]
    return game_rules.place_tile(board, row, col, value)


def play_game(bot):
    """Play one full game. Returns (score, moves, won, seconds_thinking)."""
    board = _spawn(_spawn([[0] * 4 for _ in range(4)]))
    score = moves = stalled = 0
    won = False
    thinking = 0.0

    while not game_rules.is_game_over(board):
        if _cancel.is_set():
            raise InterruptedError

        started = time.perf_counter()
        direction = bot(game_rules.copy_board(board))
        thinking += time.perf_counter() - started

        if direction not in game_rules.DIRECTIONS:
            if moves == 0:
                raise NotImplementedError   # returned None on the very first move
            break                           # the browser stops the bot here too

        new_board, points, moved = game_rules.move(board, direction)

        if not moved:
            stalled += 1
            if stalled >= MAX_STALLED_MOVES:
                break
            continue

        stalled = 0
        score += points
        moves += 1

        if game_rules.max_tile(new_board) >= WIN_TILE:
            won = True
            break

        board = _spawn(new_board)

    return score, moves, won, thinking


# ------------------------------------------------------------ bookkeeping --

def _new_entry(status):
    return {"status": status, "done": 0, "wins": 0, "score": 0,
            "moves": 0, "time": 0.0, "message": ""}


def _run_bot(bot_id):
    global _current

    # Pick up edits to the bot code, like the server does for every move
    importlib.reload(game_rules)
    importlib.reload(bots)
    bot = bots.BOTS.get(bot_id)

    with _lock:
        _current = bot_id
        entry = _stats[bot_id] = _new_entry("running")

    try:
        if bot is None:
            raise KeyError("No softbot with id '%s' in bots.py" % bot_id)

        for _ in range(GAMES_PER_BOT):
            score, moves, won, seconds = play_game(bot)
            with _lock:                      # update after each game so the table fills in live
                entry["done"]  += 1
                entry["wins"]  += won
                entry["score"] += score
                entry["moves"] += moves
                entry["time"]  += seconds

        entry["status"] = "done"
        _save()
    except NotImplementedError:
        entry["status"] = "not_implemented"
    except InterruptedError:
        entry["status"] = "cancelled"
    except Exception as error:
        traceback.print_exc()
        entry["status"] = "error"
        entry["message"] = "%s: %s" % (type(error).__name__, error)
    finally:
        with _lock:
            _current = None
        if _queue.empty():
            _cancel.clear()


def _work():
    while True:
        _run_bot(_queue.get())


def _save():
    with _lock:
        done = {k: v for k, v in _stats.items() if v["status"] == "done"}
    try:
        with open(RESULTS_FILE, "w") as f:
            json.dump(done, f)
    except OSError:
        pass


def _load():
    try:
        with open(RESULTS_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


_stats.update(_load())   # finished runs survive a server restart


# ------------------------------------------------------------- public API --

def start(bot_ids):
    """Queue benchmark runs (one bot at a time, in the order given)."""
    global _worker
    with _lock:
        for bot_id in bot_ids:
            busy = _stats.get(bot_id, {}).get("status") in ("queued", "running")
            if not busy:
                _stats[bot_id] = _new_entry("queued")
                _queue.put(bot_id)
        if _worker is None:
            _worker = threading.Thread(target=_work, daemon=True)
            _worker.start()


def cancel():
    """Drop everything that is queued and stop the run in progress."""
    with _lock:
        while True:
            try:
                bot_id = _queue.get_nowait()
            except queue.Empty:
                break
            _stats.pop(bot_id, None)
        if _current is not None:
            _cancel.set()


def snapshot():
    """Everything the table needs, as plain JSON-able data."""
    with _lock:
        result = {}
        for bot_id, e in _stats.items():
            n = e["done"]
            result[bot_id] = {
                "status":    e["status"],
                "done":      n,
                "avg_score": e["score"] / n if n else None,
                "avg_time":  e["time"]  / n if n else None,
                "wins":      e["wins"],
                "avg_moves": e["moves"] / n if n else None,
                "message":   e["message"],
            }
        return {"games": GAMES_PER_BOT, "bots": result}
