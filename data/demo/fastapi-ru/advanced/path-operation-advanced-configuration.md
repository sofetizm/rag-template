# Расширенная конфигурация операций пути { #path-operation-advanced-configuration }

## OpenAPI operationId { #openapi-operationid }

**Предупреждение:**

Если вы не «эксперт» по OpenAPI, скорее всего, это вам не нужно.

Вы можете задать OpenAPI `operationId`, который будет использоваться в вашей *операции пути*, с помощью параметра `operation_id`.

Нужно убедиться, что он уникален для каждой операции.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/", operation_id="some_specific_id_you_define")
async def read_items():
    return [{"item_id": "Foo"}]
```

### Использование имени *функции-обработчика пути* как operationId { #using-the-path-operation-function-name-as-the-operationid }

Если вы хотите использовать имена функций ваших API в качестве `operationId`, вы можете передать пользовательскую `generate_unique_id_function` в `FastAPI`.

Эта функция получает каждый `APIRoute` и возвращает `operationId`, который нужно использовать для этой операции пути.

```python
from fastapi import FastAPI
from fastapi.routing import APIRoute

def custom_generate_unique_id(route: APIRoute) -> str:
    return route.name

app = FastAPI(generate_unique_id_function=custom_generate_unique_id)

@app.get("/items/")
async def read_items():
    return [{"item_id": "Foo"}]
```

**Предупреждение:**

Если вы делаете это, убедитесь, что каждая из ваших *функций-обработчиков пути* имеет уникальное имя.

Даже если они находятся в разных модулях (файлах Python).

## Исключить из OpenAPI { #exclude-from-openapi }

Чтобы исключить *операцию пути* из генерируемой схемы OpenAPI (а значит, и из автоматических систем документации), используйте параметр `include_in_schema` и установите его в `False`:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/", include_in_schema=False)
async def read_items():
    return [{"item_id": "Foo"}]
```

## Расширенное описание из docstring { #advanced-description-from-docstring }

Вы можете ограничить количество строк из docstring *функции-обработчика пути*, используемых для OpenAPI.

Добавление `\f` (экранированного символа «form feed») заставит **FastAPI** обрезать текст, используемый для OpenAPI, в этой точке.

Это не отобразится в документации, но другие инструменты (например, Sphinx) смогут использовать остальное.

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
    \f
    :param item: User input.
    """
    return item
```

## Дополнительные ответы { #additional-responses }

Вы, вероятно, уже видели, как объявлять `response_model` и `status_code` для *операции пути*.

Это определяет метаданные об основном HTTP-ответе *операции пути*.

Также можно объявлять дополнительные ответы с их моделями, статус-кодами и т.д.

В документации есть целая глава об этом — [Дополнительные ответы в OpenAPI](additional-responses.md).

## Дополнительные данные OpenAPI { #openapi-extra }

Когда вы объявляете *операцию пути* в своём приложении, **FastAPI** автоматически генерирует соответствующие метаданные об этой *операции пути* для включения в схему OpenAPI.

**Технические детали:**

В спецификации OpenAPI это называется [Объект операции](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#operation-object).

Он содержит всю информацию об *операции пути* и используется для генерации автоматической документации.

Там есть `tags`, `parameters`, `requestBody`, `responses` и т.д.

Эта специфичная для *операции пути* схема OpenAPI обычно генерируется автоматически **FastAPI**, но вы также можете её расширить.

**Совет:**

Это низкоуровневая возможность расширения.

Если вам нужно лишь объявить дополнительные ответы, удобнее сделать это через [Дополнительные ответы в OpenAPI](additional-responses.md).

Вы можете расширить схему OpenAPI для *операции пути* с помощью параметра `openapi_extra`.

### Расширения OpenAPI { #openapi-extensions }

`openapi_extra` может пригодиться, например, чтобы объявить [Расширения OpenAPI](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#specificationExtensions):

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/", openapi_extra={"x-aperture-labs-portal": "blue"})
async def read_items():
    return [{"item_id": "portal-gun"}]
```

Если вы откроете автоматическую документацию API, ваше расширение появится внизу страницы конкретной *операции пути*.

И если вы посмотрите на итоговый OpenAPI (по адресу `/openapi.json` вашего API), вы также увидите своё расширение в составе описания соответствующей *операции пути*:

```json
{
    "openapi": "3.1.0",
    "info": {
        "title": "FastAPI",
        "version": "0.1.0"
    },
    "paths": {
        "/items/": {
            "get": {
                "summary": "Read Items",
                "operationId": "read_items_items__get",
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {}
                            }
                        }
                    }
                },
                "x-aperture-labs-portal": "blue"
            }
        }
    }
}
```

### Пользовательская схема OpenAPI для *операции пути* { #custom-openapi-path-operation-schema }

Словарь в `openapi_extra` будет глубоко объединён с автоматически сгенерированной схемой OpenAPI для *операции пути*.

Таким образом, вы можете добавить дополнительные данные к автоматически сгенерированной схеме.

Например, вы можете решить читать и валидировать HTTP-запрос своим кодом, не используя автоматические возможности FastAPI и Pydantic, но при этом захотите описать HTTP-запрос в схеме OpenAPI.

Это можно сделать с помощью `openapi_extra`:

```python
from fastapi import FastAPI, Request

app = FastAPI()

def magic_data_reader(raw_body: bytes):
    return {
        "size": len(raw_body),
        "content": {
            "name": "Maaaagic",
            "price": 42,
            "description": "Just kiddin', no magic here. ✨",
        },
    }

@app.post(
    "/items/",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "required": ["name", "price"],
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "price": {"type": "number"},
                            "description": {"type": "string"},
                        },
                    }
                }
            },
            "required": True,
        },
    },
)
async def create_item(request: Request):
    raw_body = await request.body()
    data = magic_data_reader(raw_body)
    return data
```

В этом примере мы не объявляли никакую Pydantic-модель. Фактически тело запроса даже не распарсено как JSON, оно читается напрямую как `bytes`, а функция `magic_data_reader()` будет отвечать за его парсинг каким-то способом.

Тем не менее, мы можем объявить ожидаемую схему для тела запроса.

### Пользовательский тип содержимого в OpenAPI { #custom-openapi-content-type }

Используя тот же приём, вы можете воспользоваться Pydantic-моделью, чтобы определить JSON Schema, которая затем будет включена в пользовательский раздел схемы OpenAPI для *операции пути*.

И вы можете сделать это, даже если тип данных в HTTP-запросе — не JSON.

Например, в этом приложении мы не используем встроенную функциональность FastAPI для извлечения JSON Schema из моделей Pydantic, равно как и автоматическую валидацию JSON. Мы объявляем тип содержимого HTTP-запроса как YAML, а не JSON:

```python
import yaml
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ValidationError

app = FastAPI()

class Item(BaseModel):
    name: str
    tags: list[str]

@app.post(
    "/items/",
    openapi_extra={
        "requestBody": {
            "content": {"application/x-yaml": {"schema": Item.model_json_schema()}},
            "required": True,
        },
    },
)
async def create_item(request: Request):
    raw_body = await request.body()
    try:
        data = yaml.safe_load(raw_body)
    except yaml.YAMLError:
        raise HTTPException(status_code=422, detail="Invalid YAML")
    try:
        item = Item.model_validate(data)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors(include_url=False))
    return item
```

Тем не менее, хотя мы не используем встроенную функциональность по умолчанию, мы всё равно используем Pydantic-модель, чтобы вручную сгенерировать JSON Schema для данных, которые мы хотим получить в YAML.

Затем мы работаем с HTTP-запросом напрямую и извлекаем тело как `bytes`. Это означает, что FastAPI даже не попытается распарсить полезную нагрузку HTTP-запроса как JSON.

А затем в нашем коде мы напрямую парсим это содержимое YAML и снова используем ту же Pydantic-модель, чтобы валидировать YAML-содержимое:

```python
import yaml
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ValidationError

app = FastAPI()

class Item(BaseModel):
    name: str
    tags: list[str]

@app.post(
    "/items/",
    openapi_extra={
        "requestBody": {
            "content": {"application/x-yaml": {"schema": Item.model_json_schema()}},
            "required": True,
        },
    },
)
async def create_item(request: Request):
    raw_body = await request.body()
    try:
        data = yaml.safe_load(raw_body)
    except yaml.YAMLError:
        raise HTTPException(status_code=422, detail="Invalid YAML")
    try:
        item = Item.model_validate(data)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors(include_url=False))
    return item
```

**Совет:**

Здесь мы переиспользуем ту же Pydantic-модель.

Но аналогично мы могли бы валидировать данные и каким-то другим способом.
