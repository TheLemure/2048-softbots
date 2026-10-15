// =====================================================================
// Softbots
//
// The softbot logic lives in Python (softbots/bots.py). This file builds
// the buttons and, for every move, sends the board to the Python server
// (softbots/server.py) and plays the direction it sends back:
//
//   0: up, 1: right, 2: down, 3: left
//
// Start the server with `python softbots/server.py` and open
// http://localhost:8000 (opening index.html directly won't reach Python).
// =====================================================================

var Softbots = {};

// Button order and labels. Each id must match a key in BOTS in bots.py.
Softbots.list = [
  { name: "Random",              id: "random" },
  { name: "Uniform Cost Search", id: "ucs" },
  { name: "Greedy",              id: "greedy" },
  { name: "Simulated Annealing", id: "simulated_annealing" },
  { name: "MiniMax",             id: "minimax" },
  { name: "ExpectiMax",          id: "expectimax" }
];

// Returns the board as a list of rows, board[row][col] (0 = empty),
// which is the format the Python softbots receive
Softbots.getBoard = function (game) {
  var board = [];

  for (var y = 0; y < game.size; y++) {
    board.push([]);
    for (var x = 0; x < game.size; x++) {
      var tile = game.grid.cells[x][y];
      board[y].push(tile ? tile.value : 0);
    }
  }

  return board;
};

// Ask the Python server for a move. Resolves to the server's JSON reply.
Softbots.requestMove = function (botId, board) {
  return fetch("/move", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ bot: botId, board: board })
  }).then(function (response) {
    return response.json();
  });
};

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
  this.runId      = 0;         // lets us ignore replies from a bot that was stopped
  this.buttons    = [];

  // Stop the bot if the user starts a new game themselves
  this.game.inputManager.on("restart", this.stop.bind(this));

  this.createButtons();

  if (window.location.protocol === "file:") {
    this.setStatus("Softbots need the Python server: run " +
                   "\"python softbots/server.py\" and open http://localhost:8000");
  }
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

  this.runId++;
  this.activeBot = null;
  this.buttons.forEach(function (button) {
    button.classList.remove("active");
  });

  this.setStatus(typeof message === "string" ? message : "");
};

SoftbotRunner.prototype.scheduleNextMove = function () {
  this.timer = setTimeout(this.step.bind(this), this.moveDelay);
};

// Ask the active softbot (in Python) for one move and apply it
SoftbotRunner.prototype.step = function () {
  var self  = this;
  var bot   = this.activeBot;
  var game  = this.game;
  var runId = this.runId;

  this.timer = null;
  if (!bot) return;

  if (game.isGameTerminated()) {
    this.stop(bot.name + " finished. Score: " + game.score);
    return;
  }

  Softbots.requestMove(bot.id, Softbots.getBoard(game)).then(function (reply) {
    // The bot was stopped or replaced while Python was thinking
    if (runId !== self.runId) return;

    if (reply.error) {
      console.error(reply.error);
      self.stop(bot.name + " error (see Python terminal)");
      return;
    }

    self.applyMove(bot, reply.move);
  }, function (error) {
    if (runId !== self.runId) return;

    console.error("Could not reach the Python server:", error);
    self.stop("Can't reach the Python server. Is \"python softbots/server.py\" running?");
  });
};

SoftbotRunner.prototype.applyMove = function (bot, direction) {
  var game = this.game;

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

// =====================================================================
// Softbot stats table
//
// One row per entry in Softbots.list, so adding a softbot there (and in
// BOTS in bots.py) automatically adds its row here. Python plays the
// games headlessly (softbots/stats.py); this just starts the runs and
// shows the results as they come in.
//
// To add another column, add one entry to SoftbotStats.columns.
// =====================================================================

function formatNumber(value, digits) {
  return value.toLocaleString(undefined, { minimumFractionDigits: digits,
                                           maximumFractionDigits: digits });
}

SoftbotStats.columns = [
  { title: "Avg Score", value: function (s) { return formatNumber(s.avg_score, 0); } },
  { title: "Avg Time",  value: function (s) { return formatNumber(s.avg_time, s.avg_time < 10 ? 3 : 1) + " s"; } },
  { title: "Wins",      value: function (s, games) { return s.wins + " / " + games; } },
  { title: "Avg Moves", value: function (s) { return formatNumber(s.avg_moves, 1); } }
];

function SoftbotStats(container) {
  this.table  = container.querySelector(".stats-table");
  this.note   = container.querySelector(".stats-note");
  this.games  = 100;       // replaced by the server's number once it replies
  this.data   = {};        // bot id -> latest stats from the server
  this.cells  = {};        // bot id -> { cells: [td, ...], action: td }
  this.timer  = null;

  var self = this;
  container.querySelector(".stats-run-all").addEventListener("click", function (event) {
    event.preventDefault();
    self.run(Softbots.list.map(function (bot) { return bot.id; }));
  });
  container.querySelector(".stats-stop").addEventListener("click", function (event) {
    event.preventDefault();
    self.post("/stats/cancel", {});
  });

  this.buildTable();
  this.refresh();          // shows results saved from earlier runs
}

SoftbotStats.prototype.buildTable = function () {
  var self = this;
  var head = this.table.createTHead().insertRow();

  ["Algorithm"].concat(SoftbotStats.columns.map(function (c) { return c.title; }), [""])
    .forEach(function (title) {
      var th = document.createElement("th");
      th.textContent = title;
      head.appendChild(th);
    });

  var body = this.table.createTBody();

  Softbots.list.forEach(function (bot) {
    var row = body.insertRow();
    row.insertCell().textContent = bot.name;

    var cells = SoftbotStats.columns.map(function () { return row.insertCell(); });
    var action = row.insertCell();
    action.className = "stats-action";

    self.cells[bot.id] = { cells: cells, action: action };
  });
};

// Send a request and show the reply (every endpoint answers with the latest stats)
SoftbotStats.prototype.post = function (url, body) {
  var self = this;
  return fetch(url, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(body)
  }).then(function (response) { return response.json(); })
    .then(function (reply) { self.update(reply); },
          function () { self.note.textContent = "Can't reach the Python server."; });
};

SoftbotStats.prototype.run = function (ids) {
  this.post("/stats/run", { bots: ids });
};

SoftbotStats.prototype.refresh = function () {
  var self = this;
  fetch("/stats").then(function (response) { return response.json(); })
    .then(function (reply) { self.update(reply); },
          function () { self.note.textContent = "Can't reach the Python server."; });
};

SoftbotStats.prototype.update = function (reply) {
  var self = this;
  var busy = false;

  this.games = reply.games;
  this.data  = reply.bots;

  Softbots.list.forEach(function (bot) {
    var s    = self.data[bot.id];
    var view = self.cells[bot.id];
    var hasNumbers = s && s.done > 0;

    SoftbotStats.columns.forEach(function (column, i) {
      view.cells[i].textContent = hasNumbers ? column.value(s, self.games) : "-";
    });

    view.action.textContent = "";
    view.action.title = "";

    if (s && (s.status === "running" || s.status === "queued")) {
      busy = true;
      view.action.textContent = s.status === "queued" ? "queued" : s.done + "/" + self.games;
    } else {
      var label = "Run";
      if (s && s.status === "not_implemented") label = "n/a";
      if (s && s.status === "error")           { label = "error"; view.action.title = s.message; }
      if (s && s.status === "cancelled")       label = "stopped";

      var link = document.createElement("a");
      link.className   = "stats-run";
      link.textContent = label;
      link.addEventListener("click", function (event) {
        event.preventDefault();
        self.run([bot.id]);
      });
      view.action.appendChild(link);
    }
  });

  this.note.textContent = "Each softbot plays " + this.games + " games without the animation. " +
                          "Time is how long the softbot spent thinking per game.";

  // Keep polling while anything is queued or running
  clearTimeout(this.timer);
  if (busy) this.timer = setTimeout(this.refresh.bind(this), 1000);
};
