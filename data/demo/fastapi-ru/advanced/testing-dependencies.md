# Тестирование зависимостей с переопределениями { #testing-dependencies-with-overrides }

## Переопределение зависимостей во время тестирования { #overriding-dependencies-during-testing }

Есть сценарии, когда может понадобиться переопределить зависимость во время тестирования.

Вы не хотите, чтобы исходная зависимость выполнялась (и любые её подзависимости тоже).

Вместо этого вы хотите предоставить другую зависимость, которая будет использоваться только во время тестов (возможно, только в некоторых конкретных тестах) и будет возвращать значение, которое можно использовать везде, где использовалось значение исходной зависимости.

### Варианты использования: внешний сервис { #use-cases-external-service }

Пример: у вас есть внешний провайдер аутентификации, к которому нужно обращаться.

Вы отправляете ему токен, а он возвращает аутентифицированного пользователя.

Такой провайдер может брать плату за каждый запрос, и его вызов может занимать больше времени, чем использование фиксированного мок-пользователя для тестов.

Вероятно, вы захотите протестировать внешний провайдер один раз, но не обязательно вызывать его для каждого запускаемого теста.

В таком случае вы можете переопределить зависимость, которая обращается к этому провайдеру, и использовать собственную зависимость, возвращающую мок-пользователя, только для ваших тестов.

### Используйте атрибут `app.dependency_overrides` { #use-the-app-dependency-overrides-attribute }

Для таких случаев у вашего приложения **FastAPI** есть атрибут `app.dependency_overrides`, это простой `dict`.

Чтобы переопределить зависимость для тестирования, укажите в качестве ключа исходную зависимость (функцию), а в качестве значения — ваше переопределение зависимости (другую функцию).

Тогда **FastAPI** будет вызывать это переопределение вместо исходной зависимости.

```python
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}

@app.get("/items/")
async def read_items(commons: Annotated[dict, Depends(common_parameters)]):
    return {"message": "Hello Items!", "params": commons}

@app.get("/users/")
async def read_users(commons: Annotated[dict, Depends(common_parameters)]):
    return {"message": "Hello Users!", "params": commons}

client = TestClient(app)

async def override_dependency(q: str | None = None):
    return {"q": q, "skip": 5, "limit": 10}

app.dependency_overrides[common_parameters] = override_dependency

def test_override_in_items():
    response = client.get("/items/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Hello Items!",
        "params": {"q": None, "skip": 5, "limit": 10},
    }

def test_override_in_items_with_q():
    response = client.get("/items/?q=foo")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Hello Items!",
        "params": {"q": "foo", "skip": 5, "limit": 10},
    }

def test_override_in_items_with_params():
    response = client.get("/items/?q=foo&skip=100&limit=200")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Hello Items!",
        "params": {"q": "foo", "skip": 5, "limit": 10},
    }
```

**Совет:**

Вы можете задать переопределение для зависимости, используемой в любом месте вашего приложения **FastAPI**.

Исходная зависимость может использоваться в функции-обработчике пути, в декораторе операции пути (когда вы не используете возвращаемое значение), в вызове `.include_router()` и т.д.

FastAPI всё равно сможет её переопределить.

Затем вы можете сбросить переопределения (удалить их), установив `app.dependency_overrides` в пустой `dict`:

```python
app.dependency_overrides = {}
```

**Совет:**

Если вы хотите переопределять зависимость только во время некоторых тестов, задайте переопределение в начале теста (внутри функции теста) и сбросьте его в конце (в конце функции теста).
