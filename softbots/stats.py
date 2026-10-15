"""
Statistics for the softbots: plays a softbot through one whole game in
Python (no browser, no animation) and reports how it did.

The "Run statistics" button in the browser asks the server for one game
at a time, so the table fills in as the results come back.
"""

import random
import time

import game_rules

WIN_TILE = 2048
MAX_STALLED_MOVES = 50  # same as the browser: give up on a bot that keeps making moves that do nothing


def add_random_tile(board):
    """Add a 2 (90% of the time) or a 4 (10%) to a random empty cell, like the real game."""
    row, col = random.choice(game_rules.empty_cells(board))
    value = 2 if random.random() < 0.9 else 4
    return game_rules.place_tile(board, row, col, value)


def play_game(bot):
    """
    Play one game with the given softbot function, following the same rules
    as the browser game. The game ends when:
    - the bot makes a 2048 tile ("won"; the browser stops the bot here too),
    - there are no moves left ("lost"),
    - or the bot returns no move, or keeps making moves that do nothing
      ("gave_up").

    Returns a dict with:
        score     the final score
        moves     how many moves the bot made
        max_tile  the biggest tile on the board at the end
        ended     "won", "lost" or "gave_up"
        seconds   how long the whole game took
    """
    board = add_random_tile(add_random_tile([[0] * 4 for _ in range(4)]))
    score = 0
    moves = 0
    stalled = 0
    ended = "lost"
    start = time.perf_counter()

    while not game_rules.is_game_over(board):
        # Bots can read the score with get_score(), like in the browser
        game_rules.set_score(score)
        direction = bot(game_rules.copy_board(board))

        if direction not in game_rules.DIRECTIONS:
            ended = "gave_up"
            break

        new_board, points, moved = game_rules.move(board, direction)
        if not moved:
            stalled += 1
            if stalled >= MAX_STALLED_MOVES:
                ended = "gave_up"
                break
            continue

        stalled = 0
        score += points
        moves += 1
        board = new_board
        if game_rules.max_tile(board) >= WIN_TILE:
            ended = "won"
            break

        board = add_random_tile(board)

    seconds = time.perf_counter() - start
    return {"score": score, "moves": moves, "max_tile": game_rules.max_tile(board),
            "ended": ended, "seconds": seconds}
