# Как JavaScript отправляет запросы, а Python-сервер их обрабатывает

Этот документ связывает теорию HTTP с реальным кодом проекта.
Если `async` и `await` пока непонятны, сначала прочитайте `docs/browser-async-await.md`.

Главная цепочка:

```text
HTML-форма
  -> JavaScript берет данные с экрана
  -> fetch отправляет HTTP-запрос
  -> server.py выбирает ветку по URL
  -> Python-функция обрабатывает данные
  -> сервер возвращает JSON
  -> JavaScript обновляет экран
```

## Как читать функции с нуля

Функция - это именованный кусок кода.

Функцию можно представить как маленький станок:

```text
входные данные -> функция -> результат
```

Пример из обычной жизни:

```text
мука, вода, соль -> функция "испечь хлеб" -> хлеб
```

Пример в коде:

```python
def clean_name(raw_name):
    ...
    return name
```

Здесь:

| Часть | Что значит |
| --- | --- |
| `def` | Начинается функция Python |
| `clean_name` | Имя функции |
| `raw_name` | Входные данные функции |
| `return name` | Что функция возвращает наружу |

В JavaScript функция выглядит немного иначе:

```javascript
function showProblem(problem) {
  ...
}
```

Здесь:

| Часть | Что значит |
| --- | --- |
| `function` | Начинается функция JavaScript |
| `showProblem` | Имя функции |
| `problem` | Входные данные функции |
| код внутри `{ ... }` | Что функция делает |

## Что значит "вызвать функцию"

Создать функцию мало. Ее еще нужно вызвать.

Функция объявлена:

```javascript
function showProblem(problem) {
  ...
}
```

Функция вызвана:

```javascript
showProblem(result.problem);
```

Это читается так:

```text
возьми result.problem
передай его в функцию showProblem
пусть функция обновит пример на экране
```

В Python так же:

```python
problem = make_problem(game_id)
```

Это читается так:

```text
вызови функцию make_problem
передай ей game_id
результат положи в переменную problem
```

## Что значит `return`

`return` - это ответ функции.

Пример:

```python
def start_new_game(name):
    game_id = secrets.token_hex(12)
    ...
    return game_id
```

Функция создает `game_id` и возвращает его тому коду, который ее вызвал.

Потом другой код может сохранить этот результат:

```python
game_id = start_new_game(name)
```

Схема:

```text
start_new_game("Аня")
        │
        v
создала game_id
        │
        v
return game_id
        │
        v
переменная game_id получила значение
```

## Что значит `async` и `await` в JavaScript

Запрос на сервер занимает время.

Браузер не получает ответ мгновенно:

```text
отправили запрос
ждем сеть
сервер думает
ждем сеть обратно
получили ответ
```

Поэтому в `game.js` используются `async` и `await`.

```javascript
async function loadLeaderboard() {
  const response = await fetch("/api/leaderboard");
  const data = await response.json();
  showLeaderboard(data.leaderboard);
}
```

Простыми словами:

| Код | Смысл |
| --- | --- |
| `async function` | Внутри функции можно ждать долгие действия |
| `await fetch(...)` | Подожди, пока сервер ответит |
| `await response.json()` | Подожди, пока ответ превратится в данные |

Без `await` код мог бы попытаться использовать ответ раньше, чем сервер его прислал.

## Что такое обработчик события

Событие - это действие на странице.

Например:

```text
игрок нажал кнопку
игрок отправил форму
игрок ввел текст
```

В `game.js` есть код:

```javascript
startForm.addEventListener("submit", async function (event) {
  ...
});
```

Это читается так:

```text
когда форма startForm будет отправлена,
запусти эту функцию
```

`event.preventDefault()` означает:

```text
браузер, не перезагружай страницу обычным способом
мы сами отправим данные через JavaScript
```

## Карта функций клиента

Клиентские функции лежат в `static/game.js`.

| Функция | Что получает | Что делает | Что возвращает |
| --- | --- | --- | --- |
| `sendJson(url, data)` | URL и объект с данными | Отправляет `POST` на сервер | JSON-ответ сервера |
| `loadLeaderboard()` | Ничего | Запрашивает общий счет | Ничего, обновляет экран |
| `showLeaderboard(rows)` | Список игроков | Рисует таблицу лидеров | Ничего |
| `showProblem(problem)` | Пример от сервера | Показывает пример на экране | Ничего |
| `finishGame()` | Ничего | Отправляет завершение игры | Ничего, обновляет экран |
| обработчик `startForm` | Событие отправки формы | Отправляет имя игрока | Ничего, запускает игру |
| обработчик `answerForm` | Событие отправки ответа | Отправляет ответ игрока | Ничего, показывает результат |

## Карта функций сервера

Серверные функции лежат в `server.py`.

| Функция | Что получает | Что делает | Что возвращает |
| --- | --- | --- | --- |
| `application(environ, start_response)` | HTTP-запрос от `wsgiref` | Выбирает нужную ветку по URL | HTTP-ответ |
| `read_json(environ)` | Данные запроса | Читает JSON из тела запроса | Словарь Python |
| `send_json(start_response, status, data)` | Статус и словарь | Превращает словарь в JSON | HTTP-ответ |
| `handle_start(...)` | Запрос `/api/start` | Создает игру и первый пример | JSON с игрой |
| `handle_answer(...)` | Запрос `/api/answer` | Проверяет ответ игрока | JSON с результатом |
| `handle_finish(...)` | Запрос `/api/finish` | Сохраняет счет | JSON с итогом |
| `get_leaderboard()` | Ничего | Читает общий счет из файла | Список игроков |

Главное:

```text
функции JavaScript работают в браузере
функции Python работают на сервере
между ними нет прямого вызова
между ними HTTP-запросы и HTTP-ответы
```

## 1. Общая схема обмена в этой игре

```text
┌──────────────────────────┐
│ static/game.js           │
│ код в браузере           │
└────────────┬─────────────┘
             │ HTTP-запрос через fetch
             │ GET /api/leaderboard
             │ POST /api/start
             │ POST /api/answer
             │ POST /api/finish
             v
┌──────────────────────────┐
│ server.py                │
│ код на сервере           │
└────────────┬─────────────┘
             │ HTTP-ответ
             │ JSON или файл
             v
┌──────────────────────────┐
│ static/game.js           │
│ обновляет страницу       │
└──────────────────────────┘
```

## 2. Главная функция клиента: `sendJson`

В `static/game.js` есть функция:

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

Что здесь происходит:

| Код | Что значит |
| --- | --- |
| `async function` | Функция умеет ждать ответ сервера |
| `fetch(url, ...)` | Отправить HTTP-запрос |
| `method: "POST"` | Отправляем данные на сервер |
| `Content-Type: application/json` | Говорим серверу: в теле запроса JSON |
| `JSON.stringify(data)` | Превращаем объект JavaScript в JSON-текст |
| `await response.json()` | Ждем ответ и превращаем JSON в объект JavaScript |

Простыми словами:

```text
sendJson берет URL и данные
отправляет их на сервер
ждет JSON-ответ
возвращает ответ в JavaScript-код
```

## 3. Пример: получить общий счет

### Клиент отправляет `GET /api/leaderboard`

В `static/game.js`:

```javascript
async function loadLeaderboard() {
  const response = await fetch("/api/leaderboard");
  const data = await response.json();
  showLeaderboard(data.leaderboard);
}
```

Здесь нет `method: "POST"`, поэтому `fetch` делает обычный `GET`.

Запрос по смыслу:

```text
GET /api/leaderboard
```

Ответ сервера по смыслу:

```json
{
  "leaderboard": [
    {"name": "Аня", "score": 12},
    {"name": "Борис", "score": 7}
  ]
}
```

После ответа клиент вызывает:

```javascript
showLeaderboard(data.leaderboard);
```

То есть браузер берет данные от сервера и рисует список игроков на странице.

### Сервер обрабатывает `/api/leaderboard`

В `server.py` внутри `application`:

```python
elif read_request == True and path == "/api/leaderboard":
    result = {
        "leaderboard": get_leaderboard(),
    }
    return send_json(start_response, "200 OK", result)
```

Что происходит:

1. Сервер видит путь `/api/leaderboard`.
2. Сервер вызывает `get_leaderboard()`.
3. `get_leaderboard()` читает счет из `data/scores.txt`.
4. Сервер возвращает JSON браузеру.

Схема:

```text
game.js
  fetch("/api/leaderboard")
      │
      v
server.py
  application видит path == "/api/leaderboard"
      │
      v
  get_leaderboard()
      │
      v
  send_json(...)
      │
      v
game.js
  showLeaderboard(...)
```

## 4. Пример: начать игру

### Клиент отправляет имя игрока

В `static/game.js`:

```javascript
startForm.addEventListener("submit", async function (event) {
  event.preventDefault();

  const result = await sendJson("/api/start", {
    name: playerNameInput.value,
  });

  gameId = result.game_id;
  secondsLeft = result.seconds;

  currentPlayer.textContent = result.name;
  score.textContent = result.score;

  showLeaderboard(result.leaderboard);
  showProblem(result.problem);
  startTimer();
});
```

Что это значит:

1. Игрок нажал кнопку "Старт".
2. Браузер не перезагружает страницу благодаря `event.preventDefault()`.
3. JavaScript берет имя из поля:

```javascript
playerNameInput.value
```

4. JavaScript отправляет на сервер:

```javascript
sendJson("/api/start", {
  name: playerNameInput.value,
});
```

HTTP-запрос по смыслу:

```text
POST /api/start
Content-Type: application/json

{
  "name": "Аня"
}
```

### Сервер принимает имя и создает игру

В `server.py` внутри `application`:

```python
elif method == "POST" and path == "/api/start":
    return handle_start(start_response, environ)
```

Сервер выбирает функцию `handle_start`.

В `handle_start`:

```python
def handle_start(start_response, environ):
    data = read_json(environ)

    raw_name = data.get("name", "")
    name = clean_name(raw_name)

    game_id = start_new_game(name)
    problem = make_problem(game_id)
    leaderboard = get_leaderboard()

    result = {
        "game_id": game_id,
        "name": name,
        "seconds": GAME_SECONDS,
        "score": 0,
        "problem": problem,
        "leaderboard": leaderboard,
    }

    response = send_json(start_response, "200 OK", result)
    return response
```

Что происходит по шагам:

1. `read_json(environ)` читает JSON из тела запроса.
2. `data.get("name", "")` берет имя игрока.
3. `clean_name(raw_name)` чистит имя.
4. `start_new_game(name)` создает игру и возвращает `game_id`.
5. `make_problem(game_id)` создает первый пример.
6. `get_leaderboard()` берет общий счет.
7. `send_json(...)` отправляет ответ браузеру.

Ответ сервера по смыслу:

```json
{
  "game_id": "abc123",
  "name": "Аня",
  "seconds": 60,
  "score": 0,
  "problem": {
    "id": "p1",
    "text": "7 * 8"
  },
  "leaderboard": []
}
```

### Клиент использует ответ сервера

После ответа JavaScript сохраняет `game_id`:

```javascript
gameId = result.game_id;
```

Это важно. Потом браузер будет отправлять этот `game_id` вместе с ответами игрока, чтобы сервер понял, к какой игре относится запрос.

Потом клиент показывает пример:

```javascript
showProblem(result.problem);
```

Схема всего старта:

```text
Игрок ввел имя
      │
      v
game.js отправил POST /api/start
      │
      v
server.py вызвал handle_start
      │
      v
сервер создал game_id и первый пример
      │
      v
server.py вернул JSON
      │
      v
game.js сохранил gameId и показал пример
```

## 5. Пример: отправить ответ на пример

### Клиент отправляет ответ

В `static/game.js`:

```javascript
answerForm.addEventListener("submit", async function (event) {
  event.preventDefault();

  const result = await sendJson("/api/answer", {
    game_id: gameId,
    problem_id: currentProblemId,
    answer: answerInput.value,
  });

  if (result.correct) {
    message.textContent = "Верно!";
  } else {
    message.textContent = "Неверно. Правильный ответ: " + result.right_answer;
  }

  score.textContent = result.score;
  showProblem(result.problem);
});
```

Запрос по смыслу:

```text
POST /api/answer
Content-Type: application/json

{
  "game_id": "abc123",
  "problem_id": "p1",
  "answer": "56"
}
```

Зачем нужны поля:

| Поле | Зачем нужно |
| --- | --- |
| `game_id` | Какая игра сейчас идет |
| `problem_id` | На какой пример отвечает игрок |
| `answer` | Что ввел игрок |

### Сервер выбирает обработчик

В `server.py` внутри `application`:

```python
elif method == "POST" and path == "/api/answer":
    return handle_answer(start_response, environ)
```

Сервер видит `/api/answer` и вызывает `handle_answer`.

### Сервер читает JSON

В начале `handle_answer`:

```python
data = read_json(environ)

game_id = str(data.get("game_id", ""))
problem_id = str(data.get("problem_id", ""))
answer_text = str(data.get("answer", ""))
answer_text = answer_text.strip()
```

После этого в Python появляются обычные переменные:

```text
game_id
problem_id
answer_text
```

### Сервер находит игру и пример

```python
if game_id in GAMES:
    game = GAMES[game_id]
else:
    game = None

if problem_id in PROBLEMS:
    problem = PROBLEMS[problem_id]
    del PROBLEMS[problem_id]
else:
    problem = None
```

`GAMES` хранит текущие игры.

`PROBLEMS` хранит правильные ответы для текущих примеров.

Схема памяти сервера:

```text
GAMES
  abc123 -> имя, счет, время окончания

PROBLEMS
  p1 -> game_id abc123, правильный ответ 56
```

### Сервер проверяет ответ

```python
try:
    player_answer = int(answer_text)
except ValueError:
    player_answer = None

right_answer = problem["answer"]

if player_answer == right_answer:
    correct = True
else:
    correct = False

if correct == True:
    game["score"] = game["score"] + 1
```

Что происходит:

1. Текст из браузера превращается в число.
2. Сервер берет правильный ответ из `PROBLEMS`.
3. Сервер сравнивает числа.
4. Если ответ верный, счет увеличивается.

### Сервер возвращает результат и новый пример

```python
next_problem = make_problem(game_id)

result = {
    "ok": True,
    "correct": correct,
    "right_answer": right_answer,
    "score": game["score"],
    "finished": False,
    "problem": next_problem,
}

response = send_json(start_response, "200 OK", result)
return response
```

Ответ по смыслу:

```json
{
  "ok": true,
  "correct": true,
  "right_answer": 56,
  "score": 1,
  "finished": false,
  "problem": {
    "id": "p2",
    "text": "9 + 4"
  }
}
```

### Клиент обновляет экран

В `game.js`:

```javascript
score.textContent = result.score;
showProblem(result.problem);
```

Браузер показывает новый счет и новый пример.

Схема ответа:

```text
server.py проверил ответ
      │
      v
вернул JSON: correct, score, problem
      │
      v
game.js показал сообщение, счет и новый пример
```

## 6. Пример: закончить игру

### Клиент отправляет завершение игры

Когда таймер дошел до нуля, `game.js` вызывает:

```javascript
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
```

Запрос по смыслу:

```text
POST /api/finish
Content-Type: application/json

{
  "game_id": "abc123"
}
```

### Сервер сохраняет счет

В `application`:

```python
elif method == "POST" and path == "/api/finish":
    return handle_finish(start_response, environ)
```

В `handle_finish`:

```python
def handle_finish(start_response, environ):
    data = read_json(environ)

    game_id = str(data.get("game_id", ""))

    result = finish_game(game_id)
    result["finished"] = True

    response = send_json(start_response, "200 OK", result)
    return response
```

`finish_game(game_id)` делает главную работу:

```python
if game["finished"] == False:
    add_score_to_file(game["name"], game["score"])
    game["finished"] = True
```

То есть сервер:

1. Находит игру по `game_id`.
2. Берет имя и счет.
3. Записывает счет в `data/scores.txt`.
4. Отмечает игру завершенной.
5. Возвращает обновленную таблицу лидеров.

## 7. Как `read_json` превращает запрос в словарь Python

Клиент отправил:

```json
{
  "name": "Аня"
}
```

На сервере это сначала байты в `environ["wsgi.input"]`.

Функция `read_json`:

```python
body_stream = environ["wsgi.input"]
body_bytes = body_stream.read(length)
raw_body = body_bytes.decode("utf-8")

if raw_body.strip() == "":
    data = {}
else:
    data = json.loads(raw_body)
```

После `json.loads(raw_body)` сервер получает словарь Python:

```python
{
    "name": "Аня"
}
```

Дальше это уже обычная работа со словарем:

```python
raw_name = data.get("name", "")
```

## 8. Как `send_json` превращает словарь Python в ответ

Сервер подготовил словарь:

```python
result = {
    "ok": True,
    "score": 1,
}
```

`send_json` превращает его в JSON:

```python
text = json.dumps(data, ensure_ascii=False)
body = text.encode("utf-8")
```

Потом `send_bytes` отправляет статус, заголовки и тело:

```python
response = send_bytes(start_response, status, body, "application/json; charset=utf-8")
```

Браузер получает JSON и делает:

```javascript
const data = await response.json();
```

После этого в JavaScript снова обычный объект:

```javascript
data.score
data.ok
```

## 9. Таблица соответствия клиента и сервера

| Действие игрока | Код клиента | HTTP | Код сервера |
| --- | --- | --- | --- |
| Открыть игру | браузер открывает страницу | `GET /` | `send_file(... index.html ...)` |
| Загрузить счет | `loadLeaderboard()` | `GET /api/leaderboard` | `get_leaderboard()` |
| Начать игру | `sendJson("/api/start", ...)` | `POST /api/start` | `handle_start(...)` |
| Ответить | `sendJson("/api/answer", ...)` | `POST /api/answer` | `handle_answer(...)` |
| Закончить игру | `sendJson("/api/finish", ...)` | `POST /api/finish` | `handle_finish(...)` |

## 10. Главная мысль

JavaScript не вызывает Python-функции напрямую.

Нельзя представить это так:

```text
game.js напрямую вызвал handle_answer()
```

Правильная схема такая:

```text
game.js
  -> HTTP-запрос через fetch
  -> server.py получил URL и JSON
  -> application выбрала Python-функцию
  -> Python-функция вернула JSON
  -> game.js получил JSON и обновил экран
```

Это главное отличие веб-приложения от обычной программы в одном файле:

```text
клиент и сервер живут в разных местах
они общаются сообщениями по HTTP
```
