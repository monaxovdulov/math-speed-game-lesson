# FastAPI без декораторов

## Зачем эта ветка

В версии на `wsgiref` ученик видит много низкоуровневых деталей:

- `environ`;
- `start_response`;
- HTTP-заголовки;
- байты;
- ручную отправку JSON.

Это полезно для понимания, но тяжело для первого знакомства с веб-приложением.

Эта ветка показывает тот же проект на FastAPI. Здесь идея выше уровнем:

```text
URL -> функция Python -> словарь или файл -> ответ браузеру
```

## Где роутинг

Обычно FastAPI часто показывают через декораторы над функциями.
В этом проекте декораторы не используются. Вместо них маршруты указаны явно:

```python
app.add_api_route("/", page_index, methods=["GET", "HEAD"])
app.add_api_route("/api/start", api_start, methods=["POST"])
app.add_api_route("/api/answer", api_answer, methods=["POST"])
app.add_api_route("/api/finish", api_finish, methods=["POST"])
```

Это читается так:

```text
если пришел GET /, вызови функцию page_index
если пришел POST /api/start, вызови функцию api_start
если пришел POST /api/answer, вызови функцию api_answer
```

## Что FastAPI делает за нас

FastAPI берет на себя детали, которые в низкоуровневой версии приходилось писать вручную.

| Что нужно сделать | В низкоуровневой версии | В FastAPI-версии |
| --- | --- | --- |
| Принять HTTP-запрос | `application(environ, start_response)` | FastAPI делает сам |
| Вернуть JSON | `json.dumps`, `encode`, заголовки | Можно вернуть обычный словарь |
| Вернуть файл | открыть файл и отдать байты | `FileResponse(file_path)` |
| Вернуть текст | собрать байты и заголовки | `PlainTextResponse("ok")` |
| Связать URL и функцию | большой `if / elif` | `app.add_api_route(...)` |

## Почему `data=Body(default=None)`

В функциях `api_start`, `api_answer` и `api_finish` есть аргумент:

```python
def api_start(data=Body(default=None)):
```

Он означает:

```text
FastAPI, возьми JSON из тела запроса и положи его в переменную data.
```

Например браузер отправляет:

```json
{
  "name": "Аня"
}
```

А функция получает:

```python
data = {"name": "Аня"}
```

## Как объяснить ученику

Главное место для урока - нижняя часть `server.py`:

```python
app.add_api_route("/", page_index, methods=["GET", "HEAD"])
app.add_api_route("/api/start", api_start, methods=["POST"])
app.add_api_route("/api/answer", api_answer, methods=["POST"])
app.add_api_route("/api/finish", api_finish, methods=["POST"])
```

Потом можно открыть функции `page_index`, `api_start`, `api_answer`, `api_finish` и показать:

```text
каждый URL запускает свою обычную Python-функцию
```

## Как запустить

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 server.py
```

Открыть:

```text
http://127.0.0.1:8000/
```
