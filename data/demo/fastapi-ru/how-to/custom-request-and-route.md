# Пользовательские классы Request и APIRoute { #custom-request-and-apiroute-class }

В некоторых случаях может понадобиться переопределить логику, используемую классами `Request` и `APIRoute`.

В частности, это может быть хорошей альтернативой логике в middleware.

Например, если вы хотите прочитать или изменить тело запроса до того, как оно будет обработано вашим приложением.

**Опасность:**

Это «продвинутая» возможность.

Если вы только начинаете работать с **FastAPI**, возможно, стоит пропустить этот раздел.

## Сценарии использования { #use-cases }

Некоторые сценарии:

* Преобразование тел запросов не в формате JSON в JSON (например, [`msgpack`](https://msgpack.org/index.html)).
* Распаковка тел запросов, сжатых с помощью gzip.
* Автоматическое логирование всех тел запросов.

## Обработка пользовательского кодирования тела запроса { #handling-custom-request-body-encodings }

Посмотрим, как использовать пользовательский подкласс `Request` для распаковки gzip-запросов.

И подкласс `APIRoute`, чтобы использовать этот пользовательский класс запроса.

### Создать пользовательский класс `GzipRequest` { #create-a-custom-gziprequest-class }

**Совет:**

Это учебный пример, демонстрирующий принцип работы. Если вам нужна поддержка Gzip, вы можете использовать готовый [`GzipMiddleware`](../advanced/middleware.md#gzipmiddleware).

Сначала создадим класс `GzipRequest`, который переопределит метод `Request.body()` и распакует тело запроса при наличии соответствующего HTTP-заголовка.

Если в HTTP-заголовке нет `gzip`, он не будет пытаться распаковывать тело.

Таким образом, один и тот же класс маршрута сможет обрабатывать как gzip-сжатые, так и несжатые HTTP-запросы.

```python
import gzip
from collections.abc import Callable
from typing import Annotated

from fastapi import Body, FastAPI, Request, Response
from fastapi.routing import APIRoute

class GzipRequest(Request):
    async def body(self) -> bytes:
        if not hasattr(self, "_body"):
            body = await super().body()
            if "gzip" in self.headers.getlist("Content-Encoding"):
                body = gzip.decompress(body)
            self._body = body
        return self._body

class GzipRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            request = GzipRequest(request.scope, request.receive)
            return await original_route_handler(request)

        return custom_route_handler

app = FastAPI()
app.router.route_class = GzipRoute

@app.post("/sum")
async def sum_numbers(numbers: Annotated[list[int], Body()]):
    return {"sum": sum(numbers)}
```

### Создать пользовательский класс `GzipRoute` { #create-a-custom-gziproute-class }

Далее создадим пользовательский подкласс `fastapi.routing.APIRoute`, который будет использовать `GzipRequest`.

На этот раз он переопределит метод `APIRoute.get_route_handler()`.

Этот метод возвращает функцию. Именно эта функция получает HTTP-запрос и возвращает HTTP-ответ.

Здесь мы используем её, чтобы создать `GzipRequest` из исходного HTTP-запроса.

```python
import gzip
from collections.abc import Callable
from typing import Annotated

from fastapi import Body, FastAPI, Request, Response
from fastapi.routing import APIRoute

class GzipRequest(Request):
    async def body(self) -> bytes:
        if not hasattr(self, "_body"):
            body = await super().body()
            if "gzip" in self.headers.getlist("Content-Encoding"):
                body = gzip.decompress(body)
            self._body = body
        return self._body

class GzipRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            request = GzipRequest(request.scope, request.receive)
            return await original_route_handler(request)

        return custom_route_handler

app = FastAPI()
app.router.route_class = GzipRoute

@app.post("/sum")
async def sum_numbers(numbers: Annotated[list[int], Body()]):
    return {"sum": sum(numbers)}
```

**Технические детали:**

У `Request` есть атрибут `request.scope` — это просто Python-`dict`, содержащий метаданные, связанные с HTTP-запросом.

У `Request` также есть `request.receive` — функция для «получения» тела запроса.

И `dict` `scope`, и функция `receive` являются частью спецификации ASGI.

Именно этих двух компонентов — `scope` и `receive` — достаточно, чтобы создать новый экземпляр `Request`.

Чтобы узнать больше о `Request`, см. [документацию Starlette о запросах](https://starlette.dev/requests/).

Единственное, что делает по-другому функция, возвращённая `GzipRequest.get_route_handler`, — преобразует `Request` в `GzipRequest`.

Благодаря этому наш `GzipRequest` позаботится о распаковке данных (при необходимости) до передачи их в наши *операции пути*.

Дальше вся логика обработки остаётся прежней.

Но благодаря изменениям в `GzipRequest.body` тело запроса будет автоматически распаковано при необходимости, когда оно будет загружено **FastAPI**.

## Доступ к телу запроса в обработчике исключений { #accessing-the-request-body-in-an-exception-handler }

**Совет:**

Для решения этой задачи, вероятно, намного проще использовать `body` в пользовательском обработчике `RequestValidationError` ([Обработка ошибок](../tutorial/handling-errors.md#use-the-requestvalidationerror-body)).

Но этот пример всё равно актуален и показывает, как взаимодействовать с внутренними компонентами.

Тем же подходом можно воспользоваться, чтобы получить доступ к телу запроса в обработчике исключений.

Нужно лишь обработать HTTP-запрос внутри блока `try`/`except`:

```python
from collections.abc import Callable
from typing import Annotated

from fastapi import Body, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute

class ValidationErrorLoggingRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                return await original_route_handler(request)
            except RequestValidationError as exc:
                body = await request.body()
                detail = {"errors": exc.errors(), "body": body.decode()}
                raise HTTPException(status_code=422, detail=detail)

        return custom_route_handler

app = FastAPI()
app.router.route_class = ValidationErrorLoggingRoute

@app.post("/")
async def sum_numbers(numbers: Annotated[list[int], Body()]):
    return sum(numbers)
```

Если произойдёт исключение, экземпляр `Request` всё ещё будет в области видимости, поэтому мы сможем прочитать тело запроса и использовать его при обработке ошибки:

```python
from collections.abc import Callable
from typing import Annotated

from fastapi import Body, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute

class ValidationErrorLoggingRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                return await original_route_handler(request)
            except RequestValidationError as exc:
                body = await request.body()
                detail = {"errors": exc.errors(), "body": body.decode()}
                raise HTTPException(status_code=422, detail=detail)

        return custom_route_handler

app = FastAPI()
app.router.route_class = ValidationErrorLoggingRoute

@app.post("/")
async def sum_numbers(numbers: Annotated[list[int], Body()]):
    return sum(numbers)
```

## Пользовательский класс `APIRoute` в роутере { #custom-apiroute-class-in-a-router }

Вы также можете задать параметр `route_class` у `APIRouter`:

```python
import time
from collections.abc import Callable

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.routing import APIRoute

class TimedRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            before = time.time()
            response: Response = await original_route_handler(request)
            duration = time.time() - before
            response.headers["X-Response-Time"] = str(duration)
            print(f"route duration: {duration}")
            print(f"route response: {response}")
            print(f"route response headers: {response.headers}")
            return response

        return custom_route_handler

app = FastAPI()
router = APIRouter(route_class=TimedRoute)

@app.get("/")
async def not_timed():
    return {"message": "Not timed"}

@router.get("/timed")
async def timed():
    return {"message": "It's the time of my life"}

app.include_router(router)
```

В этом примере *операции пути*, объявленные в `router`, будут использовать пользовательский класс `TimedRoute` и получат дополнительный HTTP-заголовок `X-Response-Time` в HTTP-ответе с временем, затраченным на формирование HTTP-ответа:

```python
import time
from collections.abc import Callable

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.routing import APIRoute

class TimedRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            before = time.time()
            response: Response = await original_route_handler(request)
            duration = time.time() - before
            response.headers["X-Response-Time"] = str(duration)
            print(f"route duration: {duration}")
            print(f"route response: {response}")
            print(f"route response headers: {response.headers}")
            return response

        return custom_route_handler

app = FastAPI()
router = APIRouter(route_class=TimedRoute)

@app.get("/")
async def not_timed():
    return {"message": "Not timed"}

@router.get("/timed")
async def timed():
    return {"message": "It's the time of my life"}

app.include_router(router)
```
