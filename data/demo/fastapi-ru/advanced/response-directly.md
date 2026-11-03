# Возврат ответа напрямую { #return-a-response-directly }

Когда вы создаёте **FastAPI** *операцию пути*, вы можете возвращать из неё любые данные: `dict`, `list`, Pydantic-модель, модель базы данных и т.д.

Если вы объявите [Модель ответа](../tutorial/response-model.md), FastAPI будет использовать её для сериализации данных в JSON с помощью Pydantic.

Если вы не объявите модель ответа, FastAPI использует `jsonable_encoder`, как описано в [JSON кодировщик](../tutorial/encoder.md), и поместит результат в `JSONResponse`.

Также вы можете создать `JSONResponse` напрямую и вернуть его.

**Подсказка:**

Обычно вы получите значительно лучшую производительность, если будете использовать [Модель ответа](../tutorial/response-model.md), а не возвращать `JSONResponse` напрямую, так как в этом случае сериализация данных с помощью Pydantic происходит на стороне Rust.

## Возврат `Response` { #return-a-response }

Вы можете возвращать `Response` или любой его подкласс.

**Примечание:**

`JSONResponse` сам по себе является подклассом `Response`.

И когда вы возвращаете `Response`, **FastAPI** передаст его напрямую.

Это не приведет к преобразованию данных с помощью Pydantic-моделей, содержимое не будет преобразовано в какой-либо тип и т.д.

Это даёт вам большую гибкость. Вы можете возвращать любые типы данных, переопределять любые объявления или валидацию данных и т.д.

Это также накладывает на вас ответственность. Вам нужно удостовериться, что возвращаемые данные корректны, в правильном формате, что их можно сериализовать и т.д.

## Использование `jsonable_encoder` в `Response` { #using-the-jsonable-encoder-in-a-response }

Поскольку **FastAPI** не изменяет объект `Response`, который вы возвращаете, вы должны убедиться, что его содержимое готово к отправке.

Например, вы не можете поместить Pydantic-модель в `JSONResponse`, не преобразовав её сначала в `dict` с помощью преобразования всех типов данных (таких как `datetime`, `UUID` и т.д.) в совместимые с JSON типы.

В таких случаях вы можете использовать `jsonable_encoder` для преобразования данных перед передачей их в ответ:

```python
from datetime import datetime

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

class Item(BaseModel):
    title: str
    timestamp: datetime
    description: str | None = None

app = FastAPI()

@app.put("/items/{id}")
def update_item(id: str, item: Item):
    json_compatible_item_data = jsonable_encoder(item)
    return JSONResponse(content=json_compatible_item_data)
```

**Технические детали:**

Вы также можете использовать `from starlette.responses import JSONResponse`.

**FastAPI** предоставляет `starlette.responses` через `fastapi.responses` просто для вашего удобства, как разработчика. Но большинство доступных Response-классов поступают напрямую из Starlette.

## Возврат пользовательского `Response` { #returning-a-custom-response }

Пример выше показывает все необходимые части, но он пока не очень полезен, так как вы могли бы просто вернуть `item` напрямую, и **FastAPI** поместил бы его в `JSONResponse`, преобразовав в `dict` и т.д. Всё это происходит по умолчанию.

Теперь давайте посмотрим, как можно использовать это для возврата пользовательского ответа.

Допустим, вы хотите вернуть ответ в формате [XML](https://en.wikipedia.org/wiki/XML).

Вы можете поместить ваш XML-контент в строку, поместить её в `Response` и вернуть:

```python
from fastapi import FastAPI, Response

app = FastAPI()

@app.get("/legacy/")
def get_legacy_data():
    data = """<?xml version="1.0"?>
    <shampoo>
    <Header>
        Apply shampoo here.
    </Header>
    <Body>
        You'll have to use soap here.
    </Body>
    </shampoo>
    """
    return Response(content=data, media_type="application/xml")
```

## Как работает модель ответа { #how-a-response-model-works }

Когда вы объявляете [Модель ответа - возвращаемый тип](../tutorial/response-model.md) в операции пути, **FastAPI** будет использовать её для сериализации данных в JSON с помощью Pydantic.

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    tags: list[str] = []

@app.post("/items/")
async def create_item(item: Item) -> Item:
    return item

@app.get("/items/")
async def read_items() -> list[Item]:
    return [
        Item(name="Portal Gun", price=42.0),
        Item(name="Plumbus", price=32.0),
    ]
```

Поскольку это происходит на стороне Rust, производительность будет значительно выше, чем если бы это выполнялось обычным Python и классом `JSONResponse`.

При использовании `response_model` или возвращаемого типа FastAPI не будет использовать `jsonable_encoder` для преобразования данных (что было бы медленнее) и не будет использовать класс `JSONResponse`.

Вместо этого он берёт JSON-байты, сгенерированные Pydantic с использованием модели ответа (или возвращаемого типа), и возвращает `Response` с правильным типом содержимого для JSON (`application/json`) напрямую.

## Примечания { #notes }

Когда вы возвращаете объект `Response` напрямую, его данные не валидируются, не преобразуются (не сериализуются) и не документируются автоматически.

Но вы всё равно можете задокументировать это, как описано в [Дополнительные ответы в OpenAPI](additional-responses.md).

В следующих разделах вы увидите, как использовать/объявлять такие кастомные `Response`, при этом сохраняя автоматическое преобразование данных, документацию и т.д.
