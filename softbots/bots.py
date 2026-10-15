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

from game_rules import UP, RIGHT, DOWN, LEFT, DIRECTIONS, move,  max_tile, legal_moves, \
    empty_cells, place_tile, is_game_over, get_score, NEW_TILE_PROBABILITIES

def evaluate(board, points=0):
    """
    Evaluate the board and return a score (higher is better).

    points is how many points the moves leading to this board earned
    (add up the second value returned by move() along the search path).

    Tiles are measured by their exponent (2 -> 1, 4 -> 2, 8 -> 3, ...) so
    big tiles don't drown out everything else. What is rewarded:
    - Empty cells: more room to move and less chance of getting stuck
    - Points earned by the moves that led here
    - The biggest tile
    - Monotonicity: each row and column sorted in one direction, like
      64, 32, 16, 8, so tiles line up to merge into each other
    - Smoothness: neighbouring tiles close in value, so they can merge soon
    - The biggest tile sitting in a corner
    Losing gets a huge penalty so the search avoids it at all costs.
    """
    EMPTY_WEIGHT = 2.7
    POINTS_WEIGHT = 1.0
    MAX_TILE_WEIGHT = 1.0
    MONOTONICITY_WEIGHT = 1.0
    SMOOTHNESS_WEIGHT = 0.1
    CORNER_WEIGHT = 1.0
    GAME_OVER_SCORE = -1_000_000

    num_empty_cells = len(empty_cells(board))
    # is_game_over is slow, and the game can't be over with an empty cell
    if num_empty_cells == 0 and is_game_over(board):
        return GAME_OVER_SCORE

    exponents = [[int(math.log2(value)) if value else 0 for value in row] for row in board]
    columns = [list(column) for column in zip(*exponents)]

    monotonicity = 0
    smoothness = 0
    for line in exponents + columns:
        increasing = 0
        decreasing = 0
        for a, b in zip(line, line[1:]):
            if a < b:
                increasing += b - a
            else:
                decreasing += a - b
            if a and b:
                smoothness -= abs(a - b)
        # Only penalise the line for going against its main direction
        monotonicity -= min(increasing, decreasing)

    biggest = int(math.log2(max_tile(board)))
    corners = [exponents[0][0], exponents[0][-1], exponents[-1][0], exponents[-1][-1]]
    corner = biggest if biggest in corners else 0

    return (num_empty_cells * EMPTY_WEIGHT
            + math.log2(points + 1) * POINTS_WEIGHT
            + biggest * MAX_TILE_WEIGHT
            + monotonicity * MONOTONICITY_WEIGHT
            + smoothness * SMOOTHNESS_WEIGHT
            + corner * CORNER_WEIGHT)


def random_bot(board):
    """
    Just choose a random move out of the legal ones. 
    
    This is the simplest softbot, used as a baseline for comparison.
    """
    moves = legal_moves(board)

    if is_game_over(board):
        return None


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
        # There's always at least one: a legal move never leaves the board full
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
    "greedy":              greedy,
    "simulated_annealing": simulated_annealing,
    "minimax":             minimax,
    "expectimax":          expectimax,
}