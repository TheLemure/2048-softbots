"""
2048 game rules in Python, so softbots can try out moves without touching
the real game in the browser.

Boards are lists of rows, read like the screen: board[row][col], with
row 0 at the top and col 0 on the left. Empty cells are 0.

    [[0, 2, 0, 0],
     [0, 0, 4, 0],
     [0, 0, 0, 0],
     [2, 0, 0, 0]]

None of these functions modify the board you pass in; they return new ones.
"""

UP, RIGHT, DOWN, LEFT = 0, 1, 2, 3
DIRECTIONS = [UP, RIGHT, DOWN, LEFT]
DIRECTION_NAMES = {UP: "up", RIGHT: "right", DOWN: "down", LEFT: "left"}

# After every move the game adds one tile to a random empty cell:
# a 2 with 90% probability, a 4 with 10% probability.
NEW_TILE_PROBABILITIES = {2: 0.9, 4: 0.1}

# The real game's score, as shown in the browser. The server updates it
# before every call to a softbot.
_current_score = 0


def copy_board(board):
    return [row[:] for row in board]


def _slide_row_left(row):
    """Slide and merge one row to the left. Returns (new_row, points)."""
    tiles = [value for value in row if value != 0]
    merged = []
    points = 0
    i = 0
    while i < len(tiles):
        # Two equal neighbours merge once; the result can't merge again this move
        if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
            merged.append(tiles[i] * 2)
            points += tiles[i] * 2
            i += 2
        else:
            merged.append(tiles[i])
            i += 1
    return merged + [0] * (len(row) - len(merged)), points


def move(board, direction):
    """
    Apply a move WITHOUT adding the random new tile.

    Returns (new_board, points_gained, moved), where moved is False if the
    move doesn't change the board (the real game ignores such moves).
    """
    size = len(board)
    new_board = copy_board(board)
    points = 0

    for i in range(size):
        # Read row/column i as a line that slides "left", then write it back
        if direction == LEFT:
            line = board[i][:]
        elif direction == RIGHT:
            line = board[i][::-1]
        elif direction == UP:
            line = [board[r][i] for r in range(size)]
        elif direction == DOWN:
            line = [board[r][i] for r in range(size)][::-1]
        else:
            raise ValueError("direction must be 0-3, got %r" % (direction,))

        line, line_points = _slide_row_left(line)
        points += line_points

        if direction == LEFT:
            new_board[i] = line
        elif direction == RIGHT:
            new_board[i] = line[::-1]
        elif direction == UP:
            for r in range(size):
                new_board[r][i] = line[r]
        else:  # DOWN
            line = line[::-1]
            for r in range(size):
                new_board[r][i] = line[r]

    return new_board, points, new_board != board


def legal_moves(board):
    """Directions that actually change the board."""
    return [d for d in DIRECTIONS if move(board, d)[2]]


def empty_cells(board):
    """List of (row, col) positions that are empty."""
    return [(r, c)
            for r, row in enumerate(board)
            for c, value in enumerate(row)
            if value == 0]


def place_tile(board, row, col, value):
    """Return a copy of the board with a tile added at (row, col)."""
    new_board = copy_board(board)
    new_board[row][col] = value
    return new_board


def is_game_over(board):
    return not legal_moves(board)


def max_tile(board):
    return max(max(row) for row in board)


def set_score(score):
    """Called by the server with the browser's score before each move."""
    global _current_score
    _current_score = score


def get_score():
    """The actual game score shown in the browser right now."""
    return _current_score
