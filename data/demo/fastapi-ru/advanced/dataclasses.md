# Использование dataclasses { #using-dataclasses }

FastAPI построен поверх **Pydantic**, и я показывал вам, как использовать Pydantic-модели для объявления HTTP-запросов и HTTP-ответов.

Но FastAPI также поддерживает использование [`dataclasses`](https://docs.python.org/3/library/dataclasses.html) тем же способом:

```python
from dataclasses import dataclass

from fastapi import FastAPI

@dataclass
class Item:
    name: str
    price: float
    description: str | None = None
    tax: float | None = None

app = FastAPI()

@app.post("/items/")
async def create_item(item: Item):
    return item
```

Это по-прежнему поддерживается благодаря **Pydantic**, так как в нём есть [встроенная поддержка `dataclasses`](https://pydantic.dev/docs/validation/latest/concepts/dataclasses/#usage-of-stdlib-dataclasses-with-basemodel).

Так что даже если в коде выше Pydantic не используется явно, FastAPI использует Pydantic, чтобы конвертировать стандартные dataclasses в собственный вариант dataclasses от Pydantic.

И, конечно, поддерживаются те же возможности:

* валидация данных
* сериализация данных
* документирование данных и т.д.

Это работает так же, как с Pydantic-моделями. И на самом деле под капотом это достигается тем же образом, с использованием Pydantic.

**Примечание:**

Помните, что dataclasses не умеют всего того, что умеют Pydantic-модели.

Поэтому вам всё ещё может потребоваться использовать Pydantic-модели.

Но если у вас уже есть набор dataclasses, это полезный приём — задействовать их для веб-API на FastAPI. 🤓

## Dataclasses в `response_model` { #dataclasses-in-response-model }

Вы также можете использовать `dataclasses` в параметре `response_model`:

```python
from dataclasses import dataclass, field

from fastapi import FastAPI

@dataclass
class Item:
    name: str
    price: float
    tags: list[str] = field(default_factory=list)
    description: str | None = None
    tax: float | None = None

app = FastAPI()

@app.get("/items/next", response_model=Item)
async def read_next_item():
    return {
        "name": "Island In The Moon",
        "price": 12.99,
        "description": "A place to be playin' and havin' fun",
        "tags": ["breater"],
    }
```

Этот dataclass будет автоматически преобразован в Pydantic dataclass.

Таким образом, его схема появится в интерфейсе документации API:

## Dataclasses во вложенных структурах данных { #dataclasses-in-nested-data-structures }

Вы также можете комбинировать `dataclasses` с другими аннотациями типов, чтобы создавать вложенные структуры данных.

В некоторых случаях вам всё же может понадобиться использовать версию `dataclasses` из Pydantic. Например, если у вас возникают ошибки с автоматически генерируемой документацией API.

В таком случае вы можете просто заменить стандартные `dataclasses` на `pydantic.dataclasses`, которая является полностью совместимой заменой (drop-in replacement):

```python
from dataclasses import field  # (1)

from fastapi import FastAPI
from pydantic.dataclasses import dataclass  # (2)

@dataclass
class Item:
    name: str
    description: str | None = None

@dataclass
class Author:
    name: str
    items: list[Item] = field(default_factory=list)  # (3)

app = FastAPI()

@app.post("/authors/{author_id}/items/", response_model=Author)  # (4)
async def create_author_items(author_id: str, items: list[Item]):  # (5)
    return {"name": author_id, "items": items}  # (6)

@app.get("/authors/", response_model=list[Author])  # (7)
def get_authors():  # (8)
    return [  # (9)
        {
            "name": "Breaters",
            "items": [
                {
                    "name": "Island In The Moon",
                    "description": "A place to be playin' and havin' fun",
                },
                {"name": "Holy Buddies"},
            ],
        },
        {
            "name": "System of an Up",
            "items": [
                {
                    "name": "Salt",
                    "description": "The kombucha mushroom people's favorite",
                },
                {"name": "Pad Thai"},
                {
                    "name": "Lonely Night",
                    "description": "The mostests lonliest nightiest of allest",
                },
            ],
        },
    ]
```

1. Мы по-прежнему импортируем `field` из стандартных `dataclasses`.

2. `pydantic.dataclasses` — полностью совместимая замена (drop-in replacement) для `dataclasses`.

3. Dataclass `Author` содержит список dataclass `Item`.

4. Dataclass `Author` используется в параметре `response_model`.

5. Вы можете использовать и другие стандартные аннотации типов вместе с dataclasses в качестве тела запроса.

    В этом случае это список dataclass `Item`.

6. Здесь мы возвращаем словарь, содержащий `items`, который является списком dataclass.

    FastAPI по-прежнему способен сериализовать данные в JSON.

7. Здесь `response_model` использует аннотацию типа — список dataclass `Author`.

    Снова, вы можете комбинировать `dataclasses` со стандартными аннотациями типов.

8. Обратите внимание, что эта *функция-обработчик пути* использует обычный `def` вместо `async def`.

    Как и всегда в FastAPI, вы можете сочетать `def` и `async def` по необходимости.

    Если хотите освежить в памяти, когда что использовать, посмотрите раздел _"Нет времени?"_ в документации про [`async` и `await`](../async.md#in-a-hurry).

9. Эта *функция-обработчик пути* возвращает не dataclasses (хотя могла бы), а список словарей с внутренними данными.

    FastAPI использует параметр `response_model` (в котором заданы dataclasses), чтобы преобразовать HTTP-ответ.

Вы можете комбинировать `dataclasses` с другими аннотациями типов множеством способов, чтобы формировать сложные структуры данных.

Смотрите подсказки в коде выше, чтобы увидеть более конкретные детали.

## Узнать больше { #learn-more }

Вы также можете комбинировать `dataclasses` с другими Pydantic-моделями, наследоваться от них, включать их в свои модели и т.д.

Чтобы узнать больше, посмотрите [документацию Pydantic о dataclasses](https://pydantic.dev/docs/validation/latest/concepts/dataclasses/).

## Версия { #version }

Доступно начиная с версии FastAPI `0.67.0`. 🔖
