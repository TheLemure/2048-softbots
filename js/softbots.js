// =====================================================================
// Softbots
//
// Each softbot is a function that receives the current GameManager and
// returns the direction it wants to move:
//
//   0: up, 1: right, 2: down, 3: left
//
// Returning null/undefined (or anything that isn't 0-3) stops the bot.
//
// Useful things on the `game` object (see game_manager.js):
//   game.grid                  - Grid of Tile objects (game.grid.cells[x][y])
//   game.score                 - current score
//   game.size                  - board width/height (4)
//   game.getVector(direction)  - {x, y} vector for a direction
//   game.movesAvailable()      - true if any move is still possible
//
// IMPORTANT: a softbot must NOT call game.move() itself or modify
// game.grid directly; the runner below makes the chosen move. Bots that
// need to look ahead should work on their own copy of the board
// (e.g. Softbots.getBoard(game)).
// =====================================================================

var Softbots = {};

// Returns a plain 2D array of tile values (0 = empty), indexed board[x][y]
Softbots.getBoard = function (game) {
  var board = [];

  for (var x = 0; x < game.size; x++) {
    board.push([]);
    for (var y = 0; y < game.size; y++) {
      var tile = game.grid.cells[x][y];
      board[x].push(tile ? tile.value : 0);
    }
  }

  return board;
};

// --- Softbot stubs ----------------------------------------------------

Softbots.random = function (game) {
  // TODO: implement Random softbot
  return null;
};

Softbots.bfs = function (game) {
  // TODO: implement Breadth-First Search softbot
  return null;
};

Softbots.dfs = function (game) {
  // TODO: implement Depth-First Search softbot
  return null;
};

Softbots.iterativeDeepening = function (game) {
  // TODO: implement Iterative Deepening softbot
  return null;
};

Softbots.ucs = function (game) {
  // TODO: implement Uniform Cost Search softbot
  return null;
};

Softbots.greedy = function (game) {
  // TODO: implement Greedy (best-first) softbot
  return null;
};

Softbots.aStar = function (game) {
  // TODO: implement A* softbot
  return null;
};

Softbots.hillClimbing = function (game) {
  // TODO: implement Hill Climbing softbot
  return null;
};

Softbots.simulatedAnnealing = function (game) {
  // TODO: implement Simulated Annealing softbot
  return null;
};

Softbots.miniMax = function (game) {
  // TODO: implement MiniMax softbot
  return null;
};

Softbots.expectiMax = function (game) {
  // TODO: implement ExpectiMax softbot
  return null;
};

// Button order and labels for the softbot panel
Softbots.list = [
  { name: "Random",              fn: Softbots.random },
  { name: "BFS",                 fn: Softbots.bfs },
  { name: "DFS",                 fn: Softbots.dfs },
  { name: "Iterative Deepening", fn: Softbots.iterativeDeepening },
  { name: "UCS",                 fn: Softbots.ucs },
  { name: "Greedy",              fn: Softbots.greedy },
  { name: "A*",                  fn: Softbots.aStar },
  { name: "Hill Climbing",       fn: Softbots.hillClimbing },
  { name: "Simulated Annealing", fn: Softbots.simulatedAnnealing },
  { name: "MiniMax",             fn: Softbots.miniMax },
  { name: "ExpectiMax",          fn: Softbots.expectiMax }
];

// =====================================================================
// Softbot runner: builds the buttons, restarts the game, and plays the
// chosen softbot's moves one at a time so the user can watch.
// =====================================================================

function SoftbotRunner(game, container, status) {
  this.game      = game;
  this.container = container;
  this.status    = status;

  this.moveDelay        = 150; // ms between moves (tile animation is 100ms)
  this.maxStalledMoves  = 50;  // stop if the bot keeps picking moves that do nothing

  this.timer      = null;
  this.activeBot  = null;
  this.buttons    = [];

  // Stop the bot if the user starts a new game themselves
  this.game.inputManager.on("restart", this.stop.bind(this));

  this.createButtons();
}

SoftbotRunner.prototype.createButtons = function () {
  var self = this;

  Softbots.list.forEach(function (bot) {
    var button = document.createElement("a");
    button.className   = "softbot-button";
    button.textContent = bot.name;

    button.addEventListener("click", function (event) {
      event.preventDefault();
      self.start(bot, button);
    });

    self.container.appendChild(button);
    self.buttons.push(button);
  });
};

// Start a fresh game and run the given softbot
SoftbotRunner.prototype.start = function (bot, button) {
  this.stop();

  this.game.restart();

  this.activeBot     = bot;
  this.stalledMoves  = 0;
  button.classList.add("active");
  this.setStatus("Running: " + bot.name);

  this.scheduleNextMove();
};

SoftbotRunner.prototype.stop = function (message) {
  if (this.timer) {
    clearTimeout(this.timer);
    this.timer = null;
  }

  this.activeBot = null;
  this.buttons.forEach(function (button) {
    button.classList.remove("active");
  });

  this.setStatus(typeof message === "string" ? message : "");
};

SoftbotRunner.prototype.scheduleNextMove = function () {
  this.timer = setTimeout(this.step.bind(this), this.moveDelay);
};

// Ask the active softbot for one move and apply it
SoftbotRunner.prototype.step = function () {
  var bot  = this.activeBot;
  var game = this.game;

  this.timer = null;
  if (!bot) return;

  if (game.isGameTerminated()) {
    this.stop(bot.name + " finished. Score: " + game.score);
    return;
  }

  var direction;
  try {
    direction = bot.fn(game);
  } catch (error) {
    console.error(bot.name + " softbot threw an error:", error);
    this.stop(bot.name + " crashed (see console)");
    return;
  }

  if ([0, 1, 2, 3].indexOf(direction) === -1) {
    this.stop(bot.name + " returned no move (not implemented?)");
    return;
  }

  var before = JSON.stringify(game.grid.serialize());
  game.move(direction);

  if (JSON.stringify(game.grid.serialize()) === before) {
    this.stalledMoves++;
    if (this.stalledMoves >= this.maxStalledMoves) {
      this.stop(bot.name + " is stuck making moves that do nothing");
      return;
    }
  } else {
    this.stalledMoves = 0;
  }

  this.scheduleNextMove();
};

SoftbotRunner.prototype.setStatus = function (text) {
  if (this.status) this.status.textContent = text;
};
