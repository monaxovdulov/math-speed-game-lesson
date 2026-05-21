import os
import random
import secrets
import time

from fastapi import Body, FastAPI
from fastapi.responses import FileResponse, PlainTextResponse


# FastAPI - это готовый инструмент для веб-серверов.
# Он сам умеет разбирать HTTP-запросы, JSON и ответы браузеру.
app = FastAPI(title="Математический забег")


# os.path.abspath(__file__) дает полный путь к этому файлу server.py.
# os.path.dirname(...) берет папку, в которой лежит этот файл.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Здесь лежат файлы браузера: HTML, CSS и JavaScript.
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Здесь лежит текстовый файл с очками игроков.
DEFAULT_DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_DIR = os.environ.get("DATA_DIR", DEFAULT_DATA_DIR)
SCORES_FILE = os.path.join(DATA_DIR, "scores.txt")

# Сколько секунд длится одна игра.
GAME_SECONDS_TEXT = os.environ.get("GAME_SECONDS", "60")
GAME_SECONDS = int(GAME_SECONDS_TEXT)

# Эти словари живут в памяти Python-сервера.
# Если сервер перезапустить, они очистятся.
GAMES = {}
PROBLEMS = {}


def ensure_data_file():
    """
    Проверяет, что папка data и файл scores.txt существуют.

    Если папки или файла нет, функция создает их.
    Это нужно, чтобы остальной код мог спокойно читать и писать счет.
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    if not os.path.exists(SCORES_FILE):
        file = open(SCORES_FILE, "w", encoding="utf-8")
        file.write("")
        file.close()


def clean_name(raw_name):
    """
    Приводит имя игрока к безопасному виду.

    Игрок вводит имя в браузере. Сервер не должен слепо доверять этому тексту.
    Мы убираем символ-разделитель | и переносы строк, потому что они сломают
    простой формат файла scores.txt.
    """
    name = str(raw_name)
    name = name.strip()
    name = name.replace("|", "")
    name = name.replace("\n", " ")
    name = name.replace("\r", " ")

    if name == "":
        name = "Игрок"

    name = name[:30]
    return name


def load_scores():
    """
    Читает общий счет игроков из текстового файла.

    Файл хранит строки такого вида:

    Аня|12
    Борис|7

    Функция возвращает словарь:

    {"Аня": 12, "Борис": 7}
    """
    ensure_data_file()

    scores = {}

    file = open(SCORES_FILE, "r", encoding="utf-8")
    text = file.read()
    file.close()

    lines = text.splitlines()

    for line in lines:
        parts = line.split("|")

        if len(parts) == 2:
            name = parts[0]
            score_text = parts[1]

            try:
                score = int(score_text)
            except ValueError:
                score = 0

            scores[name] = score

    return scores


def save_scores(scores):
    """
    Записывает словарь с очками обратно в текстовый файл.

    На вход приходит словарь:

    {"Аня": 12, "Борис": 7}

    В файл записываются строки:

    Аня|12
    Борис|7
    """
    ensure_data_file()

    lines = []

    names = list(scores.keys())
    names.sort()

    for name in names:
        score = scores[name]
        line = name + "|" + str(score)
        lines.append(line)

    text = "\n".join(lines)

    if text != "":
        text = text + "\n"

    file = open(SCORES_FILE, "w", encoding="utf-8")
    file.write(text)
    file.close()


def add_score_to_file(name, score):
    """
    Добавляет очки одной законченной игры к общему счету игрока.

    Если игрок уже есть в файле, новый результат прибавляется к старому.
    Если игрока еще нет, он появляется в файле.
    """
    scores = load_scores()

    if name in scores:
        old_score = scores[name]
    else:
        old_score = 0

    new_score = old_score + score
    scores[name] = new_score

    save_scores(scores)


def make_leaderboard_row(name, score):
    """
    Создает одну строку таблицы лидеров.

    FastAPI сам превратит словарь Python в JSON для браузера.
    """
    row = {
        "name": name,
        "score": score,
    }
    return row


def score_sort_key(row):
    """
    Помогает отсортировать таблицу лидеров.

    Минус перед очками нужен, чтобы большие очки оказались выше маленьких.
    """
    score = row["score"]
    name = row["name"]

    sort_key = (-score, name.lower())
    return sort_key


def get_leaderboard():
    """
    Возвращает первые 10 игроков по общему счету.
    """
    scores = load_scores()
    rows = []

    for name in scores:
        score = scores[name]
        row = make_leaderboard_row(name, score)
        rows.append(row)

    rows.sort(key=score_sort_key)

    best_rows = rows[:10]
    return best_rows


def make_problem(game_id):
    """
    Создает новый случайный математический пример.

    Сервер отправляет браузеру только текст примера и id примера.
    Правильный ответ остается на сервере в словаре PROBLEMS.
    """
    operations = ["+", "-", "*"]
    operation = random.choice(operations)

    if operation == "+":
        left = random.randint(2, 50)
        right = random.randint(2, 50)
        answer = left + right
    elif operation == "-":
        left = random.randint(10, 80)
        right = random.randint(2, left)
        answer = left - right
    else:
        left = random.randint(2, 12)
        right = random.randint(2, 12)
        answer = left * right

    problem_id = secrets.token_hex(8)

    PROBLEMS[problem_id] = {
        "game_id": game_id,
        "answer": answer,
    }

    problem_text = str(left) + " " + operation + " " + str(right)

    problem = {
        "id": problem_id,
        "text": problem_text,
    }

    return problem


def start_new_game(name):
    """
    Создает новую игру для одного игрока.

    Возвращает game_id. Это случайная строка, по которой сервер дальше узнает
    конкретную игру в запросах /api/answer и /api/finish.
    """
    game_id = secrets.token_hex(12)

    game = {
        "name": name,
        "score": 0,
        "ends_at": time.time() + GAME_SECONDS,
        "finished": False,
    }

    GAMES[game_id] = game
    return game_id


def finish_game(game_id):
    """
    Завершает игру и сохраняет очки в текстовый файл.

    Если игра уже была завершена, второй раз очки не записываются.
    """
    if game_id in GAMES:
        game = GAMES[game_id]
    else:
        result = {
            "ok": False,
            "message": "Игра не найдена.",
            "leaderboard": get_leaderboard(),
        }
        return result

    if game["finished"] == False:
        add_score_to_file(game["name"], game["score"])
        game["finished"] = True

    result = {
        "ok": True,
        "name": game["name"],
        "score": game["score"],
        "leaderboard": get_leaderboard(),
    }

    return result


def make_error(message):
    """
    Создает одинаковый словарь ошибки для разных API-ответов.
    """
    error = {
        "ok": False,
        "message": message,
    }
    return error


def get_request_data(data):
    """
    Проверяет тело запроса.

    FastAPI сам прочитал JSON и передал его в аргумент data.
    Нам остается убедиться, что это словарь.
    """
    if data is None:
        data = {}

    if type(data) != dict:
        data = {}

    return data


def page_index():
    """
    GET /

    Возвращает главный HTML-файл.
    """
    file_path = os.path.join(STATIC_DIR, "index.html")
    return FileResponse(file_path, media_type="text/html; charset=utf-8")


def page_style():
    """
    GET /style.css

    Возвращает CSS-файл.
    """
    file_path = os.path.join(STATIC_DIR, "style.css")
    return FileResponse(file_path, media_type="text/css; charset=utf-8")


def page_script():
    """
    GET /game.js

    Возвращает JavaScript-файл.
    """
    file_path = os.path.join(STATIC_DIR, "game.js")
    return FileResponse(file_path, media_type="text/javascript; charset=utf-8")


def health():
    """
    GET /health

    Маленькая проверка, что сервер жив.
    """
    return PlainTextResponse("ok")


def api_leaderboard():
    """
    GET /api/leaderboard

    Возвращает общий счет игроков.
    """
    result = {
        "leaderboard": get_leaderboard(),
    }
    return result


def api_start(data=Body(default=None)):
    """
    POST /api/start

    Игрок ввел имя и нажал "Старт".
    FastAPI передает JSON-тело запроса в переменную data.
    """
    data = get_request_data(data)

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

    return result


def api_answer(data=Body(default=None)):
    """
    POST /api/answer

    Игрок отправил ответ на пример.
    """
    data = get_request_data(data)

    game_id = str(data.get("game_id", ""))
    problem_id = str(data.get("problem_id", ""))
    answer_text = str(data.get("answer", ""))
    answer_text = answer_text.strip()

    if game_id in GAMES:
        game = GAMES[game_id]
    else:
        game = None

    if problem_id in PROBLEMS:
        problem = PROBLEMS[problem_id]
        del PROBLEMS[problem_id]
    else:
        problem = None

    if game is None:
        return make_error("Игра не найдена.")

    if problem is None:
        return make_error("Задача не найдена.")

    if problem["game_id"] != game_id:
        return make_error("Эта задача относится к другой игре.")

    current_time = time.time()

    if current_time > game["ends_at"]:
        result = finish_game(game_id)
        result["finished"] = True
        return result

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

    next_problem = make_problem(game_id)

    result = {
        "ok": True,
        "correct": correct,
        "right_answer": right_answer,
        "score": game["score"],
        "finished": False,
        "problem": next_problem,
    }

    return result


def api_finish(data=Body(default=None)):
    """
    POST /api/finish

    Таймер в браузере дошел до нуля.
    """
    data = get_request_data(data)

    game_id = str(data.get("game_id", ""))

    result = finish_game(game_id)
    result["finished"] = True

    return result


# Это главный учебный блок этой ветки.
# Здесь видно: URL -> функция.
# Декораторов нет. FastAPI получает этот список маршрутов явно.
app.add_api_route("/", page_index, methods=["GET", "HEAD"])
app.add_api_route("/style.css", page_style, methods=["GET", "HEAD"])
app.add_api_route("/game.js", page_script, methods=["GET", "HEAD"])
app.add_api_route("/health", health, methods=["GET", "HEAD"])
app.add_api_route("/api/leaderboard", api_leaderboard, methods=["GET", "HEAD"])
app.add_api_route("/api/start", api_start, methods=["POST"])
app.add_api_route("/api/answer", api_answer, methods=["POST"])
app.add_api_route("/api/finish", api_finish, methods=["POST"])


if __name__ == "__main__":
    # Этот блок нужен, чтобы проект можно было запускать привычной командой:
    #
    # python3 server.py
    #
    # Uvicorn - это сервер, который умеет запускать FastAPI-приложения.
    import uvicorn

    ensure_data_file()

    host = os.environ.get("HOST", "127.0.0.1")

    port_text = os.environ.get("PORT", "8000")
    port = int(port_text)

    uvicorn.run(app, host=host, port=port)
