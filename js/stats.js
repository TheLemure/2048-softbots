// =====================================================================
// Statistics
//
// The "Run statistics" button plays every softbot in Softbots.list a set
// number of games and shows two tables:
//   - Results: average score, win percentage (games that reached 2048),
//     average moves per game, and average time per game and per move
//   - How often each softbot reached each tile, and how its games ended
//     (won, lost, or gave up)
//
// The games are played in Python without the browser (softbots/stats.py),
// one request per game, so the tables fill in as the results come back.
// =====================================================================

// Ask the Python server to play one whole game with a softbot. Resolves to
// {score, moves, max_tile, ended, seconds}, or {error} if the bot crashed.
Softbots.requestStatsGame = function (botId) {
  return fetch("/stats/game", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ bot: botId })
  }).then(function (response) {
    return response.json();
  });
};

function StatsRunner(container) {
  this.input        = container.querySelector(".stats-games");
  this.button       = container.querySelector(".stats-button");
  this.status       = container.querySelector(".stats-status");
  this.resultsTbody = container.querySelector(".stats-results tbody");
  this.tilesTbody   = container.querySelector(".stats-tiles tbody");

  this.running = false;
  this.runId   = 0;   // lets us ignore replies from a run that was stopped
  this.rows    = {};  // bot id -> {results: row, tiles: row}

  var self = this;
  this.button.addEventListener("click", function (event) {
    event.preventDefault();
    if (self.running) {
      self.stop("Stopped.");
    } else {
      self.start();
    }
  });
}

// The "Reached at least" columns. They must match the table in index.html.
StatsRunner.tiles = [128, 256, 512, 1024];

StatsRunner.prototype.start = function () {
  var games = parseInt(this.input.value, 10);
  if (!(games >= 1)) {
    this.setStatus("Enter how many games each softbot should play (1 or more).");
    return;
  }

  this.games   = games;
  this.running = true;
  this.runId++;
  this.button.textContent = "Stop";
  this.input.disabled     = true;

  this.createRows();
  this.playNext(this.runId, 0, this.newTotals());
};

StatsRunner.prototype.stop = function (message) {
  // A game that is already running in Python still finishes, but its
  // result is ignored
  this.runId++;
  this.running = false;
  this.button.textContent = "Run statistics";
  this.input.disabled     = false;
  this.setStatus(message);
};

StatsRunner.prototype.newTotals = function () {
  var reached = {};
  StatsRunner.tiles.forEach(function (tile) {
    reached[tile] = 0;
  });

  return {
    games:   0,
    score:   0,
    moves:   0,
    seconds: 0,
    reached: reached,                          // tile -> games that reached at least it
    ended:   { won: 0, lost: 0, gave_up: 0 }   // how many games ended each way
  };
};

// One row per softbot in each table, filled with dashes until its games come back
StatsRunner.prototype.createRows = function () {
  var self = this;

  this.resultsTbody.innerHTML = "";
  this.tilesTbody.innerHTML   = "";
  this.rows = {};

  Softbots.list.forEach(function (bot) {
    self.rows[bot.id] = {
      results: self.addRow(self.resultsTbody, bot.name, 6),
      tiles:   self.addRow(self.tilesTbody, bot.name, StatsRunner.tiles.length + 3)
    };
    self.rows[bot.id].results.children[1].textContent = "0 / " + self.games;
  });
};

// Add a row with the softbot's name followed by `cells` dashes
StatsRunner.prototype.addRow = function (tbody, name, cells) {
  var row = document.createElement("tr");

  for (var i = 0; i <= cells; i++) {
    var cell = document.createElement("td");
    cell.textContent = i === 0 ? name : "-";
    row.appendChild(cell);
  }

  tbody.appendChild(row);
  return row;
};

// Play the next game: game number totals.games + 1 of the softbot at
// botIndex. Moves on to the next softbot once this one has played them all.
StatsRunner.prototype.playNext = function (runId, botIndex, totals) {
  var self = this;

  if (runId !== this.runId) return;

  if (botIndex >= Softbots.list.length) {
    this.stop("Done: every softbot played " + this.games + " games.");
    return;
  }

  var bot = Softbots.list[botIndex];
  if (totals.games >= this.games) {
    this.playNext(runId, botIndex + 1, this.newTotals());
    return;
  }

  this.setStatus("Playing " + bot.name + ": game " + (totals.games + 1) +
                 " of " + this.games + "...");

  Softbots.requestStatsGame(bot.id).then(function (reply) {
    if (runId !== self.runId) return;

    if (reply.error) {
      // Skip the rest of this softbot's games and carry on with the next one
      console.error(reply.error);
      self.showError(bot);
      self.playNext(runId, botIndex + 1, self.newTotals());
      return;
    }

    totals.games   += 1;
    totals.score   += reply.score;
    totals.moves   += reply.moves;
    totals.seconds += reply.seconds;
    totals.ended[reply.ended] += 1;
    StatsRunner.tiles.forEach(function (tile) {
      if (reply.max_tile >= tile) totals.reached[tile] += 1;
    });
    self.showTotals(bot, totals);

    self.playNext(runId, botIndex, totals);
  }, function (error) {
    if (runId !== self.runId) return;

    console.error("Could not reach the Python server:", error);
    self.stop("Can't reach the Python server. Is \"python softbots/server.py\" running?");
  });
};

StatsRunner.prototype.showTotals = function (bot, totals) {
  var self    = this;
  var games   = totals.games;
  var results = this.rows[bot.id].results.children;
  var tiles   = this.rows[bot.id].tiles.children;

  results[1].textContent = games + " / " + this.games;
  results[2].textContent = Math.round(totals.score / games);
  results[3].textContent = this.percent(totals.ended.won, games);
  results[4].textContent = Math.round(totals.moves / games);
  results[5].textContent = this.formatTime(totals.seconds / games);
  // A bot that gives up straight away makes no moves at all
  results[6].textContent = totals.moves ? this.formatTime(totals.seconds / totals.moves) : "-";

  StatsRunner.tiles.forEach(function (tile, i) {
    tiles[1 + i].textContent = self.percent(totals.reached[tile], games);
  });
  var ended = 1 + StatsRunner.tiles.length;
  tiles[ended].textContent     = this.percent(totals.ended.won, games);
  tiles[ended + 1].textContent = this.percent(totals.ended.lost, games);
  tiles[ended + 2].textContent = this.percent(totals.ended.gave_up, games);
};

StatsRunner.prototype.showError = function (bot) {
  var cells = this.rows[bot.id].results.children;
  cells[1].textContent = "Error (see Python terminal)";
};

StatsRunner.prototype.percent = function (count, games) {
  return Math.round(100 * count / games) + "%";
};

StatsRunner.prototype.formatTime = function (seconds) {
  var ms = seconds * 1000;
  if (ms < 10)   return ms.toFixed(2) + " ms";  // e.g. Random's moves take a fraction of a ms
  if (ms < 1000) return Math.round(ms) + " ms";
  return seconds.toFixed(2) + " s";
};

StatsRunner.prototype.setStatus = function (text) {
  this.status.textContent = text || "";
};
