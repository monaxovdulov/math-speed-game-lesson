import json
import os
import random
import secrets
import time
from wsgiref.simple_server import make_server


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
# os.environ.get нужен для Docker: там можно поменять время без правки кода.
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

    # Берем только первые 30 символов, чтобы имя не было слишком длинным.
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

    # Для урока файл открывается явно через open.
    # Поэтому ниже мы сами вызываем file.close().
    file = open(SCORES_FILE, "r", encoding="utf-8")
    text = file.read()
    file.close()

    lines = text.splitlines()

    for line in lines:
        parts = line.split("|")

        # Если строка не похожа на "имя|очки", просто пропускаем ее.
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

    Браузеру удобно получать данные в виде словарей, потому что потом эти
    словари легко превращаются в JSON.
    """
    row = {
        "name": name,
        "score": score,
    }
    return row


def score_sort_key(row):
    """
    Помогает отсортировать таблицу лидеров.

    sort вызывает эту функцию для каждой строки.
    Минус перед очками нужен, чтобы большие очки оказались выше маленьких.
    """
    score = row["score"]
    name = row["name"]

    sort_key = (-score, name.lower())
    return sort_key


def get_leaderboard():
    """
    Возвращает первые 10 игроков по общему счету.

    Результат выглядит так:

    [
        {"name": "Аня", "score": 12},
        {"name": "Борис", "score": 7}
    ]
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

    # problem_id нужен, чтобы сервер потом понял, на какой пример отвечает игрок.
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
    Это защищает от случайного двойного запроса /api/finish.
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


def read_json(environ):
    """
    Читает JSON из тела HTTP-запроса.

    environ - это словарь от wsgiref. В нем лежит техническая информация
    о запросе: метод, путь, длина тела, поток с телом запроса.
    """
    length_text = environ.get("CONTENT_LENGTH")

    if length_text is None:
        length_text = "0"

    if length_text == "":
        length_text = "0"

    try:
        length = int(length_text)
    except ValueError:
        length = 0

    body_stream = environ["wsgi.input"]
    body_bytes = body_stream.read(length)
    raw_body = body_bytes.decode("utf-8")

    if raw_body.strip() == "":
        data = {}
    else:
        data = json.loads(raw_body)

    return data


def send_bytes(start_response, status, body, content_type):
    """
    Отправляет браузеру готовые байты.

    HTTP-ответ состоит из трех частей:
    1. статус, например "200 OK";
    2. заголовки, например Content-Type;
    3. тело ответа, например HTML или JSON.
    """
    headers = [
        ("Content-Type", content_type),
        ("Content-Length", str(len(body))),
        ("Cache-Control", "no-store"),
    ]

    start_response(status, headers)

    # WSGI-сервер ждет список байтов, поэтому возвращаем [body].
    return [body]


def send_json(start_response, status, data):
    """
    Превращает Python-словарь в JSON и отправляет его браузеру.
    """
    text = json.dumps(data, ensure_ascii=False)
    body = text.encode("utf-8")

    response = send_bytes(start_response, status, body, "application/json; charset=utf-8")
    return response


def send_text(start_response, status, text):
    """
    Отправляет простой текстовый ответ.
    """
    body = text.encode("utf-8")

    response = send_bytes(start_response, status, body, "text/plain; charset=utf-8")
    return response


def send_file(start_response, file_path, content_type):
    """
    Читает файл с диска и отправляет его браузеру.

    Так сервер отдает index.html, style.css и game.js.
    """
    file = open(file_path, "rb")
    body = file.read()
    file.close()

    response = send_bytes(start_response, "200 OK", body, content_type)
    return response


def handle_start(start_response, environ):
    """
    Обрабатывает POST /api/start.

    Этот URL вызывается, когда игрок ввел имя и нажал кнопку "Старт".
    """
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


def handle_answer(start_response, environ):
    """
    Обрабатывает POST /api/answer.

    Этот URL вызывается после каждого ответа игрока.
    Сервер проверяет ответ и возвращает следующий пример.
    """
    data = read_json(environ)

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
        error = {
            "ok": False,
            "message": "Игра не найдена.",
        }
        return send_json(start_response, "400 Bad Request", error)

    if problem is None:
        error = {
            "ok": False,
            "message": "Задача не найдена.",
        }
        return send_json(start_response, "400 Bad Request", error)

    if problem["game_id"] != game_id:
        error = {
            "ok": False,
            "message": "Эта задача относится к другой игре.",
        }
        return send_json(start_response, "400 Bad Request", error)

    current_time = time.time()

    if current_time > game["ends_at"]:
        result = finish_game(game_id)
        result["finished"] = True
        return send_json(start_response, "200 OK", result)

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

    response = send_json(start_response, "200 OK", result)
    return response


def handle_finish(start_response, environ):
    """
    Обрабатывает POST /api/finish.

    Этот URL вызывается, когда таймер в браузере дошел до нуля.
    """
    data = read_json(environ)

    game_id = str(data.get("game_id", ""))

    result = finish_game(game_id)
    result["finished"] = True

    response = send_json(start_response, "200 OK", result)
    return response


def application(environ, start_response):
    """
    Главная функция веб-приложения.

    WSGI-сервер вызывает эту функцию на каждый HTTP-запрос.
    Здесь явно написано, какой URL какую часть кода запускает.
    """
    method = environ["REQUEST_METHOD"]
    path = environ["PATH_INFO"]

    # HEAD похож на GET, но браузер или проверяющая программа просит только
    # заголовки ответа. Для простоты учебного примера отдаем тот же ответ.
    if method == "GET" or method == "HEAD":
        read_request = True
    else:
        read_request = False

    try:
        if read_request == True and path == "/":
            file_path = os.path.join(STATIC_DIR, "index.html")
            return send_file(start_response, file_path, "text/html; charset=utf-8")

        elif read_request == True and path == "/style.css":
            file_path = os.path.join(STATIC_DIR, "style.css")
            return send_file(start_response, file_path, "text/css; charset=utf-8")

        elif read_request == True and path == "/game.js":
            file_path = os.path.join(STATIC_DIR, "game.js")
            return send_file(start_response, file_path, "text/javascript; charset=utf-8")

        elif read_request == True and path == "/health":
            return send_text(start_response, "200 OK", "ok")

        elif read_request == True and path == "/api/leaderboard":
            result = {
                "leaderboard": get_leaderboard(),
            }
            return send_json(start_response, "200 OK", result)

        elif method == "POST" and path == "/api/start":
            return handle_start(start_response, environ)

        elif method == "POST" and path == "/api/answer":
            return handle_answer(start_response, environ)

        elif method == "POST" and path == "/api/finish":
            return handle_finish(start_response, environ)

        else:
            return send_text(start_response, "404 Not Found", "Страница не найдена.")

    except json.JSONDecodeError:
        error = {
            "ok": False,
            "message": "Неверный JSON.",
        }
        return send_json(start_response, "400 Bad Request", error)


if __name__ == "__main__":
    # Этот блок запускается только при команде:
    #
    # python3 server.py
    #
    # Если другой файл импортирует server.py, этот блок не запустится.
    ensure_data_file()

    host = os.environ.get("HOST", "127.0.0.1")

    port_text = os.environ.get("PORT", "8000")
    port = int(port_text)

    print("Server started: http://" + host + ":" + str(port))

    # make_server - готовая функция из стандартной библиотеки Python.
    # Она слушает порт и передает каждый запрос в нашу функцию application.
    server = make_server(host, port, application)
    server.serve_forever()
