# Расширение OpenAPI { #extending-openapi }

Иногда может понадобиться изменить сгенерированную схему OpenAPI.

В этом разделе показано, как это сделать.

## Обычный процесс { #the-normal-process }

Обычный (по умолчанию) процесс выглядит так.

Приложение `FastAPI` (экземпляр) имеет метод `.openapi()`, который должен возвращать схему OpenAPI.

В процессе создания объекта приложения регистрируется *операция пути* (обработчик пути) для `/openapi.json` (или для того, что указано в вашем `openapi_url`).

Она просто возвращает JSON-ответ с результатом вызова метода приложения `.openapi()`.

По умолчанию метод `.openapi()` проверяет свойство `.openapi_schema`: если в нём уже есть данные, возвращает их.

Если нет — генерирует схему с помощью вспомогательной функции `fastapi.openapi.utils.get_openapi`.

Функция `get_openapi()` принимает параметры:

* `title`: Заголовок OpenAPI, отображается в документации.
* `version`: Версия вашего API, например `2.5.0`.
* `openapi_version`: Версия используемой спецификации OpenAPI. По умолчанию — последняя: `3.1.0`.
* `summary`: Краткое описание API.
* `description`: Описание вашего API; может включать Markdown и будет отображаться в документации.
* `routes`: Список маршрутов — это каждая зарегистрированная *операция пути*. Берутся из `app.routes`. FastAPI использует их, чтобы собрать зарегистрированные *операции пути*, включая те из подключённых роутеров.

**Технические детали:**

`app.routes` — это более низкоуровневое дерево маршрутов. Оно может включать кандидаты маршрутов, которые FastAPI использует внутренне для подключённых роутеров, а не только конечные объекты `APIRoute`.

Вы всё равно можете передать `app.routes` в `get_openapi()`. FastAPI обойдёт это дерево маршрутов, чтобы собрать фактические операции пути.

**Примечание:**

Параметр `summary` доступен в OpenAPI 3.1.0 и выше, поддерживается FastAPI 0.99.0 и выше.

## Переопределение значений по умолчанию { #overriding-the-defaults }

Используя информацию выше, вы можете той же вспомогательной функцией сгенерировать схему OpenAPI и переопределить любые нужные части.

Например, добавим [расширение OpenAPI ReDoc для включения собственного логотипа](https://github.com/Redocly/redoc/blob/main/docs/redoc-vendor-extensions.md#x-logo).

### Обычный **FastAPI** { #normal-fastapi }

Сначала напишите приложение **FastAPI** как обычно:

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI()

@app.get("/items/")
async def read_items():
    return [{"name": "Foo"}]

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Custom title",
        version="2.5.0",
        summary="This is a very custom OpenAPI schema",
        description="Here's a longer description of the custom **OpenAPI** schema",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### Сгенерируйте схему OpenAPI { #generate-the-openapi-schema }

Затем используйте ту же вспомогательную функцию для генерации схемы OpenAPI внутри функции `custom_openapi()`:

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI()

@app.get("/items/")
async def read_items():
    return [{"name": "Foo"}]

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Custom title",
        version="2.5.0",
        summary="This is a very custom OpenAPI schema",
        description="Here's a longer description of the custom **OpenAPI** schema",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### Измените схему OpenAPI { #modify-the-openapi-schema }

Теперь можно добавить расширение ReDoc, добавив кастомный `x-logo` в «объект» `info` в схеме OpenAPI:

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI()

@app.get("/items/")
async def read_items():
    return [{"name": "Foo"}]

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Custom title",
        version="2.5.0",
        summary="This is a very custom OpenAPI schema",
        description="Here's a longer description of the custom **OpenAPI** schema",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### Кэшируйте схему OpenAPI { #cache-the-openapi-schema }

Вы можете использовать свойство `.openapi_schema` как «кэш» для хранения сгенерированной схемы.

Так приложению не придётся генерировать схему каждый раз, когда пользователь открывает документацию API.

Она будет создана один раз, а затем тот же кэшированный вариант будет использоваться для последующих запросов.

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI()

@app.get("/items/")
async def read_items():
    return [{"name": "Foo"}]

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Custom title",
        version="2.5.0",
        summary="This is a very custom OpenAPI schema",
        description="Here's a longer description of the custom **OpenAPI** schema",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### Переопределите метод { #override-the-method }

Теперь вы можете заменить метод `.openapi()` на вашу новую функцию.

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI()

@app.get("/items/")
async def read_items():
    return [{"name": "Foo"}]

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Custom title",
        version="2.5.0",
        summary="This is a very custom OpenAPI schema",
        description="Here's a longer description of the custom **OpenAPI** schema",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### Проверьте { #check-it }

Перейдите на [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) — вы увидите, что используется ваш кастомный логотип (в этом примере — логотип **FastAPI**):
