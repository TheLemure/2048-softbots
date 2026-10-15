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
    Evaluate the board and return a score (higher is better).

    Tiles are measured by their exponent (2 -> 1, 4 -> 2, 8 -> 3, ...), so a
    2048 doesn't drown out everything else. What the evaluation rewards:
    - Empty cells: more room to move and less chance of getting stuck
    - Monotonicity: each row and column sorted in one direction, like
      64, 32, 16, 8, so tiles line up to merge into each other
    - Smoothness: neighbouring tiles close in value, so they can merge soon
    - Biggest tile in a corner, where it's out of the way
    - Losing gets a huge penalty so the search avoids it at all costs
    """
    EMPTY_WEIGHT = 2.7
    MONOTONICITY_WEIGHT = 1.0
    SMOOTHNESS_WEIGHT = 0.1
    CORNER_WEIGHT = 1.0
    GAME_OVER_SCORE = -1_000_000

    num_empty_cells = len(empty_cells(board))
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

    biggest = max(max(row) for row in exponents)
    corners = [exponents[0][0], exponents[0][-1], exponents[-1][0], exponents[-1][-1]]
    corner = biggest if biggest in corners else 0

    return (num_empty_cells * EMPTY_WEIGHT
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
    """
    Breadth-First Search: look at every sequence of moves up to MAX_DEPTH,
    level by level, and pick the first move of the sequence that leads to
    the best-scoring board.

    For simplicity this ignores the random tile added after each move.
    """
    MAX_DEPTH = 3

    if is_game_over(board):
        return None

    # Each queue entry is (board, the first move that led here, depth)
    queue = deque()
    for direction in legal_moves(board):
        new_board = move(board, direction)[0]
        queue.append((new_board, direction, 1))

    best_move = None
    best_score = -math.inf

    while queue:
        current, first_move, depth = queue.popleft()

        score = evaluate(current)
        if score > best_score:
            best_score = score
            best_move = first_move

        # Expand this board's children unless we've reached the depth limit
        if depth < MAX_DEPTH:
            for direction in legal_moves(current):
                new_board = move(current, direction)[0]
                queue.append((new_board, first_move, depth + 1))

    return best_move


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
    """
    Hill Climbing: look one move ahead and take the move that leads to
    the best-scoring board.
    """
    if is_game_over(board):
        return None

    best_move = None
    best_score = -math.inf

    for direction in legal_moves(board):
        new_board = move(board, direction)[0]
        score = evaluate(new_board)
        if score > best_score:
            best_score = score
            best_move = direction

    return best_move


def simulated_annealing(board):
    """
    Simulated Annealing: like Hill Climbing, but sometimes takes a worse
    move on purpose. Try the legal moves in random order and take each one
    with probability e^(change / temperature), where change is how much
    worse it is than the best move (so the best move is always accepted).

    The server reloads this file every move, so the temperature can't be
    stored between moves. Instead it cools down as the game score grows,
    making worse moves less and less likely.
    """
    START_TEMPERATURE = 5

    if is_game_over(board):
        return None

    temperature = START_TEMPERATURE / (1 + get_score() / 100)

    moves = legal_moves(board)
    random.shuffle(moves)

    scores = {direction: evaluate(move(board, direction)[0]) for direction in moves}
    best_score = max(scores.values())

    for direction in moves:
        change = scores[direction] - best_score  # 0 for the best move, negative otherwise
        if random.random() < math.exp(change / temperature):
            return direction


def minimax(board):
    """
    MiniMax: we pick the move (max), then assume the new tile lands in the
    worst possible cell with the worst possible value (min). Searches
    MAX_DEPTH of our moves ahead and scores the boards at the end.
    """
    MAX_DEPTH = 2

    if is_game_over(board):
        return None

    def max_value(current, depth):
        # Our turn: take the best move
        if depth == 0 or is_game_over(current):
            return evaluate(current)
        return max(min_value(move(current, direction)[0], depth)
                   for direction in legal_moves(current))

    def min_value(current, depth):
        # The game's turn: place the new tile wherever hurts us most
        cells = empty_cells(current)
        if not cells:
            return max_value(current, depth - 1)
        return min(max_value(place_tile(current, row, col, value), depth - 1)
                   for row, col in cells
                   for value in NEW_TILE_PROBABILITIES)

    best_move = None
    best_score = -math.inf

    for direction in legal_moves(board):
        score = min_value(move(board, direction)[0], MAX_DEPTH)
        if score > best_score:
            best_score = score
            best_move = direction

    return best_move


def expectimax(board):
    """
    ExpectiMax: like MiniMax, but instead of assuming the worst tile
    placement, average over every possible placement, weighted by how
    likely it is (any empty cell equally, a 2 at 90% or a 4 at 10%).
    """
    MAX_DEPTH = 2

    if is_game_over(board):
        return None

    def max_value(current, depth):
        # Our turn: take the best move
        if depth == 0 or is_game_over(current):
            return evaluate(current)
        return max(chance_value(move(current, direction)[0], depth)
                   for direction in legal_moves(current))

    def chance_value(current, depth):
        # The game's turn: average over where the new tile could appear
        cells = empty_cells(current)
        if not cells:
            return max_value(current, depth - 1)
        total = 0
        for row, col in cells:
            for value, probability in NEW_TILE_PROBABILITIES.items():
                new_board = place_tile(current, row, col, value)
                total += probability * max_value(new_board, depth - 1)
        return total / len(cells)

    best_move = None
    best_score = -math.inf

    for direction in legal_moves(board):
        score = chance_value(move(board, direction)[0], MAX_DEPTH)
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