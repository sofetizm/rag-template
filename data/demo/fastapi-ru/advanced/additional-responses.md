# Дополнительные ответы в OpenAPI { #additional-responses-in-openapi }

**Предупреждение:**

Это довольно продвинутая тема.

Если вы только начинаете работать с **FastAPI**, возможно, вам это пока не нужно.

Вы можете объявлять дополнительные ответы с дополнительными статус-кодами, типами содержимого, описаниями и т.д.

Эти дополнительные ответы будут включены в схему OpenAPI, и поэтому появятся в документации API.

Но для таких дополнительных ответов убедитесь, что вы возвращаете `Response`, например `JSONResponse`, напрямую, со своим статус-кодом и содержимым.

## Дополнительный ответ с `model` { #additional-response-with-model }

Вы можете передать вашим *декораторам операций пути* параметр `responses`.

Он принимает `dict`: ключи — это статус-коды для каждого ответа (например, `200`), а значения — другие `dict` с информацией для каждого из них.

Каждый из этих `dict` для ответа может иметь ключ `model`, содержащий Pydantic-модель, аналогично `response_model`.

**FastAPI** возьмёт эту модель, сгенерирует для неё JSON‑схему и включит её в нужное место в OpenAPI.

Например, чтобы объявить ещё один ответ со статус-кодом `404` и Pydantic-моделью `Message`, можно написать:

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

class Item(BaseModel):
    id: str
    value: str

class Message(BaseModel):
    message: str

app = FastAPI()

@app.get("/items/{item_id}", response_model=Item, responses={404: {"model": Message}})
async def read_item(item_id: str):
    if item_id == "foo":
        return {"id": "foo", "value": "there goes my hero"}
    return JSONResponse(status_code=404, content={"message": "Item not found"})
```

**Примечание:**

Имейте в виду, что необходимо возвращать `JSONResponse` напрямую.

**Примечание:**

Ключ `model` не является частью OpenAPI.

**FastAPI** возьмёт Pydantic-модель оттуда, сгенерирует JSON‑схему и поместит её в нужное место.

Нужное место:

* В ключе `content`, значением которого является другой JSON‑объект (`dict`), содержащий:
    * Ключ с типом содержимого, например `application/json`, значением которого является другой JSON‑объект, содержащий:
        * Ключ `schema`, значением которого является JSON‑схема из модели — вот нужное место.
            * **FastAPI** добавляет здесь ссылку на глобальные JSON‑схемы в другом месте вашего OpenAPI вместо того, чтобы включать схему напрямую. Так другие приложения и клиенты смогут использовать эти JSON‑схемы напрямую, предоставлять лучшие инструменты генерации кода и т.д.

Сгенерированные в OpenAPI ответы для этой *операции пути* будут такими:

```json
{
    "responses": {
        "404": {
            "description": "Additional Response",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/Message"
                    }
                }
            }
        },
        "200": {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/Item"
                    }
                }
            }
        },
        "422": {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/HTTPValidationError"
                    }
                }
            }
        }
    }
}
```

Схемы даны как ссылки на другое место внутри схемы OpenAPI:

```json
{
    "components": {
        "schemas": {
            "Message": {
                "title": "Message",
                "required": [
                    "message"
                ],
                "type": "object",
                "properties": {
                    "message": {
                        "title": "Message",
                        "type": "string"
                    }
                }
            },
            "Item": {
                "title": "Item",
                "required": [
                    "id",
                    "value"
                ],
                "type": "object",
                "properties": {
                    "id": {
                        "title": "Id",
                        "type": "string"
                    },
                    "value": {
                        "title": "Value",
                        "type": "string"
                    }
                }
            },
            "ValidationError": {
                "title": "ValidationError",
                "required": [
                    "loc",
                    "msg",
                    "type"
                ],
                "type": "object",
                "properties": {
                    "loc": {
                        "title": "Location",
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },
                    "msg": {
                        "title": "Message",
                        "type": "string"
                    },
                    "type": {
                        "title": "Error Type",
                        "type": "string"
                    }
                }
            },
            "HTTPValidationError": {
                "title": "HTTPValidationError",
                "type": "object",
                "properties": {
                    "detail": {
                        "title": "Detail",
                        "type": "array",
                        "items": {
                            "$ref": "#/components/schemas/ValidationError"
                        }
                    }
                }
            }
        }
    }
}
```

## Дополнительные типы содержимого для основного ответа { #additional-media-types-for-the-main-response }

Вы можете использовать этот же параметр `responses`, чтобы добавить разные типы содержимого для того же основного ответа.

Например, вы можете добавить дополнительный тип содержимого `image/png`, объявив, что ваша *операция пути* может возвращать JSON‑объект (с типом содержимого `application/json`) или PNG‑изображение:

```python
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

class Item(BaseModel):
    id: str
    value: str

app = FastAPI()

@app.get(
    "/items/{item_id}",
    response_model=Item,
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "Return the JSON item or an image.",
        }
    },
)
async def read_item(item_id: str, img: bool | None = None):
    if img:
        return FileResponse("image.png", media_type="image/png")
    else:
        return {"id": "foo", "value": "there goes my hero"}
```

**Примечание:**

Учтите, что изображение нужно возвращать напрямую, используя `FileResponse`.

**Примечание:**

Если вы явно не укажете другой тип содержимого в параметре `responses`, FastAPI будет считать, что ответ имеет тот же тип содержимого, что и основной класс ответа (по умолчанию `application/json`).

Но если вы указали пользовательский класс ответа с `None` в качестве его типа содержимого, FastAPI использует `application/json` для любого дополнительного ответа, у которого есть связанная модель.

## Комбинирование информации { #combining-information }

Вы также можете комбинировать информацию об ответах из нескольких мест, включая параметры `response_model`, `status_code` и `responses`.

Вы можете объявить `response_model`, используя статус-код по умолчанию `200` (или свой, если нужно), а затем объявить дополнительную информацию для этого же ответа в `responses`, напрямую в схеме OpenAPI.

**FastAPI** сохранит дополнительную информацию из `responses` и объединит её с JSON‑схемой из вашей модели.

Например, вы можете объявить ответ со статус-кодом `404`, который использует Pydantic-модель и имеет пользовательское `description`.

А также ответ со статус-кодом `200`, который использует ваш `response_model`, но включает пользовательский `example`:

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

class Item(BaseModel):
    id: str
    value: str

class Message(BaseModel):
    message: str

app = FastAPI()

@app.get(
    "/items/{item_id}",
    response_model=Item,
    responses={
        404: {"model": Message, "description": "The item was not found"},
        200: {
            "description": "Item requested by ID",
            "content": {
                "application/json": {
                    "example": {"id": "bar", "value": "The bar tenders"}
                }
            },
        },
    },
)
async def read_item(item_id: str):
    if item_id == "foo":
        return {"id": "foo", "value": "there goes my hero"}
    else:
        return JSONResponse(status_code=404, content={"message": "Item not found"})
```

Всё это будет объединено и включено в ваш OpenAPI и отображено в документации API:

## Комбинирование предопределённых и пользовательских ответов { #combine-predefined-responses-and-custom-ones }

Возможно, вы хотите иметь некоторые предопределённые ответы, применимые ко многим *операциям пути*, но при этом комбинировать их с пользовательскими ответами, необходимыми для каждой конкретной *операции пути*.

В таких случаях вы можете использовать приём Python «распаковки» `dict` с помощью `**dict_to_unpack`:

```python
old_dict = {
    "old key": "old value",
    "second old key": "second old value",
}
new_dict = {**old_dict, "new key": "new value"}
```

Здесь `new_dict` будет содержать все пары ключ-значение из `old_dict` плюс новую пару ключ-значение:

```python
{
    "old key": "old value",
    "second old key": "second old value",
    "new key": "new value",
}
```

Вы можете использовать этот приём, чтобы переиспользовать некоторые предопределённые ответы в ваших *операциях пути* и комбинировать их с дополнительными пользовательскими.

Например:

```python
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

class Item(BaseModel):
    id: str
    value: str

responses = {
    404: {"description": "Item not found"},
    302: {"description": "The item was moved"},
    403: {"description": "Not enough privileges"},
}

app = FastAPI()

@app.get(
    "/items/{item_id}",
    response_model=Item,
    responses={**responses, 200: {"content": {"image/png": {}}}},
)
async def read_item(item_id: str, img: bool | None = None):
    if img:
        return FileResponse("image.png", media_type="image/png")
    else:
        return {"id": "foo", "value": "there goes my hero"}
```

## Дополнительная информация об ответах OpenAPI { #more-information-about-openapi-responses }

Чтобы увидеть, что именно можно включать в ответы, посмотрите эти разделы спецификации OpenAPI:

* [Объект Responses OpenAPI](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#responses-object), он включает `Response Object`.
* [Объект Response OpenAPI](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#response-object), вы можете включить всё из этого объекта напрямую в каждый ответ внутри вашего параметра `responses`. Включая `description`, `headers`, `content` (внутри него вы объявляете разные типы содержимого и JSON‑схемы) и `links`.
