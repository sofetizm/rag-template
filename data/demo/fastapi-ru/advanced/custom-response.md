# Кастомные ответы — HTML, поток, файл и другие { #custom-response-html-stream-file-others }

По умолчанию **FastAPI** возвращает ответы в формате JSON.

Вы можете переопределить это, вернув `Response` напрямую, как показано в разделе [Вернуть Response напрямую](response-directly.md).

Но если вы возвращаете `Response` напрямую (или любой его подкласс, например `JSONResponse`), данные не будут автоматически преобразованы (даже если вы объявили `response_model`), и документация не будет автоматически сгенерирована (например, со специфичным «типом содержимого» в HTTP-заголовке `Content-Type` как частью сгенерированного OpenAPI).

Но вы также можете объявить `Response`, который хотите использовать (например, любой подкласс `Response`), в декораторе операции пути, указав параметр `response_class`.

Содержимое, которое вы возвращаете из своей функции-обработчика пути, будет помещено внутрь этого `Response`.

**Примечание:**

Если вы используете класс ответа без типа содержимого, FastAPI будет ожидать, что у вашего ответа нет содержимого, поэтому он не будет документировать формат ответа в сгенерированной документации OpenAPI.

## JSON-ответы { #json-responses }

По умолчанию FastAPI возвращает ответы в формате JSON.

Если вы объявите [Модель ответа](../tutorial/response-model.md), FastAPI использует её для сериализации данных в JSON с помощью Pydantic.

Если вы не объявите модель ответа, FastAPI использует `jsonable_encoder`, описанный в разделе [JSON-совместимый энкодер](../tutorial/encoder.md), и поместит результат в `JSONResponse`.

Если вы объявите `response_class` с JSON типом содержимого (`application/json`), как в случае с `JSONResponse`, данные, которые вы возвращаете, будут автоматически преобразованы (и отфильтрованы) любой Pydantic-моделью ответа (`response_model`), объявленной вами в декораторе операции пути. Но данные не будут сериализованы в JSON-байты через Pydantic; вместо этого они будут преобразованы с помощью `jsonable_encoder`, а затем переданы в класс `JSONResponse`, который сериализует их в байты, используя стандартную JSON-библиотеку Python.

### Производительность JSON { #json-performance }

Коротко: если вам нужна максимальная производительность, используйте [Модель ответа](../tutorial/response-model.md) и не объявляйте `response_class` в декораторе операции пути.

```python
@app.post("/items/")
async def create_item(item: Item) -> Item:
    return item
```

## HTML-ответ { #html-response }

Чтобы вернуть ответ с HTML напрямую из **FastAPI**, используйте `HTMLResponse`.

- Импортируйте `HTMLResponse`.
- Передайте `HTMLResponse` в параметр `response_class` вашего декоратора операции пути.

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/items/", response_class=HTMLResponse)
async def read_items():
    return """
    <html>
        <head>
            <title>Some HTML in here</title>
        </head>
        
            <h1>Look ma! HTML!</h1>
        
    </html>
    """
```

**Примечание:**

Параметр `response_class` также используется для указания «типа содержимого» ответа.

В этом случае HTTP-заголовок `Content-Type` будет установлен в `text/html`.

И это будет задокументировано как таковое в OpenAPI.

### Вернуть `Response` { #return-a-response }

Как показано в разделе [Вернуть Response напрямую](response-directly.md), вы также можете переопределить ответ прямо в своей операции пути, просто вернув его.

Тот же пример сверху, возвращающий `HTMLResponse`, может выглядеть так:

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/items/")
async def read_items():
    html_content = """
    <html>
        <head>
            <title>Some HTML in here</title>
        </head>
        
            <h1>Look ma! HTML!</h1>
        
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)
```

**Предупреждение:**

`Response`, возвращённый напрямую вашей функцией-обработчиком пути, не будет задокументирован в OpenAPI (например, `Content-Type` не будет задокументирован) и не будет виден в автоматически сгенерированной интерактивной документации.

**Примечание:**

Разумеется, фактический заголовок `Content-Type`, статус-код и т.д. возьмутся из объекта `Response`, который вы вернули.

### Задокументировать в OpenAPI и переопределить `Response` { #document-in-openapi-and-override-response }

Если вы хотите переопределить ответ внутри функции, но при этом задокументировать «тип содержимого» в OpenAPI, вы можете использовать параметр `response_class` И вернуть объект `Response`.

Тогда `response_class` будет использоваться только для документирования *операции пути* в OpenAPI, а ваш `Response` будет использован как есть.

#### Вернуть `HTMLResponse` напрямую { #return-an-htmlresponse-directly }

Например, это может быть что-то вроде:

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

def generate_html_response():
    html_content = """
    <html>
        <head>
            <title>Some HTML in here</title>
        </head>
        
            <h1>Look ma! HTML!</h1>
        
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/items/", response_class=HTMLResponse)
async def read_items():
    return generate_html_response()
```

В этом примере функция `generate_html_response()` уже генерирует и возвращает `Response` вместо возврата HTML в `str`.

Возвращая результат вызова `generate_html_response()`, вы уже возвращаете `Response`, который переопределит поведение **FastAPI** по умолчанию.

Но поскольку вы также передали `HTMLResponse` в `response_class`, **FastAPI** будет знать, как задокументировать это в OpenAPI и интерактивной документации как HTML с `text/html`:

## Доступные ответы { #available-responses }

Ниже перечислены некоторые доступные классы ответов.

Учтите, что вы можете использовать `Response`, чтобы вернуть что угодно ещё, или даже создать собственный подкласс.

**Технические детали:**

Вы также могли бы использовать `from starlette.responses import HTMLResponse`.

**FastAPI** предоставляет те же `starlette.responses` как `fastapi.responses` для вашего удобства как разработчика. Но большинство доступных классов ответов приходят непосредственно из Starlette.

### `Response` { #response }

Базовый класс `Response`, от него наследуются все остальные ответы.

Его можно возвращать напрямую.

Он принимает следующие параметры:

- `content` — `str` или `bytes`.
- `status_code` — целое число, HTTP статус-код.
- `headers` — словарь строк.
- `media_type` — строка, задающая тип содержимого. Например, `"text/html"`.

FastAPI (фактически Starlette) автоматически добавит заголовок Content-Length. Также будет добавлен заголовок Content-Type, основанный на `media_type` и с добавлением charset для текстовых типов.

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

### `HTMLResponse` { #htmlresponse }

Принимает текст или байты и возвращает HTML-ответ, как описано выше.

### `PlainTextResponse` { #plaintextresponse }

Принимает текст или байты и возвращает ответ в виде простого текста.

```python
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI()

@app.get("/", response_class=PlainTextResponse)
async def main():
    return "Hello World"
```

### `JSONResponse` { #jsonresponse }

Принимает данные и возвращает ответ, кодированный как `application/json`.

Это ответ по умолчанию, используемый в **FastAPI**, как было сказано выше.

**Технические детали:**

Но если вы объявите модель ответа или тип возвращаемого значения, они будут использованы напрямую для сериализации данных в JSON, и ответ с корректным типом содержимого для JSON будет возвращён напрямую, без использования класса `JSONResponse`.

Это идеальный способ получить наилучшую производительность.

### `RedirectResponse` { #redirectresponse }

Возвращает HTTP-редирект. По умолчанию использует статус-код 307 (Temporary Redirect — временное перенаправление).

Вы можете вернуть `RedirectResponse` напрямую:

```python
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

app = FastAPI()

@app.get("/typer")
async def redirect_typer():
    return RedirectResponse("https://typer.tiangolo.com")
```

---

Или можно использовать его в параметре `response_class`:

```python
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

app = FastAPI()

@app.get("/fastapi", response_class=RedirectResponse)
async def redirect_fastapi():
    return "https://fastapi.tiangolo.com"
```

Если вы сделаете так, то сможете возвращать URL напрямую из своей функции-обработчика пути.

В этом случае будет использован статус-код по умолчанию для `RedirectResponse`, то есть `307`.

---

Также вы можете использовать параметр `status_code` в сочетании с параметром `response_class`:

```python
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

app = FastAPI()

@app.get("/pydantic", response_class=RedirectResponse, status_code=302)
async def redirect_pydantic():
    return "https://docs.pydantic.dev/"
```

### `StreamingResponse` { #streamingresponse }

Принимает асинхронный генератор или обычный генератор/итератор (функцию с `yield`) и отправляет тело ответа потоково.

```python
import anyio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

async def fake_video_streamer():
    for i in range(10):
        yield b"some fake video bytes"
        await anyio.sleep(0)

@app.get("/")
async def main():
    return StreamingResponse(fake_video_streamer())
```

**Технические детали:**

Задача `async` может быть отменена только при достижении `await`. Если `await` отсутствует, генератор (функция с `yield`) не может быть корректно отменён и может продолжить работу даже после запроса на отмену.

Так как этому небольшому примеру не нужны операторы `await`, мы добавляем `await anyio.sleep(0)`, чтобы дать циклу событий возможность обработать отмену.

Это ещё более важно для больших или бесконечных потоков.

**Совет:**

Вместо того чтобы возвращать `StreamingResponse` напрямую, вероятно, лучше следовать стилю из раздела [Передача данных потоком](./stream-data.md) - так гораздо удобнее, и отмена обрабатывается «за кулисами».

Если вы передаёте JSON Lines потоком, следуйте руководству [Поток JSON Lines](../tutorial/stream-json-lines.md).

### `FileResponse` { #fileresponse }

Асинхронно отправляет файл как ответ.

Для создания экземпляра принимает иной набор аргументов, чем другие типы ответов:

- `path` — путь к файлу, который будет отправлен.
- `headers` — любые дополнительные заголовки для включения, в виде словаря.
- `media_type` — строка, задающая тип содержимого. Если не задан, для определения типа содержимого будет использовано имя файла или путь.
- `filename` — если задан, будет включён в заголовок ответа `Content-Disposition`.

Файловые ответы будут содержать соответствующие заголовки `Content-Length`, `Last-Modified` и `ETag`.

```python
from fastapi import FastAPI
from fastapi.responses import FileResponse

some_file_path = "large-video-file.mp4"
app = FastAPI()

@app.get("/")
async def main():
    return FileResponse(some_file_path)
```

Вы также можете использовать параметр `response_class`:

```python
from fastapi import FastAPI
from fastapi.responses import FileResponse

some_file_path = "large-video-file.mp4"
app = FastAPI()

@app.get("/", response_class=FileResponse)
async def main():
    return some_file_path
```

В этом случае вы можете возвращать путь к файлу напрямую из своей функции-обработчика пути.

## Пользовательский класс ответа { #custom-response-class }

Вы можете создать собственный класс ответа, унаследовавшись от `Response`, и использовать его.

Например, предположим, что вы хотите использовать [`orjson`](https://github.com/ijl/orjson) с некоторыми настройками.

Скажем, вы хотите, чтобы возвращался отформатированный JSON с отступами, то есть хотите использовать опцию orjson `orjson.OPT_INDENT_2`.

Вы могли бы создать `CustomORJSONResponse`. Главное, что вам нужно сделать — реализовать метод `Response.render(content)`, который возвращает содержимое как `bytes`:

```python
from typing import Any

import orjson
from fastapi import FastAPI, Response

app = FastAPI()

class CustomORJSONResponse(Response):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        assert orjson is not None, "orjson must be installed"
        return orjson.dumps(content, option=orjson.OPT_INDENT_2)

@app.get("/", response_class=CustomORJSONResponse)
async def main():
    return {"message": "Hello World"}
```

Теперь вместо того, чтобы возвращать:

```json
{"message": "Hello World"}
```

...этот ответ вернёт:

```json
{
  "message": "Hello World"
}
```

Разумеется, вы наверняка найдёте гораздо более полезные способы воспользоваться этим, чем просто форматирование JSON. 😉

### `orjson` или Модель ответа { #orjson-or-response-model }

Если вы стремитесь увеличить производительность, вероятно, лучше использовать [Модель ответа](../tutorial/response-model.md), чем ответ на базе `orjson`.

С моделью ответа FastAPI использует Pydantic для сериализации данных в JSON, без промежуточных шагов, таких как преобразование через `jsonable_encoder`, которое происходило бы в любом другом случае.

А под капотом Pydantic использует те же базовые механизмы на Rust, что и `orjson`, для сериализации в JSON, так что с моделью ответа вы и так получите лучшую производительность.

## Класс ответа по умолчанию { #default-response-class }

При создании экземпляра класса **FastAPI** или `APIRouter` вы можете указать, какой класс ответа использовать по умолчанию.

Параметр, который это определяет, — `default_response_class`.

В примере ниже **FastAPI** будет использовать `HTMLResponse` по умолчанию во всех операциях пути, вместо JSON.

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(default_response_class=HTMLResponse)

@app.get("/items/")
async def read_items():
    return "<h1>Items</h1>This is a list of items."
```

**Совет:**

Вы по-прежнему можете переопределять `response_class` в операциях пути, как и раньше.

## Дополнительная документация { #additional-documentation }

Вы также можете объявить тип содержимого и многие другие детали в OpenAPI с помощью `responses`: [Дополнительные ответы в OpenAPI](additional-responses.md).
