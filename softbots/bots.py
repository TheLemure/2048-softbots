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

import random

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


def bfs(board):
    # TODO: implement Breadth-First Search softbot
    return None



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



def a_star(board):
    # TODO: implement A* softbot
    return None


def hill_climbing(board):
    # TODO: implement Hill Climbing softbot
    return None


def simulated_annealing(board):
    # TODO: implement Simulated Annealing softbot
    return None

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
    # TODO: implement ExpectiMax softbot
    return None


# Maps the id the browser sends to the function that handles it.
# The ids must match the ones in js/softbots.js.
BOTS = {
    "random":              random_bot,
    "bfs":                 bfs,
    "greedy":              greedy,
    "a_star":              a_star,
    "hill_climbing":       hill_climbing,
    "simulated_annealing": simulated_annealing,
    "minimax":             minimax,
    "expectimax":          expectimax,
}
