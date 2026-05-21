let gameId = "";
let currentProblemId = "";
let secondsLeft = 0;
let timerId = null;

const startScreen = document.querySelector("#start-screen");
const gameScreen = document.querySelector("#game-screen");
const startForm = document.querySelector("#start-form");
const answerForm = document.querySelector("#answer-form");
const playerNameInput = document.querySelector("#player-name");
const answerInput = document.querySelector("#answer-input");
const currentPlayer = document.querySelector("#current-player");
const timer = document.querySelector("#timer");
const score = document.querySelector("#score");
const problemText = document.querySelector("#problem-text");
const message = document.querySelector("#message");
const leaderboard = document.querySelector("#leaderboard");
const refreshScore = document.querySelector("#refresh-score");


async function sendJson(url, data) {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  return response.json();
}


function showProblem(problem) {
  currentProblemId = problem.id;
  problemText.textContent = problem.text;
  answerInput.value = "";
  answerInput.focus();
}


function showLeaderboard(rows) {
  leaderboard.innerHTML = "";

  if (rows.length === 0) {
    const item = document.createElement("li");
    item.textContent = "Пока нет результатов";
    leaderboard.appendChild(item);
    return;
  }

  for (const row of rows) {
    const item = document.createElement("li");
    item.textContent = row.name + " ";

    const points = document.createElement("span");
    points.textContent = row.score + " очков";

    item.appendChild(points);
    leaderboard.appendChild(item);
  }
}


async function loadLeaderboard() {
  const response = await fetch("/api/leaderboard");
  const data = await response.json();
  showLeaderboard(data.leaderboard);
}


function stopTimer() {
  if (timerId !== null) {
    clearInterval(timerId);
    timerId = null;
  }
}


function startTimer() {
  stopTimer();
  timer.textContent = secondsLeft;

  timerId = setInterval(async function () {
    secondsLeft = secondsLeft - 1;
    timer.textContent = secondsLeft;

    if (secondsLeft <= 0) {
      stopTimer();
      await finishGame();
    }
  }, 1000);
}


async function finishGame() {
  const result = await sendJson("/api/finish", {
    game_id: gameId,
  });

  message.textContent = "Игра закончена. Очки за попытку: " + result.score;
  answerInput.disabled = true;
  showLeaderboard(result.leaderboard);
  gameScreen.classList.add("hidden");
  startScreen.classList.remove("hidden");
}


startForm.addEventListener("submit", async function (event) {
  event.preventDefault();

  const result = await sendJson("/api/start", {
    name: playerNameInput.value,
  });

  gameId = result.game_id;
  secondsLeft = result.seconds;

  currentPlayer.textContent = result.name;
  score.textContent = result.score;
  message.textContent = "";
  answerInput.disabled = false;

  startScreen.classList.add("hidden");
  gameScreen.classList.remove("hidden");

  showLeaderboard(result.leaderboard);
  showProblem(result.problem);
  startTimer();
});


answerForm.addEventListener("submit", async function (event) {
  event.preventDefault();

  const result = await sendJson("/api/answer", {
    game_id: gameId,
    problem_id: currentProblemId,
    answer: answerInput.value,
  });

  if (result.finished) {
    stopTimer();
    message.textContent = "Время вышло. Очки за попытку: " + result.score;
    answerInput.disabled = true;
    showLeaderboard(result.leaderboard);
    gameScreen.classList.add("hidden");
    startScreen.classList.remove("hidden");
    return;
  }

  if (result.correct) {
    message.textContent = "Верно!";
  } else {
    message.textContent = "Неверно. Правильный ответ: " + result.right_answer;
  }

  score.textContent = result.score;
  showProblem(result.problem);
});


refreshScore.addEventListener("click", loadLeaderboard);
loadLeaderboard();
