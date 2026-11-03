# Обработка ошибок { #handling-errors }

Существует множество ситуаций, когда необходимо сообщить об ошибке клиенту, использующему ваш API.

Таким клиентом может быть браузер с фронтендом, чужой код, IoT-устройство и т.д.

Возможно, вам придется сообщить клиенту о следующем:

* Клиент не имеет достаточных привилегий для выполнения данной операции.
* Клиент не имеет доступа к данному ресурсу.
* Элемент, к которому клиент пытался получить доступ, не существует.
* и т.д.

В таких случаях обычно возвращают **HTTP статус-код** в диапазоне **400** (от 400 до 499).

Они похожи на двухсотые HTTP статус-коды (от 200 до 299). Эти статус-коды "200" означают, что в HTTP-запросе в каком-то смысле был "успех".

HTTP статус-коды в диапазоне 400 означают, что произошла ошибка со стороны клиента.

Помните все эти ошибки **"404 Not Found"** (и шутки)?

## Использование `HTTPException` { #use-httpexception }

Для возврата клиенту HTTP-ответов с ошибками используется `HTTPException`.

### Импортируйте `HTTPException` { #import-httpexception }

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

items = {"foo": "The Foo Wrestlers"}

@app.get("/items/{item_id}")
async def read_item(item_id: str):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item": items[item_id]}
```

### Вызовите `HTTPException` в своем коде { #raise-an-httpexception-in-your-code }

`HTTPException` - это обычное исключение Python с дополнительными данными, актуальными для API.

Поскольку это исключение Python, то его не `return`, а `raise`.

Это также означает, что если вы находитесь внутри вспомогательной функции, которая вызывается внутри вашей *функции-обработчика пути*, и вы вызываете `HTTPException` изнутри этой вспомогательной функции, то остальной код в *функции-обработчике пути* выполняться не будет, запрос сразу завершится, а HTTP-ошибка из `HTTPException` будет отправлена клиенту.

Преимущество вызова исключения перед возвратом значения станет более очевидным в разделе о зависимостях и безопасности.

В данном примере, когда клиент запрашивает элемент по несуществующему ID, вызовите исключение со статус-кодом `404`:

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

items = {"foo": "The Foo Wrestlers"}

@app.get("/items/{item_id}")
async def read_item(item_id: str):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item": items[item_id]}
```

### Возвращаемый ответ { #the-resulting-response }

Если клиент запросит `http://example.com/items/foo` (`item_id` `"foo"`), то он получит HTTP статус-код 200 и ответ в формате JSON:

```json
{
  "item": "The Foo Wrestlers"
}
```

Но если клиент запросит `http://example.com/items/bar` (несуществующий `item_id` `"bar"`), то он получит HTTP статус-код 404 (ошибка "не найдено") и JSON-ответ в виде:

```json
{
  "detail": "Item not found"
}
```

**Подсказка:**

При вызове `HTTPException` в качестве параметра `detail` можно передавать любое значение, которое может быть преобразовано в JSON, а не только `str`.

Вы можете передать `dict`, `list` и т.д.

Они автоматически обрабатываются **FastAPI** и преобразуются в JSON.

## Добавление пользовательских HTTP-заголовков { #add-custom-headers }

В некоторых ситуациях полезно иметь возможность добавлять пользовательские HTTP-заголовки к HTTP-ошибке. Например, для некоторых типов безопасности.

Скорее всего, вам не потребуется использовать это непосредственно в коде.

Но в случае, если это необходимо для продвинутого сценария, можно добавить пользовательские HTTP-заголовки:

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

items = {"foo": "The Foo Wrestlers"}

@app.get("/items-header/{item_id}")
async def read_item_header(item_id: str):
    if item_id not in items:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
            headers={"X-Error": "There goes my error"},
        )
    return {"item": items[item_id]}
```

## Установка пользовательских обработчиков исключений { #install-custom-exception-handlers }

Вы можете добавить пользовательские обработчики исключений с помощью [тех же утилит обработки исключений из Starlette](https://starlette.dev/exceptions/).

Допустим, у вас есть пользовательское исключение `UnicornException`, которое вы (или используемая вами библиотека) можете вызвать с помощью `raise`.

И вы хотите обрабатывать это исключение глобально с помощью FastAPI.

Можно добавить собственный обработчик исключений с помощью `@app.exception_handler()`:

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class UnicornException(Exception):
    def __init__(self, name: str):
        self.name = name

app = FastAPI()

@app.exception_handler(UnicornException)
async def unicorn_exception_handler(request: Request, exc: UnicornException):
    return JSONResponse(
        status_code=418,
        content={"message": f"Oops! {exc.name} did something. There goes a rainbow..."},
    )

@app.get("/unicorns/{name}")
async def read_unicorn(name: str):
    if name == "yolo":
        raise UnicornException(name=name)
    return {"unicorn_name": name}
```

Здесь, если запросить `/unicorns/yolo`, то *операция пути* вызовет `UnicornException`.

Но оно будет обработано `unicorn_exception_handler`.

Таким образом, вы получите чистую ошибку с HTTP статус-кодом `418` и содержимым JSON:

```json
{"message": "Oops! yolo did something. There goes a rainbow..."}
```

**Технические детали:**

Также можно использовать `from starlette.requests import Request` и `from starlette.responses import JSONResponse`.

**FastAPI** предоставляет тот же `starlette.responses`, что и `fastapi.responses`, просто для удобства разработчика. Однако большинство доступных ответов поступает непосредственно из Starlette. То же самое касается и `Request`.

## Переопределение стандартных обработчиков исключений { #override-the-default-exception-handlers }

**FastAPI** имеет некоторые обработчики исключений по умолчанию.

Эти обработчики отвечают за возврат стандартных JSON-ответов при вызове `HTTPException` с помощью `raise` и при наличии в HTTP-запросе недопустимых данных.

Вы можете переопределить эти обработчики исключений на свои собственные.

### Переопределение исключений валидации запроса { #override-request-validation-exceptions }

Когда HTTP-запрос содержит недопустимые данные, **FastAPI** внутренне вызывает `RequestValidationError`.

А также включает в себя обработчик исключений по умолчанию для него.

Чтобы переопределить его, импортируйте `RequestValidationError` и используйте его с `@app.exception_handler(RequestValidationError)`, чтобы декорировать обработчик исключений.

Обработчик исключения получит объект `Request` и исключение.

```python
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    message = "Validation errors:"
    for error in exc.errors():
        message += f"\nField: {error['loc']}, Error: {error['msg']}"
    return PlainTextResponse(message, status_code=400)

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    if item_id == 3:
        raise HTTPException(status_code=418, detail="Nope! I don't like 3.")
    return {"item_id": item_id}
```

Теперь, если перейти к `/items/foo`, то вместо стандартной JSON-ошибки с:

```json
{
    "detail": [
        {
            "loc": [
                "path",
                "item_id"
            ],
            "msg": "value is not a valid integer",
            "type": "type_error.integer"
        }
    ]
}
```

вы получите текстовую версию с:

```
Validation errors:
Field: ('path', 'item_id'), Error: Input should be a valid integer, unable to parse string as an integer
```

### Переопределите обработчик ошибок `HTTPException` { #override-the-httpexception-error-handler }

Аналогичным образом можно переопределить обработчик `HTTPException`.

Например, для этих ошибок можно вернуть обычный текстовый ответ вместо JSON:

```python
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    message = "Validation errors:"
    for error in exc.errors():
        message += f"\nField: {error['loc']}, Error: {error['msg']}"
    return PlainTextResponse(message, status_code=400)

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    if item_id == 3:
        raise HTTPException(status_code=418, detail="Nope! I don't like 3.")
    return {"item_id": item_id}
```

**Технические детали:**

Можно также использовать `from starlette.responses import PlainTextResponse`.

**FastAPI** предоставляет тот же `starlette.responses`, что и `fastapi.responses`, просто для удобства разработчика. Однако большинство доступных ответов поступает непосредственно из Starlette.

**Внимание:**

Имейте в виду, что `RequestValidationError` содержит информацию об имени файла и строке, где происходит ошибка валидации, чтобы вы могли при желании отобразить её в логах вместе с релевантной информацией.

Но это означает, что если вы просто преобразуете её в строку и вернёте эту информацию напрямую, вы можете допустить небольшую утечку информации о своей системе, поэтому здесь код извлекает и показывает каждую ошибку отдельно.

### Используйте тело `RequestValidationError` { #use-the-requestvalidationerror-body }

Ошибка `RequestValidationError` содержит `body` (тело запроса), которое она получила с недопустимыми данными.

Вы можете использовать его при разработке приложения для логирования тела запроса и его отладки, возврата пользователю и т.д.

```python
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )

class Item(BaseModel):
    title: str
    size: int

@app.post("/items/")
async def create_item(item: Item):
    return item
```

Теперь попробуйте отправить недопустимый элемент, например:

```json
{
  "title": "towel",
  "size": "XL"
}
```

Вы получите ответ о том, что данные недопустимы, содержащий полученное тело запроса:

```json
{
  "detail": [
    {
      "loc": [
        "body",
        "size"
      ],
      "msg": "value is not a valid integer",
      "type": "type_error.integer"
    }
  ],
  "body": {
    "title": "towel",
    "size": "XL"
  }
}
```

#### `HTTPException` в FastAPI и `HTTPException` в Starlette { #fastapis-httpexception-vs-starlettes-httpexception }

**FastAPI** имеет собственный `HTTPException`.

Класс ошибок **FastAPI** `HTTPException` наследует от класса ошибок Starlette `HTTPException`.

Единственное отличие состоит в том, что `HTTPException` в **FastAPI** принимает любые данные, пригодные для преобразования в JSON, в поле `detail`, тогда как `HTTPException` в Starlette принимает для него только строки.

Таким образом, вы можете продолжать вызывать `HTTPException` от **FastAPI** как обычно в своем коде.

Но когда вы регистрируете обработчик исключений, вы должны зарегистрировать его для `HTTPException` от Starlette.

Таким образом, если какая-либо часть внутреннего кода Starlette, расширение или плагин Starlette вызовет исключение Starlette `HTTPException`, ваш обработчик сможет перехватить и обработать его.

В данном примере, чтобы иметь возможность использовать оба `HTTPException` в одном коде, исключение Starlette переименовано в `StarletteHTTPException`:

```python
from starlette.exceptions import HTTPException as StarletteHTTPException
```

### Переиспользование обработчиков исключений **FastAPI** { #reuse-fastapis-exception-handlers }

Если вы хотите использовать исключение вместе с теми же обработчиками исключений по умолчанию из **FastAPI**, вы можете импортировать и повторно использовать обработчики исключений по умолчанию из `fastapi.exception_handlers`:

```python
from fastapi import FastAPI, HTTPException
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    print(f"OMG! An HTTP error!: {repr(exc)}")
    return await http_exception_handler(request, exc)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(f"OMG! The client sent invalid data!: {exc}")
    return await request_validation_exception_handler(request, exc)

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    if item_id == 3:
        raise HTTPException(status_code=418, detail="Nope! I don't like 3.")
    return {"item_id": item_id}
```

В этом примере вы просто выводите ошибку с очень выразительным сообщением, но идея вам понятна. Вы можете использовать исключение, а затем просто повторно использовать стандартные обработчики исключений.
