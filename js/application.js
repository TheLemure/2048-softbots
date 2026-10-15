// Wait till the browser is ready to render the game (avoids glitches)
window.requestAnimationFrame(function () {
  var game = new GameManager(4, KeyboardInputManager, HTMLActuator, LocalStorageManager);

  new SoftbotRunner(game,
                    document.querySelector(".softbot-buttons"),
                    document.querySelector(".softbot-status"),
                    document.querySelector(".softbot-speed"));

  new StatsRunner(document.querySelector(".stats-panel"));
});
