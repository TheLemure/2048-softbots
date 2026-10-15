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

from game_rules import UP, RIGHT, DOWN, LEFT, DIRECTIONS, move,  max_tile, legal_moves, \
    empty_cells, place_tile, is_game_over, get_score, NEW_TILE_PROBABILITIES

def evaluate(board):
    """
    Evaluate the board and return a score.

    What is currently implemented in the evaluation:    
    - The number of empty cells (more is better) * 100
    - The maximum tile (higher is better) * 10
    - The score shown in the browser (higher is better)
    """
    
    num_empty_cells = len(empty_cells(board))
    return( num_empty_cells*100  +  max_tile*10  +  get_score())


def random_bot(board):
    """
    Just choose a random move out of the legal ones. 
    
    This is the simplest softbot, used as a baseline for comparison.
    """
    moves = legal_moves(board)

    if is_game_over(board):
        return None


    return random.choice(moves)


def bfs(board):
    # TODO: implement Breadth-First Search softbot
    return None


def dfs(board):
    # TODO: implement Depth-First Search softbot
    return None


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
    return None


def greedy(board):
    # TODO: implement Greedy (best-first) softbot
    return None


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
    start_temp = 5000
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

    if random.random() < math.exp(delta_e / T):
        chosen = random.choice(moves)                                 # random move
    elif delta_e >= 0:
        chosen = best_move                                # hill climbing                    # it "hit": random move
    else:
        # Missed. Keep playing the best move unless it's a bad outcome:
        # no score improvement AND another cell gets used up.
        if best_value <= current_value and best_empty < current_empty:
            chosen = None                                   # stop
        else:
            chosen = best_move
            print("H")

    # --- cool down and save T for the next call ---
    with open(temp_file, "w") as f:
        f.write(str(max(T - 1, min_temp)))

    return chosen


def minimax(board):
    # TODO: implement MiniMax softbot
    return None


def expectimax(board):
    # TODO: implement ExpectiMax softbot
    return None


# Maps the id the browser sends to the function that handles it.
# The ids must match the ones in js/softbots.js.
BOTS = {
    "random":              random_bot,
    "bfs":                 bfs,
    "dfs":                 dfs,
    "ucs":                 ucs,
    "greedy":              greedy,
    "a_star":              a_star,
    "hill_climbing":       hill_climbing,
    "simulated_annealing": simulated_annealing,
    "minimax":             minimax,
    "expectimax":          expectimax,
}