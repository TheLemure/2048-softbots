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


def bfs(board):
    # TODO: implement Breadth-First Search softbot
    return None


def dfs(board):
    # TODO: implement Depth-First Search softbot
    return None


def iterative_deepening(board):
    # TODO: implement Iterative Deepening softbot
    return None


def ucs(board):
    # TODO: implement Uniform Cost Search softbot
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
    # TODO: implement Simulated Annealing softbot
    return None


def minimax(board):
    # TODO: implement MiniMax softbot
    return None


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
    "bfs":                 bfs,
    "dfs":                 dfs,
    "iterative_deepening": iterative_deepening,
    "ucs":                 ucs,
    "greedy":              greedy,
    "a_star":              a_star,
    "hill_climbing":       hill_climbing,
    "simulated_annealing": simulated_annealing,
    "minimax":             minimax,
    "expectimax":          expectimax,
}