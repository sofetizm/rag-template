# События, отправляемые сервером (SSE) { #server-sent-events-sse }

Вы можете передавать данные потоком клиенту, используя Server-Sent Events (SSE).

Это похоже на [Стриминг JSON Lines](stream-json-lines.md), но использует формат `text/event-stream`, который нативно поддерживается браузерами через [`EventSource` API](https://developer.mozilla.org/en-US/docs/Web/API/EventSource).

**Примечание:**

Добавлено в FastAPI 0.135.0.

## Что такое Server-Sent Events? { #what-are-server-sent-events }

SSE — это стандарт для потоковой передачи данных с сервера на клиента по HTTP.

Каждое событие — это небольшой текстовый блок с «полями», такими как `data`, `event`, `id` и `retry`, разделёнными пустыми строками.

Это выглядит так:

```
data: {"name": "Portal Gun", "price": 999.99}

data: {"name": "Plumbus", "price": 32.99}

```

SSE часто используют для стриминга ответов ИИ в чатах, живых уведомлений, логов и наблюдаемости, а также в других случаях, когда сервер «проталкивает» обновления клиенту.

**Совет:**

Если вам нужно стримить бинарные данные, например видео или аудио, посмотрите расширенное руководство: [Потоковая передача данных](../advanced/stream-data.md).

## Стриминг SSE с FastAPI { #stream-sse-with-fastapi }

Чтобы стримить SSE с FastAPI, используйте `yield` в своей функции-обработчике пути и укажите `response_class=EventSourceResponse`.

Импортируйте `EventSourceResponse` из `fastapi.sse`:

```python
from collections.abc import AsyncIterable, Iterable

from fastapi import FastAPI
from fastapi.sse import EventSourceResponse
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str | None

items = [
    Item(name="Plumbus", description="A multi-purpose household device."),
    Item(name="Portal Gun", description="A portal opening device."),
    Item(name="Meeseeks Box", description="A box that summons a Meeseeks."),
]

@app.get("/items/stream", response_class=EventSourceResponse)
async def sse_items() -> AsyncIterable[Item]:
    for item in items:
        yield item
```

Каждый возвращаемый через `yield` элемент кодируется как JSON и отправляется в поле `data:` события SSE.

Если вы объявите тип возврата как `AsyncIterable[Item]`, FastAPI будет использовать его, чтобы выполнить **валидацию**, добавить **документацию** и **сериализовать** данные с помощью Pydantic.

```python
from collections.abc import AsyncIterable, Iterable

from fastapi import FastAPI
from fastapi.sse import EventSourceResponse
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str | None

items = [
    Item(name="Plumbus", description="A multi-purpose household device."),
    Item(name="Portal Gun", description="A portal opening device."),
    Item(name="Meeseeks Box", description="A box that summons a Meeseeks."),
]

@app.get("/items/stream", response_class=EventSourceResponse)
async def sse_items() -> AsyncIterable[Item]:
    for item in items:
        yield item
```

**Совет:**

Так как Pydantic будет сериализовать это на стороне **Rust**, вы получите значительно более высокую **производительность**, чем если не объявите тип возврата.

### Несинхронные функции-обработчики пути { #non-async-path-operation-functions }

Вы также можете использовать обычные функции `def` (без `async`) и применять `yield` тем же образом.

FastAPI проследит, чтобы выполнение прошло корректно и не блокировало цикл событий.

Так как в этом случае функция не async, правильным типом возврата будет `Iterable[Item]`:

```python
@app.get("/items/stream-no-async", response_class=EventSourceResponse)
def sse_items_no_async() -> Iterable[Item]:
    for item in items:
        yield item
```

### Без объявленного типа возврата { #no-return-type }

Вы также можете опустить тип возврата. FastAPI использует [`jsonable_encoder`](./encoder.md) для преобразования данных и их отправки.

```python
@app.get("/items/stream-no-annotation", response_class=EventSourceResponse)
async def sse_items_no_annotation():
    for item in items:
        yield item
```

## `ServerSentEvent` { #serversentevent }

Если вам нужно задать поля SSE, такие как `event`, `id`, `retry` или `comment`, вы можете возвращать через `yield` объекты `ServerSentEvent` вместо обычных данных.

Импортируйте `ServerSentEvent` из `fastapi.sse`:

```python
from collections.abc import AsyncIterable

from fastapi import FastAPI
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

items = [
    Item(name="Plumbus", price=32.99),
    Item(name="Portal Gun", price=999.99),
    Item(name="Meeseeks Box", price=49.99),
]

@app.get("/items/stream", response_class=EventSourceResponse)
async def stream_items() -> AsyncIterable[ServerSentEvent]:
    yield ServerSentEvent(comment="stream of item updates")
    for i, item in enumerate(items):
        yield ServerSentEvent(data=item, event="item_update", id=str(i + 1), retry=5000)
```

Поле `data` всегда кодируется как JSON. Вы можете передавать любое значение, сериализуемое в JSON, включая Pydantic-модели.

## Необработанные данные { #raw-data }

Если нужно отправлять данные без JSON-кодирования, используйте `raw_data` вместо `data`.

Это полезно для отправки заранее отформатированного текста, строк логов или специальных значений «сентинель», например `[DONE]`.

```python
from collections.abc import AsyncIterable

from fastapi import FastAPI
from fastapi.sse import EventSourceResponse, ServerSentEvent

app = FastAPI()

@app.get("/logs/stream", response_class=EventSourceResponse)
async def stream_logs() -> AsyncIterable[ServerSentEvent]:
    logs = [
        "2025-01-01 INFO  Application started",
        "2025-01-01 DEBUG Connected to database",
        "2025-01-01 WARN  High memory usage detected",
    ]
    for log_line in logs:
        yield ServerSentEvent(raw_data=log_line)
```

**Примечание:**

`data` и `raw_data` взаимно исключают друг друга. В каждом `ServerSentEvent` можно задать только одно из них.

## Возобновление с `Last-Event-ID` { #resuming-with-last-event-id }

Когда браузер переподключается после обрыва соединения, он отправляет последний полученный `id` в HTTP-заголовке `Last-Event-ID`.

Вы можете прочитать его как параметр заголовка и использовать, чтобы возобновить поток с того места, где клиент остановился:

```python
from collections.abc import AsyncIterable
from typing import Annotated

from fastapi import FastAPI, Header
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

items = [
    Item(name="Plumbus", price=32.99),
    Item(name="Portal Gun", price=999.99),
    Item(name="Meeseeks Box", price=49.99),
]

@app.get("/items/stream", response_class=EventSourceResponse)
async def stream_items(
    last_event_id: Annotated[int | None, Header()] = None,
) -> AsyncIterable[ServerSentEvent]:
    start = last_event_id + 1 if last_event_id is not None else 0
    for i, item in enumerate(items):
        if i < start:
            continue
        yield ServerSentEvent(data=item, id=str(i))
```

## SSE с POST { #sse-with-post }

SSE работает с любым HTTP-методом, не только с `GET`.

Это полезно для таких протоколов, как [MCP](https://modelcontextprotocol.io), которые стримят SSE по `POST`:

```python
from collections.abc import AsyncIterable

from fastapi import FastAPI
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel

app = FastAPI()

class Prompt(BaseModel):
    text: str

@app.post("/chat/stream", response_class=EventSourceResponse)
async def stream_chat(prompt: Prompt) -> AsyncIterable[ServerSentEvent]:
    words = prompt.text.split()
    for word in words:
        yield ServerSentEvent(data=word, event="token")
    yield ServerSentEvent(raw_data="[DONE]", event="done")
```

## Технические детали { #technical-details }

FastAPI из коробки реализует некоторые лучшие практики для SSE.

- Отправлять комментарий «ping» для поддержания соединения («keep alive») каждые 15 секунд, когда нет сообщений, чтобы предотвратить закрытие соединения некоторыми прокси, как рекомендовано в [Спецификация HTML: Server-Sent Events](https://html.spec.whatwg.org/multipage/server-sent-events.html#authoring-notes).
- Устанавливать заголовок `Cache-Control: no-cache`, чтобы предотвратить кэширование потока.
- Устанавливать специальный заголовок `X-Accel-Buffering: no`, чтобы предотвратить буферизацию в некоторых прокси, например Nginx.

Вам не нужно ничего настраивать, это работает из коробки. 🤓
