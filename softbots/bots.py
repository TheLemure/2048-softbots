"""
The softbots. Each one is a function that takes the current board and
returns the direction to move:

    0 = up, 1 = right, 2 = down, 3 = left
    (or use UP, RIGHT, DOWN, LEFT from game_rules)

The board is a list of rows, board[row][col], with 0 for empty cells.
See game_rules.py for helpers to simulate moves on a copy of the board.

Returning None (or anything that isn't 0-3) stops the softbot in the browser.

The server reloads this file on every move, so after saving your changes
just click the button again; there's no need to restart the server.
"""

import math
import random
from collections import deque

from game_rules import UP, RIGHT, DOWN, LEFT, DIRECTIONS, max_tile, move, legal_moves, \
    empty_cells, place_tile, is_game_over, NEW_TILE_PROBABILITIES

def evaluate(board):
    """
    Evaluate the board and return a score. This is a simple heuristic that
    prefers boards with more empty cells and higher tiles.
    
    """
    empty = len(empty_cells(board))
    max_tile = max(max(row) for row in board)
    return( empty * 100 + max_tile * 10)

def random_bot(board):
    """
    Pick a random direction out of the moves that actually do something.

    This is the simplest possible softbot: it doesn't look ahead or score
    boards at all. Every other softbot follows the same pattern (look at
    the board, decide on a direction, return it); they just put more
    thought into the "decide" step.
    """
    # 1. Find the directions that would change the board. Moving into a
    #    wall does nothing in 2048, so picking one would waste a turn.
    moves = legal_moves(board)

    # 2. No legal moves means the game is over; returning None stops the bot.
    if is_game_over(board):
        return None

    # 3. Choose one of the legal directions at random and return it.
    #    The browser makes this move and then asks again for the next one.
    return random.choice(moves)

WIN_VALUE = 1e9


def greedy(board):
    """Choose the legal move with the best immediate board evaluation."""
    moves = legal_moves(board)

    if not moves:
        return None

    best_move = None
    best_score = float("-inf")

    for direction in moves:
        new_board, _, moved = move(board, direction)

        if not moved:
            continue

        score = evaluate(new_board)

        if score > best_score:
            best_score = score
            best_move = direction

    return best_move

def ucs(board):
    """
    Uniform Cost Search softbot.

    Explores every sequence of `lookahead` moves, including every possible
    tile spawn after each move. The cost of a step is the number of occupied
    cells after the move and spawn, so paths that keep the board emptier are
    cheaper. Returns the first move of the cheapest path.
    """
    # --- settings (edit these) ---
    lookahead = 1          # how many moves ahead each search looks
    max_nodes = 50000      # cap on nodes generated per search
    loss_penalty = 1000    # added to a path that ends in game over

    if is_game_over(board):
        return None

    total_cells = len(board) * len(board[0])
    if isinstance(NEW_TILE_PROBABILITIES, dict):
        values = list(NEW_TILE_PROBABILITIES.keys())
    else:
        values = [2, 4]

    # buckets[cost] = list of nodes with that path cost
    # node = (depth, board, first_move, dead)
    buckets = {0: [(0, board, None, False)]}
    size = 1                # total nodes waiting in all buckets
    level = 0               # cost bucket we are currently popping from
    generated = 0
    deepest_depth = 0       # fallback if the node cap is hit
    deepest_move = None

    while size > 0:
        # Move up to the cheapest non-empty bucket.
        while not buckets.get(level):
            level += 1

        depth, state, first_move, dead = buckets[level].pop()
        size -= 1

        # Goal: looked far enough ahead, or the game ended on this path.
        # The cheapest node comes out first, so this is the cheapest path.
        if depth > 0 and (depth == lookahead or dead):
            return first_move

        if depth > deepest_depth:
            deepest_depth = depth
            deepest_move = first_move

        if generated >= max_nodes:
            break

        # Expand: every legal move x every empty cell x every spawn value.
        for direction in legal_moves(state):
            moved = move([row[:] for row in state], direction)
            if isinstance(moved, tuple):     # in case move returns (board, ...)
                moved = moved[0]

            for (r, c) in empty_cells(moved):
                for value in values:
                    child = [row[:] for row in moved]
                    child[r][c] = value

                    child_dead = is_game_over(child)
                    step_cost = total_cells - len(empty_cells(child))
                    if child_dead:
                        step_cost += loss_penalty

                    child_cost = level + step_cost
                    if child_cost not in buckets:
                        buckets[child_cost] = []
                    buckets[child_cost].append((
                        depth + 1,
                        child,
                        direction if depth == 0 else first_move,
                        child_dead,
                    ))
                    size += 1
                    generated += 1

    # Node cap hit: use the first move of the deepest path reached.
    if deepest_move is not None:
        return deepest_move
    moves = legal_moves(board)
    return moves[0] if moves else None


def a_star(board):
    # TODO: implement A* softbot
    return None


def hill_climbing(board):
    # TODO: implement Hill Climbing softbot
    return None


def simulated_annealing(board):
    """
    Simulated Annealing softbot (no lookahead).

    delta_e = (score of the best move) - (score of the current board)
      - delta_e >= 0: play the best move (like hill climbing).
      - delta_e <  0: with probability e^(delta_e / T) play a random move.
                      If it doesn't hit, keep playing the best move, UNLESS
                      that move doesn't improve the score AND uses up another
                      cell, in which case stop (return None).
    T starts at 100 and drops by 1 every time the bot is used (minimum 1).
    """
    # --- settings (edit these) ---
    start_temp = 100000
    min_temp = 1                         # keeps T from reaching 0 (divide by zero)
    temp_file = "sa_temperature.txt"     # where T is remembered between moves

    if is_game_over(board):
        return None

    moves = legal_moves(board)
    if not moves:
        return None

    # --- load T (the server reloads this file every move, so a normal
    #     variable would reset to 100 each time) ---
    try:
        with open(temp_file) as f:
            T = float(f.read())
    except (OSError, ValueError):
        T = start_temp

    # A board with 2 or fewer tiles means a new game: reset the temperature.
    tiles_on_board = sum(1 for row in board for cell in row if cell != 0)
    if tiles_on_board <= 2:
        T = start_temp

    # --- score of the current board ---
    current_empty = len(empty_cells(board))
    current_value = current_empty * 100 + max_tile(board) * 10

    # --- find the best move ---
    best_move = None
    best_value = None
    best_empty = None
    for direction in moves:
        moved = move([row[:] for row in board], direction)
        if isinstance(moved, tuple):     # in case move returns (board, ...)
            moved = moved[0]

        # -1 because the random tile that spawns after the move uses up a cell
        empty_after_spawn = len(empty_cells(moved)) - 1
        value = empty_after_spawn * 100 + max_tile(moved) * 10

        if best_value is None or value > best_value:
            best_value = value
            best_move = direction
            best_empty = empty_after_spawn

    # --- annealing decision ---
    delta_e = best_value - current_value

    if delta_e >= 0:
        chosen = best_move                                  # hill climbing
    elif random.random() < math.exp(delta_e / T):
        chosen = random.choice(moves)                       # it "hit": random move
    else:
        # Missed. Keep playing the best move unless it's a bad outcome:
        # no score improvement AND another cell gets used up.
        if best_value <= current_value and best_empty < current_empty:
            chosen = None                                   # stop
        else:
            chosen = best_move

    # --- cool down and save T for the next call ---
    with open(temp_file, "w") as f:
        f.write(str(max(T - 1, min_temp)))

    return chosen


#------------------------------------------------------------------------------#

MINIMAX_DEPTH = 4


def minimax_value(board, depth, alpha, beta, maximizing):
    if max_tile(board) >= 2048:
        return WIN_VALUE + depth

    if depth == 0 or is_game_over(board):
        return evaluate(board)

    if maximizing:
        best = float("-inf")

        for direction in legal_moves(board):
            new_board, _, moved = move(board, direction)

            if not moved:
                continue

            value = minimax_value(
                new_board, depth - 1, alpha, beta, False
            )

            best = max(best, value)
            alpha = max(alpha, best)

            if alpha >= beta:
                break

        return evaluate(board) if best == float("-inf") else best

    # Chance-like opponent: choose the least favorable tile spawn.
    cells = empty_cells(board)

    if not cells:
        return evaluate(board)

    worst = float("inf")

    for row, col in cells:
        for tile, probability in NEW_TILE_PROBABILITIES.items():
            new_board = place_tile(board, row, col, tile)

            value = minimax_value(
                new_board, depth - 1, alpha, beta, True
            )

            worst = min(worst, value)
            beta = min(beta, worst)

            if alpha >= beta:
                return worst

    return worst


def minimax(board):
    best_move = None
    best_value = float("-inf")

    for direction in legal_moves(board):
        new_board, _, moved = move(board, direction)

        if not moved:
            continue

        value = minimax_value(
            new_board,
            MINIMAX_DEPTH - 1,
            best_value,
            float("inf"),
            False
        )

        if value > best_value:
            best_value = value
            best_move = direction

    return best_move

#------------------------------------------------------------------------------#

def expectimax(board):
    """
    ExpectiMax: on our turn we take the best move (max), and on the game's
    turn we average over every way the random tile could appear (chance):
    any empty cell equally likely, a 2 at 90% or a 4 at 10%.

    Looks MAX_DEPTH of our moves ahead, adds up the points those moves
    earn, and scores the boards at the end with evaluate().
    """
    MAX_DEPTH = 2

    def max_value(current, points, depth):
        # Our turn: the board is worth as much as our best move
        if depth == 0 or is_game_over(current):
            return evaluate(current, points)
        best = -math.inf
        for direction in legal_moves(current):
            new_board, gained, _ = move(current, direction)
            best = max(best, chance_value(new_board, points + gained, depth))
        return best

    def chance_value(current, points, depth):
        # The game's turn: average over every tile it could add

        # Get the rows and columns of the empty cells, so we can place a new tile in each one
        cells = empty_cells(current)
        # If there are no empty cells, the game is over and we return the score of this board
        average = 0
        for row, col in cells:
            for value, probability in NEW_TILE_PROBABILITIES.items():
                new_board = place_tile(current, row, col, value)
                average += probability * max_value(new_board, points, depth - 1) / len(cells)
        return average

    best_move = None
    best_score = -math.inf
    for direction in legal_moves(board):
        new_board, gained, _ = move(board, direction)
        score = chance_value(new_board, gained, MAX_DEPTH)
        if score > best_score:
            best_score = score
            best_move = direction

    return best_move


# Maps the id the browser sends to the function that handles it.
# The ids must match the ones in js/softbots.js.
BOTS = {
    "random":              random_bot,
    "ucs":                 ucs,
    "greedy":              greedy,
    "simulated_annealing": simulated_annealing,
    "minimax":             minimax,
    "expectimax":          expectimax,
}
