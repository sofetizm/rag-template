# Асинхронное тестирование { #async-tests }

Вы уже видели, как тестировать **FastAPI** приложение, используя имеющийся класс `TestClient`. К этому моменту вы видели только, как писать тесты в синхронном стиле без использования `async` функций.

Возможность использования асинхронных функций в ваших тестах может быть полезна, когда, например, вы асинхронно обращаетесь к вашей базе данных. Представьте, что вы хотите отправить HTTP-запросы в ваше FastAPI приложение, а затем при помощи асинхронной библиотеки для работы с базой данных удостовериться, что ваш бекэнд корректно записал данные в базу данных.

Давайте рассмотрим, как мы можем это реализовать.

## pytest.mark.anyio { #pytest-mark-anyio }

Если мы хотим вызывать асинхронные функции в наших тестах, то наши тестовые функции должны быть асинхронными. AnyIO предоставляет для этого отличный плагин, который позволяет нам указывать, какие тестовые функции должны вызываться асинхронно.

## HTTPX { #httpx }

Даже если **FastAPI** приложение использует обычные функции `def` вместо `async def`, это все равно `async` приложение 'под капотом'.

Чтобы работать с асинхронным FastAPI приложением в ваших обычных тестовых функциях `def`, используя стандартный pytest, `TestClient` внутри себя делает некоторую магию. Но эта магия перестает работать, когда мы используем его внутри асинхронных функций. Запуская наши тесты асинхронно, мы больше не можем использовать `TestClient` внутри наших тестовых функций.

`TestClient` основан на [HTTPX](https://www.python-httpx.org), и, к счастью, мы можем использовать его (`HTTPX`) напрямую для тестирования API.

## Пример { #example }

В качестве простого примера, давайте рассмотрим файловую структуру, схожую с описанной в [Большие приложения](../tutorial/bigger-applications.md) и [Тестирование](../tutorial/testing.md):

```
.
├── app
│   ├── __init__.py
│   ├── main.py
│   └── test_main.py
```

Файл `main.py`:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Tomato"}
```

Файл `test_main.py` содержит тесты для `main.py`, теперь он может выглядеть так:

```python
import pytest
from httpx import ASGITransport, AsyncClient

from .main import app

@pytest.mark.anyio
async def test_root():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Tomato"}
```

## Запуск тестов { #run-it }

Вы можете запустить свои тесты как обычно:

```console
$ uv run pytest

---> 100%
```

## Подробнее { #in-detail }

Маркер `@pytest.mark.anyio` говорит pytest, что тестовая функция должна быть вызвана асинхронно:

```python
import pytest
from httpx import ASGITransport, AsyncClient

from .main import app

@pytest.mark.anyio
async def test_root():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Tomato"}
```

**Подсказка:**

Обратите внимание, что тестовая функция теперь `async def` вместо простого `def`, как это было при использовании `TestClient`.

Затем мы можем создать `AsyncClient` со ссылкой на приложение и посылать асинхронные HTTP-запросы, используя `await`.

```python
import pytest
from httpx import ASGITransport, AsyncClient

from .main import app

@pytest.mark.anyio
async def test_root():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Tomato"}
```

Это эквивалентно следующему:

```python
response = client.get("/")
```

...которое мы использовали для отправки наших HTTP-запросов с `TestClient`.

**Подсказка:**

Обратите внимание, что мы используем async/await с новым `AsyncClient` - HTTP-запрос асинхронный.

**Внимание:**

Если ваше приложение полагается на события lifespan, то `AsyncClient` не запустит эти события. Чтобы обеспечить их срабатывание, используйте `LifespanManager` из [florimondmanca/asgi-lifespan](https://github.com/florimondmanca/asgi-lifespan#usage).

## Вызов других асинхронных функций { #other-asynchronous-function-calls }

Теперь тестовая функция стала асинхронной, поэтому внутри нее вы можете вызывать другие `async` функции (и использовать `await` для ожидания их выполнения), помимо отправки HTTP-запросов в ваше FastAPI приложение в ваших тестах. Как если бы вы вызывали их в любом другом месте вашего кода.

**Подсказка:**

Если вы столкнулись с `RuntimeError: Task attached to a different loop` при вызове асинхронных функций в ваших тестах (например, при использовании [MotorClient для MongoDB](https://stackoverflow.com/questions/41584243/runtimeerror-task-attached-to-a-different-loop)), то не забывайте создавать экземпляры объектов, которым нужен цикл событий, только внутри асинхронных функций, например, в функции обратного вызова `@app.on_event("startup")`.
