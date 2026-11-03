# Тестирование { #testing }

Благодаря [Starlette](https://starlette.dev/testclient/), тестировать приложения **FastAPI** легко и приятно.

Тестирование основано на библиотеке [HTTPX](https://www.python-httpx.org), которая в свою очередь основана на библиотеке Requests, так что все действия знакомы и интуитивно понятны.

Используя эти инструменты, Вы можете напрямую задействовать [pytest](https://docs.pytest.org/) с **FastAPI**.

## Использование `TestClient` { #using-testclient }

**Примечание:**

Для использования `TestClient` сначала установите [`httpx`](https://www.python-httpx.org).

Добавьте его в Ваш проект:

```console
$ uv add httpx
```

Импортируйте `TestClient`.

Создайте объект `TestClient`, передав ему в качестве параметра Ваше приложение **FastAPI**.

Создайте функцию, название которой должно начинаться с `test_` (это стандарт из соглашений `pytest`).

Используйте объект `TestClient` так же, как Вы используете `httpx`.

Напишите простое утверждение с `assert` дабы проверить истинность Python-выражения (это тоже стандарт `pytest`).

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/")
async def read_main():
    return {"msg": "Hello World"}

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}
```

**Подсказка:**

Обратите внимание, что тестирующая функция является обычной `def`, а не асинхронной `async def`.

И вызов клиента также осуществляется без `await`.

Это позволяет вам использовать `pytest` без лишних усложнений.

**Технические детали:**

Также можно написать `from starlette.testclient import TestClient`.

**FastAPI** предоставляет тот же самый `starlette.testclient` как `fastapi.testclient`. Это всего лишь небольшое удобство для Вас, как разработчика. Но он берётся напрямую из Starlette.

**Подсказка:**

Если для тестирования Вам, помимо отправки запросов к приложению FastAPI, необходимо вызывать асинхронные функции (например, асинхронные функции базы данных), то ознакомьтесь со страницей [Асинхронное тестирование](../advanced/async-tests.md) в расширенном руководстве.

## Разделение тестов { #separating-tests }

В реальном приложении Вы, вероятно, разместите тесты в отдельном файле.

Кроме того, Ваше приложение **FastAPI** может состоять из нескольких файлов, модулей и т.п.

### Файл приложения **FastAPI** { #fastapi-app-file }

Допустим, структура файлов Вашего приложения похожа на ту, что описана на странице [Более крупные приложения](bigger-applications.md):

```
.
├── app
│   ├── __init__.py
│   └── main.py
```

В файле `main.py` находится Ваше приложение **FastAPI**:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_main():
    return {"msg": "Hello World"}
```

### Файл тестов { #testing-file }

Также у Вас может быть файл `test_main.py` содержащий тесты. Он может находиться в том же Python-пакете (в той же директории с файлом `__init__.py`):

```hl_lines
.
├── app
│   ├── __init__.py
│   ├── main.py
│   └── test_main.py
```

Так как этот файл находится в том же пакете, для импорта объекта `app` из модуля `main` (`main.py`) Вы можете использовать относительный импорт:

```python
from fastapi.testclient import TestClient

from .main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}
```

...и писать дальше тесты, как и раньше.

## Тестирование: расширенный пример { #testing-extended-example }

Теперь давайте расширим наш пример и добавим деталей, чтоб посмотреть, как тестировать различные части приложения.

### Расширенный файл приложения **FastAPI** { #extended-fastapi-app-file }

Мы продолжим работу с той же файловой структурой, что и ранее:

```
.
├── app
│   ├── __init__.py
│   ├── main.py
│   └── test_main.py
```

Предположим, что теперь в файле `main.py` с приложением **FastAPI** есть несколько других **операций пути**.

В нём описана операция `GET`, которая может вернуть ошибку.

Ещё есть операция `POST`, и она может вернуть несколько ошибок.

Обе *операции пути* требуют наличия в запросе HTTP-заголовка `X-Token`.

```python
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

fake_secret_token = "coneofsilence"

fake_db = {
    "foo": {"id": "foo", "title": "Foo", "description": "There goes my hero"},
    "bar": {"id": "bar", "title": "Bar", "description": "The bartenders"},
}

app = FastAPI()

class Item(BaseModel):
    id: str
    title: str
    description: str | None = None

@app.get("/items/{item_id}", response_model=Item)
async def read_main(item_id: str, x_token: Annotated[str, Header()]):
    if x_token != fake_secret_token:
        raise HTTPException(status_code=400, detail="Invalid X-Token header")
    if item_id not in fake_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return fake_db[item_id]

@app.post("/items/")
async def create_item(item: Item, x_token: Annotated[str, Header()]) -> Item:
    if x_token != fake_secret_token:
        raise HTTPException(status_code=400, detail="Invalid X-Token header")
    if item.id in fake_db:
        raise HTTPException(status_code=409, detail="Item already exists")
    fake_db[item.id] = item.model_dump()
    return item
```

### Расширенный файл тестов { #extended-testing-file }

Теперь можно обновить файл `test_main.py`, добавив в него расширенные тесты:

```python
from fastapi.testclient import TestClient

from .main import app

client = TestClient(app)

def test_read_item():
    response = client.get("/items/foo", headers={"X-Token": "coneofsilence"})
    assert response.status_code == 200
    assert response.json() == {
        "id": "foo",
        "title": "Foo",
        "description": "There goes my hero",
    }

def test_read_item_bad_token():
    response = client.get("/items/foo", headers={"X-Token": "hailhydra"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid X-Token header"}

def test_read_nonexistent_item():
    response = client.get("/items/baz", headers={"X-Token": "coneofsilence"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}

def test_create_item():
    response = client.post(
        "/items/",
        headers={"X-Token": "coneofsilence"},
        json={"id": "foobar", "title": "Foo Bar", "description": "The Foo Barters"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": "foobar",
        "title": "Foo Bar",
        "description": "The Foo Barters",
    }

def test_create_item_bad_token():
    response = client.post(
        "/items/",
        headers={"X-Token": "hailhydra"},
        json={"id": "bazz", "title": "Bazz", "description": "Drop the bazz"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid X-Token header"}

def test_create_existing_item():
    response = client.post(
        "/items/",
        headers={"X-Token": "coneofsilence"},
        json={
            "id": "foo",
            "title": "The Foo ID Stealers",
            "description": "There goes my stealer",
        },
    )
    assert response.status_code == 409
    assert response.json() == {"detail": "Item already exists"}
```

Если Вы не знаете, как передать информацию в запросе, можете воспользоваться поиском (Google) и задать вопрос: "Как передать информацию в запросе с помощью `httpx`", можно даже спросить: "Как передать информацию в запросе с помощью `requests`", поскольку дизайн HTTPX основан на дизайне Requests.

Затем Вы просто применяете найденные ответы в тестах.

Например:

* Чтобы передать *path*-параметр или *query*-параметр, добавьте его непосредственно в URL.
* Чтобы передать тело запроса JSON, передайте Python-объект (например: `dict`) через именованный параметр `json`.
* Если же Вам необходимо отправить *данные формы* вместо JSON, то используйте параметр `data` вместо `json`.
* Для передачи *HTTP-заголовков*, передайте объект `dict` через параметр `headers`.
* Для передачи *cookies* также передайте `dict`, но через параметр `cookies`.

Для получения дополнительной информации о передаче данных на бэкенд с помощью `httpx` или `TestClient` ознакомьтесь с [документацией HTTPX](https://www.python-httpx.org).

**Примечание:**

Обратите внимание, что `TestClient` принимает данные, которые можно конвертировать в JSON, но не модели Pydantic.

Если в Ваших тестах есть модель Pydantic и Вы хотите отправить её данные в приложение во время тестирования, то можете использовать функцию `jsonable_encoder`, описанную на странице [Кодировщик совместимый с JSON](encoder.md).

## Запуск { #run-it }

Далее Вам нужно установить `pytest`.

Добавьте его в Ваш проект:

```console
$ uv add pytest

---> 100%
```

Он автоматически найдёт все файлы и тесты, выполнит их и предоставит Вам отчёт о результатах тестирования.

Запустите тесты с помощью:

```console
$ uv run pytest

================ test session starts ================
platform linux -- Python 3.6.9, pytest-5.3.5, py-1.8.1, pluggy-0.13.1
rootdir: /home/user/code/superawesome-cli/app
plugins: forked-1.1.3, xdist-1.31.0, cov-2.8.1
collected 6 items

---> 100%

test_main.py ......                            [100%]

================= 1 passed in 0.03s =================
```
