# Подключение WSGI — Flask, Django и другие { #including-wsgi-flask-django-others }

Вы можете монтировать WSGI‑приложения, как вы видели в [Подприложения — Mounts](sub-applications.md), [За прокси‑сервером](behind-a-proxy.md).

Для этого вы можете использовать `WSGIMiddleware` и обернуть им ваше WSGI‑приложение, например Flask, Django и т.д.

## Использование `WSGIMiddleware` { #using-wsgimiddleware }

**Примечание:**

Для этого требуется добавить `a2wsgi` в ваш проект, например с помощью `uv add a2wsgi`.

Нужно импортировать `WSGIMiddleware` из `a2wsgi`.

Затем оберните WSGI‑приложение (например, Flask) в middleware (промежуточный слой).

После этого смонтируйте его на путь.

```python
from a2wsgi import WSGIMiddleware
from fastapi import FastAPI
from flask import Flask, request
from markupsafe import escape

flask_app = Flask(__name__)

@flask_app.route("/")
def flask_main():
    name = request.args.get("name", "World")
    return f"Hello, {escape(name)} from Flask!"

app = FastAPI()

@app.get("/v2")
def read_main():
    return {"message": "Hello World"}

app.mount("/v1", WSGIMiddleware(flask_app))
```

**Примечание:**

Ранее рекомендовалось использовать `WSGIMiddleware` из `fastapi.middleware.wsgi`, но теперь он помечен как устаревший.

Вместо него рекомендуется использовать пакет `a2wsgi`. Использование остаётся таким же.

Просто убедитесь, что пакет `a2wsgi` установлен, и правильно импортируйте `WSGIMiddleware` из `a2wsgi`.

## Проверьте { #check-it }

Теперь каждый HTTP‑запрос по пути `/v1/` будет обрабатываться приложением Flask.

А всё остальное будет обрабатываться **FastAPI**.

Если вы запустите это и перейдёте по [http://localhost:8000/v1/](http://localhost:8000/v1/), вы увидите HTTP‑ответ от Flask:

```txt
Hello, World from Flask!
```

А если вы перейдёте по [http://localhost:8000/v2](http://localhost:8000/v2), вы увидите HTTP‑ответ от FastAPI:

```json
{
    "message": "Hello World"
}
```
