# Тело запроса - Поля { #body-fields }

Таким же способом, как вы объявляете дополнительную валидацию и метаданные в параметрах *функции обработки пути* с помощью функций `Query`, `Path` и `Body`, вы можете объявлять валидацию и метаданные внутри Pydantic моделей, используя функцию `Field` из Pydantic.

## Импорт `Field` { #import-field }

Сначала вы должны импортировать его:

```python
from typing import Annotated

from fastapi import Body, FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str | None = Field(
        default=None, title="The description of the item", max_length=300
    )
    price: float = Field(gt=0, description="The price must be greater than zero")
    tax: float | None = None

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Annotated[Item, Body(embed=True)]):
    results = {"item_id": item_id, "item": item}
    return results
```

**Внимание:**

Обратите внимание, что функция `Field` импортируется непосредственно из `pydantic`, а не из `fastapi`, как все остальные функции (`Query`, `Path`, `Body` и т.д.).

## Объявление атрибутов модели { #declare-model-attributes }

Вы можете использовать функцию `Field` с атрибутами модели:

```python
from typing import Annotated

from fastapi import Body, FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str | None = Field(
        default=None, title="The description of the item", max_length=300
    )
    price: float = Field(gt=0, description="The price must be greater than zero")
    tax: float | None = None

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Annotated[Item, Body(embed=True)]):
    results = {"item_id": item_id, "item": item}
    return results
```

Функция `Field` работает так же, как `Query`, `Path` и `Body`, у неё такие же параметры и т.д.

**Технические детали:**

На самом деле, `Query`, `Path` и другие функции, которые вы увидите в дальнейшем, создают объекты подклассов общего класса `Param`, который сам по себе является подклассом `FieldInfo` из Pydantic.

И `Field` (из Pydantic) также возвращает экземпляр `FieldInfo`.

`Body` также напрямую возвращает объекты подкласса `FieldInfo`. И есть и другие, с которыми вы познакомитесь позже, которые являются подклассами класса `Body`.

Помните, что когда вы импортируете `Query`, `Path` и другое из `fastapi`, это фактически функции, которые возвращают специальные классы.

**Подсказка:**

Обратите внимание, что каждый атрибут модели с типом, значением по умолчанию и `Field` имеет ту же структуру, что и параметр *функции обработки пути* с `Field` вместо `Path`, `Query` и `Body`.

## Добавление дополнительной информации { #add-extra-information }

Вы можете объявлять дополнительную информацию с помощью `json_schema_extra` в `Field`, `Query`, `Body` и т.п. Она будет включена в сгенерированную JSON схему.

Вы узнаете больше о добавлении дополнительной информации позже в документации, когда будете изучать, как задавать примеры.

**Внимание:**

Дополнительные ключи, переданные в `json_schema_extra`, также будут присутствовать в сгенерированной OpenAPI схеме вашего приложения.
Поскольку эти ключи могут не входить в спецификацию OpenAPI, некоторые инструменты OpenAPI, например, [валидатор OpenAPI](https://validator.swagger.io/), могут не работать с вашей сгенерированной схемой.

## Резюме { #recap }

Вы можете использовать функцию `Field` из Pydantic, чтобы задавать дополнительную валидацию и метаданные для атрибутов модели.

Вы также можете использовать `json_schema_extra`, чтобы передать дополнительные метаданные JSON схемы.
