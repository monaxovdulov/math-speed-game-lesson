import json
import os
import random
import secrets
import time
from pathlib import Path
from wsgiref.simple_server import make_server


BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))
SCORES_FILE = DATA_DIR / "scores.txt"
GAME_SECONDS = int(os.environ.get("GAME_SECONDS", "60"))

GAMES = {}
PROBLEMS = {}


def ensure_data_file():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SCORES_FILE.exists():
        SCORES_FILE.write_text("", encoding="utf-8")


def clean_name(raw_name):
    name = str(raw_name).strip()
    name = name.replace("|", "").replace("\n", " ").replace("\r", " ")
    if name == "":
        return "Игрок"
    return name[:30]


def load_scores():
    ensure_data_file()
    scores = {}

    text = SCORES_FILE.read_text(encoding="utf-8")
    for line in text.splitlines():
        parts = line.split("|")
        if len(parts) != 2:
            continue

        name = parts[0]
        score_text = parts[1]

        try:
            score = int(score_text)
        except ValueError:
            score = 0

        scores[name] = score

    return scores


def save_scores(scores):
    ensure_data_file()

    lines = []
    for name in sorted(scores):
        lines.append(f"{name}|{scores[name]}")

    SCORES_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def add_score_to_file(name, score):
    scores = load_scores()
    scores[name] = scores.get(name, 0) + score
    save_scores(scores)


def get_leaderboard():
    scores = load_scores()
    rows = []

    for name, score in scores.items():
        rows.append({"name": name, "score": score})

    rows.sort(key=score_sort_key)
    return rows[:10]


def score_sort_key(row):
    return -row["score"], row["name"].lower()


def make_problem(game_id):
    operation = random.choice(["+", "-", "*"])

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

    return {
        "id": problem_id,
        "text": f"{left} {operation} {right}",
    }


def start_new_game(name):
    game_id = secrets.token_hex(12)
    GAMES[game_id] = {
        "name": name,
        "score": 0,
        "ends_at": time.time() + GAME_SECONDS,
        "finished": False,
    }

    return game_id


def finish_game(game_id):
    game = GAMES.get(game_id)

    if game is None:
        return {
            "ok": False,
            "message": "Игра не найдена.",
            "leaderboard": get_leaderboard(),
        }

    if not game["finished"]:
        add_score_to_file(game["name"], game["score"])
        game["finished"] = True

    return {
        "ok": True,
        "name": game["name"],
        "score": game["score"],
        "leaderboard": get_leaderboard(),
    }


def read_json(environ):
    length_text = environ.get("CONTENT_LENGTH") or "0"

    try:
        length = int(length_text)
    except ValueError:
        length = 0

    raw_body = environ["wsgi.input"].read(length).decode("utf-8")
    if raw_body.strip() == "":
        return {}

    return json.loads(raw_body)


def send_bytes(start_response, status, body, content_type):
    headers = [
        ("Content-Type", content_type),
        ("Content-Length", str(len(body))),
        ("Cache-Control", "no-store"),
    ]
    start_response(status, headers)
    return [body]


def send_json(start_response, status, data):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return send_bytes(start_response, status, body, "application/json; charset=utf-8")


def send_text(start_response, status, text):
    body = text.encode("utf-8")
    return send_bytes(start_response, status, body, "text/plain; charset=utf-8")


def send_file(start_response, path, content_type):
    body = path.read_bytes()
    return send_bytes(start_response, "200 OK", body, content_type)


def application(environ, start_response):
    method = environ["REQUEST_METHOD"]
    path = environ["PATH_INFO"]
    is_read_request = method == "GET" or method == "HEAD"

    try:
        if is_read_request and path == "/":
            return send_file(start_response, STATIC_DIR / "index.html", "text/html; charset=utf-8")

        elif is_read_request and path == "/style.css":
            return send_file(start_response, STATIC_DIR / "style.css", "text/css; charset=utf-8")

        elif is_read_request and path == "/game.js":
            return send_file(start_response, STATIC_DIR / "game.js", "text/javascript; charset=utf-8")

        elif is_read_request and path == "/health":
            return send_text(start_response, "200 OK", "ok")

        elif is_read_request and path == "/api/leaderboard":
            return send_json(start_response, "200 OK", {"leaderboard": get_leaderboard()})

        elif method == "POST" and path == "/api/start":
            data = read_json(environ)
            name = clean_name(data.get("name", ""))
            game_id = start_new_game(name)

            return send_json(
                start_response,
                "200 OK",
                {
                    "game_id": game_id,
                    "name": name,
                    "seconds": GAME_SECONDS,
                    "score": 0,
                    "problem": make_problem(game_id),
                    "leaderboard": get_leaderboard(),
                },
            )

        elif method == "POST" and path == "/api/answer":
            data = read_json(environ)
            game_id = str(data.get("game_id", ""))
            problem_id = str(data.get("problem_id", ""))
            answer_text = str(data.get("answer", "")).strip()

            game = GAMES.get(game_id)
            problem = PROBLEMS.pop(problem_id, None)

            if game is None or problem is None or problem["game_id"] != game_id:
                return send_json(
                    start_response,
                    "400 Bad Request",
                    {"ok": False, "message": "Задача или игра не найдена."},
                )

            if time.time() > game["ends_at"]:
                result = finish_game(game_id)
                result["finished"] = True
                return send_json(start_response, "200 OK", result)

            try:
                answer = int(answer_text)
            except ValueError:
                answer = None

            correct = answer == problem["answer"]
            if correct:
                game["score"] = game["score"] + 1

            return send_json(
                start_response,
                "200 OK",
                {
                    "ok": True,
                    "correct": correct,
                    "right_answer": problem["answer"],
                    "score": game["score"],
                    "finished": False,
                    "problem": make_problem(game_id),
                },
            )

        elif method == "POST" and path == "/api/finish":
            data = read_json(environ)
            game_id = str(data.get("game_id", ""))
            result = finish_game(game_id)
            result["finished"] = True
            return send_json(start_response, "200 OK", result)

        else:
            return send_text(start_response, "404 Not Found", "Страница не найдена.")

    except json.JSONDecodeError:
        return send_json(start_response, "400 Bad Request", {"ok": False, "message": "Неверный JSON."})


if __name__ == "__main__":
    ensure_data_file()

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))

    print(f"Server started: http://{host}:{port}")
    with make_server(host, port, application) as server:
        server.serve_forever()
