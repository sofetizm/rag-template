# Конфигурация операции пути { #path-operation-configuration }

Существует несколько параметров, которые вы можете передать вашему *декоратору операции пути* для его настройки.

**Внимание:**

Помните, что эти параметры передаются непосредственно *декоратору операции пути*, а не вашей *функции-обработчику пути*.

## Статус-код ответа { #response-status-code }

Вы можете определить (HTTP) `status_code`, который будет использован в ответах вашей *операции пути*.

Вы можете передать только `int`-значение кода, например `404`.

Но если вы не помните, для чего нужен каждый числовой код, вы можете использовать сокращенные константы в `status`:

```python
from fastapi import FastAPI, status
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    tags: set[str] = set()

@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(item: Item) -> Item:
    return item
```

Этот статус-код будет использован в ответе и будет добавлен в схему OpenAPI.

**Технические детали:**

Вы также можете использовать `from starlette import status`.

**FastAPI** предоставляет тот же `starlette.status` под псевдонимом `fastapi.status` для удобства разработчика. Но его источник - это непосредственно Starlette.

## Теги { #tags }

Вы можете добавлять теги к вашей *операции пути*, передав параметр `tags` с `list` из `str` (обычно в нём только одна строка):

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    tags: set[str] = set()

@app.post("/items/", tags=["items"])
async def create_item(item: Item) -> Item:
    return item

@app.get("/items/", tags=["items"])
async def read_items():
    return [{"name": "Foo", "price": 42}]

@app.get("/users/", tags=["users"])
async def read_users():
    return [{"username": "johndoe"}]
```

Они будут добавлены в схему OpenAPI и будут использованы автоматическими интерфейсами документации:

### Теги с перечислениями { #tags-with-enums }

Если у вас большое приложение, вы можете прийти к необходимости добавить **несколько тегов**, и возможно, вы захотите убедиться в том, что всегда используете **один и тот же тег** для связанных *операций пути*.

В этих случаях, имеет смысл хранить теги в классе `Enum`.

**FastAPI** поддерживает это так же, как и в случае с обычными строками:

```python
from enum import Enum

from fastapi import FastAPI

app = FastAPI()

class Tags(Enum):
    items = "items"
    users = "users"

@app.get("/items/", tags=[Tags.items])
async def get_items():
    return ["Portal gun", "Plumbus"]

@app.get("/users/", tags=[Tags.users])
async def read_users():
    return ["Rick", "Morty"]
```

## Краткое и развёрнутое содержание { #summary-and-description }

Вы можете добавить параметры `summary` и `description`:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    tags: set[str] = set()

@app.post(
    "/items/",
    summary="Create an item",
    description="Create an item with all the information, name, description, price, tax and a set of unique tags",
)
async def create_item(item: Item) -> Item:
    return item
```

## Описание из строк документации { #description-from-docstring }

Так как описания обычно длинные и содержат много строк, вы можете объявить описание *операции пути* в строке документации функции, и **FastAPI** прочитает её оттуда.

Вы можете использовать [Markdown](https://en.wikipedia.org/wiki/Markdown) в строке документации, и он будет интерпретирован и отображён корректно (с учетом отступа в строке документации).

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    tags: set[str] = set()

@app.post("/items/", summary="Create an item")
async def create_item(item: Item) -> Item:
    """
    Create an item with all the information:

    - **name**: each item must have a name
    - **description**: a long description
    - **price**: required
    - **tax**: if the item doesn't have tax, you can omit this
    - **tags**: a set of unique tag strings for this item
    """
    return item
```

Он будет использован в интерактивной документации:

## Описание ответа { #response-description }

Вы можете указать описание ответа с помощью параметра `response_description`:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    tags: set[str] = set()

@app.post(
    "/items/",
    summary="Create an item",
    response_description="The created item",
)
async def create_item(item: Item) -> Item:
    """
    Create an item with all the information:

    - **name**: each item must have a name
    - **description**: a long description
    - **price**: required
    - **tax**: if the item doesn't have tax, you can omit this
    - **tags**: a set of unique tag strings for this item
    """
    return item
```

**Примечание:**

Помните, что `response_description` относится конкретно к ответу, а `description` относится к *операции пути* в целом.

**Совет:**

OpenAPI указывает, что каждой *операции пути* необходимо описание ответа.

Если вдруг вы не укажете его, то **FastAPI** автоматически сгенерирует это описание с текстом "Successful response".

## Обозначение *операции пути* как устаревшей { #deprecate-a-path-operation }

Если вам необходимо пометить *операцию пути* как устаревшую, при этом не удаляя её, передайте параметр `deprecated`:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/", tags=["items"])
async def read_items():
    return [{"name": "Foo", "price": 42}]

@app.get("/users/", tags=["users"])
async def read_users():
    return [{"username": "johndoe"}]

@app.get("/elements/", tags=["items"], deprecated=True)
async def read_elements():
    return [{"item_id": "Foo"}]
```

Она будет четко помечена как устаревшая в интерактивной документации:

Проверьте, как будут выглядеть устаревшие и не устаревшие *операции пути*:

## Резюме { #recap }

Вы можете легко конфигурировать и добавлять метаданные в ваши *операции пути*, передавая параметры *декораторам операций пути*.
