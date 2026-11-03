# JSON-совместимый кодировщик { #json-compatible-encoder }

В некоторых случаях может потребоваться преобразование типа данных (например, Pydantic-модели) в тип, совместимый с JSON (например, `dict`, `list` и т.д.).

Например, если необходимо хранить его в базе данных.

Для этого **FastAPI** предоставляет функцию `jsonable_encoder()`.

## Использование `jsonable_encoder` { #using-the-jsonable-encoder }

Представим, что у вас есть база данных `fake_db`, которая принимает только JSON-совместимые данные.

Например, она не принимает объекты `datetime`, так как они не совместимы с JSON.

В таком случае объект `datetime` следует преобразовать в `str`, содержащую данные в [формате ISO](https://en.wikipedia.org/wiki/ISO_8601).

Точно так же эта база данных не может принять Pydantic-модель (объект с атрибутами), а только `dict`.

Для этого можно использовать функцию `jsonable_encoder`.

Она принимает объект, например, Pydantic-модель, и возвращает его версию, совместимую с JSON:

```python
from datetime import datetime

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

fake_db = {}

class Item(BaseModel):
    title: str
    timestamp: datetime
    description: str | None = None

app = FastAPI()

@app.put("/items/{id}")
def update_item(id: str, item: Item):
    json_compatible_item_data = jsonable_encoder(item)
    fake_db[id] = json_compatible_item_data
```

В данном примере она преобразует Pydantic-модель в `dict`, а `datetime` - в `str`.

Результатом её вызова является объект, который может быть закодирован с помощью функции из стандартной библиотеки Python – [`json.dumps()`](https://docs.python.org/3/library/json.html#json.dumps).

Функция не возвращает большой `str`, содержащий данные в формате JSON (в виде строки). Она возвращает стандартную структуру данных Python (например, `dict`) со значениями и подзначениями, которые совместимы с JSON.

**Примечание:**

`jsonable_encoder` фактически используется **FastAPI** внутри системы для преобразования данных. Однако он полезен и во многих других сценариях.
