# Дополнительные типы данных { #extra-data-types }

До сих пор вы использовали простые типы данных, такие как:

* `int`
* `float`
* `str`
* `bool`

Но вы также можете использовать и более сложные типы.

При этом у вас останутся те же возможности, что и до сих пор:

* Отличная поддержка редактора кода.
* Преобразование данных из входящих HTTP-запросов.
* Преобразование данных для ответа.
* Валидация данных.
* Автоматическая аннотация и документация.

## Другие типы данных { #other-data-types }

Ниже перечислены некоторые из дополнительных типов данных, которые вы можете использовать:

* `UUID`:
    * Стандартный "Универсальный уникальный идентификатор", используемый в качестве идентификатора во многих базах данных и системах.
    * В HTTP-запросах и HTTP-ответах будет представлен как `str`.
* `datetime.datetime`:
    * Python `datetime.datetime`.
    * В HTTP-запросах и HTTP-ответах будет представлен как `str` в формате ISO 8601, например: `2008-09-15T15:53:00+05:00`.
* `datetime.date`:
    * Python `datetime.date`.
    * В HTTP-запросах и HTTP-ответах будет представлен как `str` в формате ISO 8601, например: `2008-09-15`.
* `datetime.time`:
    * Python `datetime.time`.
    * В HTTP-запросах и HTTP-ответах будет представлен как `str` в формате ISO 8601, например: `14:23:55.003`.
* `datetime.timedelta`:
    * Python `datetime.timedelta`.
    * В HTTP-запросах и HTTP-ответах будет представлен в виде общего количества секунд типа `float`.
    * Pydantic также позволяет представить его как "кодировку разницы во времени ISO 8601", [см. документацию для получения дополнительной информации](https://pydantic.dev/docs/validation/latest/concepts/serialization/#custom-serializers).
* `frozenset`:
    * В HTTP-запросах и HTTP-ответах обрабатывается так же, как и `set`:
        * В HTTP-запросах будет прочитан список, исключены дубликаты и преобразован в `set`.
        * В HTTP-ответах `set` будет преобразован в `list`.
        * В сгенерированной схеме будет указано, что значения `set` уникальны (с помощью JSON-схемы `uniqueItems`).
* `bytes`:
    * Стандартный Python `bytes`.
    * В HTTP-запросах и HTTP-ответах будет рассматриваться как `str`.
    * В сгенерированной схеме будет указано, что это `str` в "формате" `binary`.
* `Decimal`:
    * Стандартный Python `Decimal`.
    * В HTTP-запросах и HTTP-ответах обрабатывается так же, как и `float`.
* Вы можете проверить все допустимые типы данных Pydantic здесь: [Типы данных Pydantic](https://pydantic.dev/docs/validation/latest/concepts/types/).

## Пример { #example }

Вот пример *операции пути* с параметрами, который демонстрирует некоторые из вышеперечисленных типов.

```python
from datetime import datetime, time, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import Body, FastAPI

app = FastAPI()

@app.put("/items/{item_id}")
async def read_items(
    item_id: UUID,
    start_datetime: Annotated[datetime, Body()],
    end_datetime: Annotated[datetime, Body()],
    process_after: Annotated[timedelta, Body()],
    repeat_at: Annotated[time | None, Body()] = None,
):
    start_process = start_datetime + process_after
    duration = end_datetime - start_process
    return {
        "item_id": item_id,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "process_after": process_after,
        "repeat_at": repeat_at,
        "start_process": start_process,
        "duration": duration,
    }
```

Обратите внимание, что параметры внутри функции имеют свой естественный тип данных, и вы, например, можете выполнять обычные манипуляции с датами, такие как:

```python
from datetime import datetime, time, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import Body, FastAPI

app = FastAPI()

@app.put("/items/{item_id}")
async def read_items(
    item_id: UUID,
    start_datetime: Annotated[datetime, Body()],
    end_datetime: Annotated[datetime, Body()],
    process_after: Annotated[timedelta, Body()],
    repeat_at: Annotated[time | None, Body()] = None,
):
    start_process = start_datetime + process_after
    duration = end_datetime - start_process
    return {
        "item_id": item_id,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "process_after": process_after,
        "repeat_at": repeat_at,
        "start_process": start_process,
        "duration": duration,
    }
```
