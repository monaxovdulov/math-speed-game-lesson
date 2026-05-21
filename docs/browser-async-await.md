# `async` и `await` в браузере без глубоких деталей

Этот документ объясняет только то, что нужно для понимания `static/game.js`.

Цель:

```text
понять, почему JavaScript в браузере ждет ответ сервера
и как читать код с async/await
```

Здесь не разбираются сложные внутренности JavaScript.

## 1. Почему вообще нужно ждать

Когда браузер обращается к серверу, ответ не появляется мгновенно.

Сначала браузер отправляет запрос:

```text
POST /api/start
```

Потом сервер должен:

```text
получить запрос
прочитать имя игрока
создать игру
создать первый пример
собрать JSON-ответ
отправить ответ назад
```

На это нужно время.

Схема:

```text
браузер отправил запрос
        │
        v
      ждем
        │
        v
сервер прислал ответ
        │
        v
браузер обновил экран
```

Если не ждать ответ, браузер попытается использовать данные, которых еще нет.

## 2. Обычный код и код с ожиданием

Обычный код читается сверху вниз:

```javascript
const name = "Аня";
console.log(name);
```

Но запрос к серверу - не обычное мгновенное действие.

```javascript
const response = fetch("/api/leaderboard");
```

`fetch` отправляет запрос, но ответ придет позже.

Поэтому в проекте пишется так:

```javascript
const response = await fetch("/api/leaderboard");
```

`await` можно читать как:

```text
подожди, пока это действие закончится
```

## 3. Что значит `async function`

В JavaScript `await` можно использовать внутри `async function`.

Пример из проекта:

```javascript
async function loadLeaderboard() {
  const response = await fetch("/api/leaderboard");
  const data = await response.json();
  showLeaderboard(data.leaderboard);
}
```

`async function` можно читать так:

```text
это функция, внутри которой будут ожидания
```

Она нужна, потому что внутри есть `await`.

## 4. Что значит `await fetch(...)`

Строка:

```javascript
const response = await fetch("/api/leaderboard");
```

Читается так:

```text
отправь запрос на /api/leaderboard
подожди ответ сервера
положи ответ в переменную response
```

`response` - это еще не сами данные таблицы.

Это HTTP-ответ целиком: статус, заголовки и тело.

## 5. Что значит `await response.json()`

Сервер возвращает JSON-текст.

Пример:

```json
{
  "leaderboard": [
    {"name": "Аня", "score": 12}
  ]
}
```

Браузеру нужно превратить JSON в обычный объект JavaScript.

Для этого есть:

```javascript
const data = await response.json();
```

Читается так:

```text
возьми тело ответа
подожди, пока оно превратится из JSON в объект JavaScript
положи результат в переменную data
```

После этого можно писать:

```javascript
data.leaderboard
```

## 6. Полный пример: загрузить общий счет

Код из `static/game.js`:

```javascript
async function loadLeaderboard() {
  const response = await fetch("/api/leaderboard");
  const data = await response.json();
  showLeaderboard(data.leaderboard);
}
```

Разбор по строкам:

| Строка | Что делает |
| --- | --- |
| `async function loadLeaderboard()` | Объявляет функцию, где можно ждать |
| `await fetch("/api/leaderboard")` | Ждет HTTP-ответ сервера |
| `await response.json()` | Ждет превращение JSON в объект |
| `showLeaderboard(data.leaderboard)` | Рисует таблицу лидеров на странице |

Схема:

```text
loadLeaderboard()
      │
      v
fetch("/api/leaderboard")
      │
      v
await: ждем сервер
      │
      v
response.json()
      │
      v
await: ждем данные
      │
      v
showLeaderboard(...)
```

## 7. Функция `sendJson`

В проекте несколько раз нужно отправлять данные на сервер.

Например:

```text
начать игру
отправить ответ
закончить игру
```

Чтобы не повторять один и тот же код, есть функция `sendJson`.

```javascript
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
```

Ее можно читать так:

```text
sendJson получает url и data
отправляет data на сервер как JSON
ждет ответ сервера
возвращает JSON-ответ
```

Таблица:

| Часть | Простое объяснение |
| --- | --- |
| `url` | Куда отправить запрос: `/api/start`, `/api/answer` |
| `data` | Какие данные отправить |
| `method: "POST"` | Мы отправляем данные на сервер |
| `JSON.stringify(data)` | Превращаем объект JavaScript в JSON-текст |
| `await fetch(...)` | Ждем HTTP-ответ |
| `return response.json()` | Возвращаем данные из ответа |

## 8. Почему в `sendJson` нет второго `await`

В функции написано:

```javascript
return response.json();
```

А не:

```javascript
return await response.json();
```

Для новичка можно читать оба варианта почти одинаково:

```text
верни JSON-данные из ответа
```

В этом проекте важнее понять не эту тонкость, а общую идею:

```text
сначала await fetch
потом response.json
```

Если так понятнее ученику, можно мысленно читать эту строку как:

```javascript
const data = await response.json();
return data;
```

## 9. Как старт игры ждет сервер

Код из `static/game.js`:

```javascript
startForm.addEventListener("submit", async function (event) {
  event.preventDefault();

  const result = await sendJson("/api/start", {
    name: playerNameInput.value,
  });

  gameId = result.game_id;
  secondsLeft = result.seconds;

  showLeaderboard(result.leaderboard);
  showProblem(result.problem);
  startTimer();
});
```

Что происходит:

1. Игрок нажал кнопку "Старт".
2. Запускается функция-обработчик.
3. `sendJson("/api/start", ...)` отправляет имя на сервер.
4. `await` ждет, пока сервер создаст игру.
5. Когда ответ пришел, переменная `result` получает данные.
6. Только после этого браузер показывает пример и запускает таймер.

Главная строка:

```javascript
const result = await sendJson("/api/start", {
  name: playerNameInput.value,
});
```

Читается так:

```text
отправь имя игрока на сервер
подожди ответ
положи ответ в result
```

## 10. Почему нельзя просто убрать `await`

Представим такой неправильный код:

```javascript
const result = sendJson("/api/start", {
  name: playerNameInput.value,
});

showProblem(result.problem);
```

Проблема:

```text
sendJson еще не получил ответ сервера
а код уже пытается взять result.problem
```

То есть `result.problem` еще не существует.

Поэтому правильно:

```javascript
const result = await sendJson("/api/start", {
  name: playerNameInput.value,
});

showProblem(result.problem);
```

## 11. Как отправка ответа ждет сервер

Код:

```javascript
const result = await sendJson("/api/answer", {
  game_id: gameId,
  problem_id: currentProblemId,
  answer: answerInput.value,
});
```

Читается так:

```text
отправь ответ игрока на сервер
подожди проверку
положи результат проверки в result
```

После этого код может безопасно читать:

```javascript
result.correct
result.right_answer
result.score
result.problem
```

Потому что сервер уже ответил.

## 12. Как завершение игры ждет сервер

Код:

```javascript
async function finishGame() {
  const result = await sendJson("/api/finish", {
    game_id: gameId,
  });

  message.textContent = "Игра закончена. Очки за попытку: " + result.score;
  showLeaderboard(result.leaderboard);
}
```

Читается так:

```text
сообщи серверу, что игра закончилась
подожди, пока сервер сохранит счет
получи итоговый счет и таблицу лидеров
обнови экран
```

## 13. `async` в обработчике события

В проекте есть:

```javascript
answerForm.addEventListener("submit", async function (event) {
  event.preventDefault();

  const result = await sendJson("/api/answer", {
    game_id: gameId,
    problem_id: currentProblemId,
    answer: answerInput.value,
  });

  ...
});
```

Почему после `submit` стоит `async function`?

Потому что внутри обработчика есть:

```javascript
await sendJson(...)
```

Правило для новичка:

```text
если внутри функции есть await,
перед function нужно async
```

## 14. `async` в таймере

В проекте есть таймер:

```javascript
timerId = setInterval(async function () {
  secondsLeft = secondsLeft - 1;
  timer.textContent = secondsLeft;

  if (secondsLeft <= 0) {
    stopTimer();
    await finishGame();
  }
}, 1000);
```

`setInterval` запускает функцию каждую секунду.

Когда время закончилось:

```javascript
await finishGame();
```

Это значит:

```text
подожди, пока сервер сохранит счет и вернет итог
```

## 15. Как читать `async/await` в этом проекте

Когда видишь:

```javascript
async function someName() {
  const result = await something();
}
```

Читай так:

```text
это функция, которая умеет ждать
она запускает долгое действие
она ждет результат
потом продолжает работу
```

В этой игре долгие действия почти всегда связаны с сервером:

```text
fetch(...)
sendJson(...)
finishGame()
```

## 16. Чего пока не нужно знать

Для этого урока не нужно глубоко разбирать:

- Promise;
- event loop;
- microtask queue;
- внутренности браузера;
- параллельность JavaScript.

Достаточно понимать:

```text
запрос к серверу занимает время
await говорит: подожди результат
async разрешает использовать await внутри функции
после await можно работать с данными ответа
```

## 17. Главная мысль

`async/await` в этой игре нужен не для красоты.

Он нужен, чтобы код шел в правильном порядке:

```text
1. отправить запрос
2. дождаться ответа
3. взять данные из ответа
4. обновить экран
```

Без ожидания браузер пытался бы обновить экран раньше, чем сервер прислал данные.
