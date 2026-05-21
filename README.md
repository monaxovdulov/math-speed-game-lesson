# Математический забег

Учебное веб-приложение на Python и FastAPI: игрок вводит имя, решает случайные математические примеры на время, а общий счет всех игроков сохраняется на сервере в обычном текстовом файле.

Эта ветка показывает более высокий уровень, чем версия на `wsgiref`: FastAPI сам разбирает HTTP и JSON, а URL сопоставляются явно через `app.add_api_route(...)`, без декораторов.

## Как запустить локально

```bash
cd /home/devuser/projects/math-speed-game-lesson
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 server.py
```

Открыть в браузере:

```text
http://127.0.0.1:8000/
```

## Где что лежит

- `server.py` - Python-сервер, маршруты URL, генерация примеров, проверка ответов, запись счета.
- `requirements.txt` - зависимости FastAPI и Uvicorn.
- `static/index.html` - разметка страницы.
- `static/style.css` - внешний вид страницы.
- `static/game.js` - код браузера: таймер, отправка имени и ответов на сервер.
- `data/scores.txt` - текстовый файл со счетом игроков. Создается автоматически.
- `docs/scheme.md` - схема ролей: пользователь, браузер, домен, IP, веб-сервер, Python, файл.
- `docs/how-it-works.md` - подробное объяснение работы приложения.
- `docs/lesson-plan.md` - порядок объяснения проекта на уроке.
- `docs/fastapi-no-decorators.md` - объяснение FastAPI-версии без декораторов.
- `deploy/Caddyfile.math-speed-game` - фрагмент Caddy для публичного домена.

## Явное сопоставление URL

В `server.py` внизу есть явный список маршрутов:

```python
app.add_api_route("/", page_index, methods=["GET", "HEAD"])
app.add_api_route("/api/start", api_start, methods=["POST"])
app.add_api_route("/api/answer", api_answer, methods=["POST"])
```

Это и есть роутинг: FastAPI смотрит на метод запроса и путь URL, затем вызывает нужную функцию.

## Основные URL

| URL | Метод | Роль |
| --- | --- | --- |
| `/` | `GET` | Отдать HTML-страницу игры |
| `/style.css` | `GET` | Отдать стили |
| `/game.js` | `GET` | Отдать код браузера |
| `/api/start` | `POST` | Начать игру и создать первый пример |
| `/api/answer` | `POST` | Проверить ответ игрока |
| `/api/finish` | `POST` | Закончить игру и сохранить счет |
| `/api/leaderboard` | `GET` | Получить общий счет |
| `/health` | `GET` | Проверка, что сервер жив |

## Формат текстового файла

Счет хранится в `data/scores.txt` в простом текстовом формате:

```text
Аня|12
Борис|7
```

Слева имя игрока, справа общий счет. Символ `|` нужен как разделитель.

## Деплой

В репозитории есть `Dockerfile` и `compose.yml`. Контейнер подключается к сети `granit-staging_default`, чтобы существующий Caddy мог проксировать домен на сервис `math-speed-game-lesson:8000`.

Публичный адрес:

```text
https://питоны-батоны.рф/
https://xn----8sbc0azdcec5af8hg.xn--p1ai/
```
