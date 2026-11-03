# Разделять схемы OpenAPI для входа и выхода или нет { #separate-openapi-schemas-for-input-and-output-or-not }

С момента выхода **Pydantic v2** сгенерированный OpenAPI становится чуть более точным и **корректным**, чем раньше. 😎

На самом деле, в некоторых случаях в OpenAPI будет даже **две JSON-схемы** для одной и той же Pydantic‑модели: для входа и для выхода — в зависимости от наличия **значений по умолчанию**.

Посмотрим, как это работает, и как это изменить при необходимости.

## Pydantic‑модели для входа и выхода { #pydantic-models-for-input-and-output }

Предположим, у вас есть Pydantic‑модель со значениями по умолчанию, как здесь:

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
```

### Модель для входа { #model-for-input }

Если использовать эту модель как входную, как здесь:

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None

app = FastAPI()

@app.post("/items/")
def create_item(item: Item):
    return item
```

…то поле `description` **не будет обязательным**, потому что у него значение по умолчанию `None`.

### Входная модель в документации { #input-model-in-docs }

В документации это видно: у поля `description` нет **красной звёздочки** — оно не отмечено как обязательное:

### Модель для выхода { #model-for-output }

Но если использовать ту же модель как выходную, как здесь:

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None

app = FastAPI()

@app.post("/items/")
def create_item(item: Item):
    return item

@app.get("/items/")
def read_items() -> list[Item]:
    return [
        Item(
            name="Portal Gun",
            description="Device to travel through the multi-rick-verse",
        ),
        Item(name="Plumbus"),
    ]
```

…то, поскольку у `description` есть значение по умолчанию, если вы **ничего не вернёте** для этого поля, оно всё равно будет иметь это **значение по умолчанию**.

### Модель для данных ответа { #model-for-output-response-data }

Если поработать с интерактивной документацией и посмотреть ответ, то, хотя код ничего не добавил в одно из полей `description`, JSON‑ответ содержит значение по умолчанию (`null`):

Это означает, что у него **всегда будет какое‑то значение**, просто иногда это значение может быть `None` (или `null` в JSON).

Это означает, что клиентам, использующим ваш API, не нужно проверять, существует ли это значение или нет: они могут **исходить из того, что поле всегда присутствует**, но в некоторых случаях оно будет иметь значение по умолчанию `None`.

В OpenAPI это описывается тем, что поле помечается как **обязательное**, поскольку оно всегда присутствует.

Из‑за этого JSON Schema для модели может отличаться в зависимости от использования для **входа** или **выхода**:

* для **входа** `description` **не будет обязательным**
* для **выхода** оно будет **обязательным** (и при этом может быть `None`, или, в терминах JSON, `null`)

### Выходная модель в документации { #model-for-output-in-docs }

В документации это тоже видно, что **оба**: `name` и `description`, помечены **красной звёздочкой** как **обязательные**:

### Модели для входа и выхода в документации { #model-for-input-and-output-in-docs }

Если посмотреть все доступные схемы (JSON Schema) в OpenAPI, вы увидите две: `Item-Input` и `Item-Output`.

Для `Item-Input` поле `description` **не является обязательным** — красной звёздочки нет.

А для `Item-Output` `description` **обязательно** — красная звёздочка есть.

Благодаря этой возможности **Pydantic v2** документация вашего API становится более **точной**; если у вас есть сгенерированные клиенты и SDK, они тоже будут точнее, с лучшим **удобством для разработчиков** и большей консистентностью. 🎉

## Не разделять схемы { #do-not-separate-schemas }

Однако бывают случаи, когда вы хотите иметь **одну и ту же схему для входа и выхода**.

Главный сценарий — когда у вас уже есть сгенерированный клиентский код/SDK, и вы пока не хотите обновлять весь этот автогенерируемый клиентский код/SDK, вероятно, вы захотите сделать это в какой-то момент, но, возможно, не прямо сейчас.

В таком случае вы можете отключить эту функциональность в **FastAPI** с помощью параметра `separate_input_output_schemas=False`.

**Примечание:**

Поддержка `separate_input_output_schemas` появилась в FastAPI `0.102.0`. 🤓

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None

app = FastAPI(separate_input_output_schemas=False)

@app.post("/items/")
def create_item(item: Item):
    return item

@app.get("/items/")
def read_items() -> list[Item]:
    return [
        Item(
            name="Portal Gun",
            description="Device to travel through the multi-rick-verse",
        ),
        Item(name="Plumbus"),
    ]
```

### Одна и та же схема для входной и выходной моделей в документации { #same-schema-for-input-and-output-models-in-docs }

И теперь для модели будет одна общая схема и для входа, и для выхода — только `Item`, и в ней `description` будет **не обязательным**:
