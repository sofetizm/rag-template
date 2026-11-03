# Веб-сокеты { #websockets }

Вы можете использовать [веб-сокеты](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API) в **FastAPI**.

## Установка `websockets` { #install-websockets }

Добавьте `websockets` (библиотека Python, упрощающая работу с протоколом "WebSocket") в ваш проект:

```console
$ uv add websockets

---> 100%
```

## Клиент WebSockets { #websockets-client }

### В продакшн { #in-production }

В продакшн у вас, вероятно, есть фронтенд, созданный с помощью современного фреймворка вроде React, Vue.js или Angular.

И для взаимодействия с бекендом по WebSocket вы, скорее всего, будете использовать инструменты вашего фронтенда.

Также у вас может быть нативное мобильное приложение, которое напрямую, нативным кодом, взаимодействует с вашим WebSocket-бекендом.

Либо у вас может быть любой другой способ взаимодействия с WebSocket-эндпоинтом.

---

Но для этого примера мы воспользуемся очень простым HTML‑документом с небольшим JavaScript, всё внутри одной длинной строки.

Конечно же, это неоптимально, и вы бы не использовали это в продакшн.

В продакшн у вас был бы один из вариантов выше.

Но это самый простой способ сосредоточиться на серверной части веб‑сокетов и получить рабочий пример:

```python
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            
            Send
        </form>
        
        
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
```

## Создание `websocket` { #create-a-websocket }

В вашем **FastAPI** приложении создайте `websocket`:

```python
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            
            Send
        </form>
        
        
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
```

**Технические детали:**

Вы также можете использовать `from starlette.websockets import WebSocket`.

**FastAPI** напрямую предоставляет тот же самый `WebSocket` просто для удобства вас, разработчика. Но на самом деле это `WebSocket` из Starlette.

## Ожидание и отправка сообщений { #await-for-messages-and-send-messages }

В вашем WebSocket-маршруте вы можете `await` сообщения и отправлять сообщения.

```python
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            
            Send
        </form>
        
        
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
```

Вы можете получать и отправлять двоичные, текстовые и JSON данные.

## Проверка в действии { #try-it }

Поместите ваш код в файл `main.py`, затем запустите приложение:

```console
$ uv run fastapi dev

INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Откройте браузер по адресу [http://127.0.0.1:8000](http://127.0.0.1:8000).

Вы увидите следующую простенькую страницу:

Вы можете набирать сообщения в поле ввода и отправлять их:

И ваше **FastAPI** приложение с веб-сокетами ответит:

Вы можете отправлять (и получать) множество сообщений:

И все они будут использовать одно и то же WebSocket-соединение.

## Использование `Depends` и не только { #using-depends-and-others }

В WebSocket-эндпоинтах вы можете импортировать из `fastapi` и использовать:

* `Depends`
* `Security`
* `Cookie`
* `Header`
* `Path`
* `Query`

Они работают так же, как и в других FastAPI эндпоинтах/*операциях пути*:

```python
from typing import Annotated

from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    Query,
    WebSocket,
    WebSocketException,
    status,
)
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <label>Item ID: </label>
            <label>Token: </label>
            Connect
            <hr>
            <label>Message: </label>
            Send
        </form>
        
        
        <script>
        var ws = null;
            function connect(event) {
                var itemId = document.getElementById("itemId")
                var token = document.getElementById("token")
                ws = new WebSocket("ws://localhost:8000/items/" + itemId.value + "/ws?token=" + token.value);
                ws.onmessage = function(event) {
                    var messages = document.getElementById('messages')
                    var message = document.createElement('li')
                    var content = document.createTextNode(event.data)
                    message.appendChild(content)
                    messages.appendChild(message)
                };
                event.preventDefault()
            }
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

async def get_cookie_or_token(
    websocket: WebSocket,
    session: Annotated[str | None, Cookie()] = None,
    token: Annotated[str | None, Query()] = None,
):
    if session is None and token is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    return session or token

@app.websocket("/items/{item_id}/ws")
async def websocket_endpoint(
    *,
    websocket: WebSocket,
    item_id: str,
    q: int | None = None,
    cookie_or_token: Annotated[str, Depends(get_cookie_or_token)],
):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(
            f"Session cookie or query token value is: {cookie_or_token}"
        )
        if q is not None:
            await websocket.send_text(f"Query parameter q is: {q}")
        await websocket.send_text(f"Message text was: {data}, for item ID: {item_id}")
```

**Примечание:**

Поскольку это WebSocket, вызывать `HTTPException` на самом деле не имеет смысла, вместо этого мы вызываем `WebSocketException`.

Вы можете использовать код закрытия из [допустимых кодов, определённых в спецификации](https://tools.ietf.org/html/rfc6455#section-7.4.1).

### Веб-сокеты с зависимостями: проверка в действии { #try-the-websockets-with-dependencies }

Запустите приложение:

```console
$ uv run fastapi dev

INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Откройте браузер по адресу [http://127.0.0.1:8000](http://127.0.0.1:8000).

Там вы можете задать:

* "Item ID", используемый в пути.
* "Token", используемый как query-параметр.

**Подсказка:**

Обратите внимание, что query `token` будет обработан в зависимости.

После этого вы можете подключиться к веб-сокету, а затем отправлять и получать сообщения:

## Обработка отключений и работа с несколькими клиентами { #handling-disconnections-and-multiple-clients }

Когда WebSocket-соединение закрыто, `await websocket.receive_text()` вызовет исключение `WebSocketDisconnect`, которое можно поймать и обработать как в этом примере.

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    
        <h1>WebSocket Chat</h1>
        <h2>Your ID: </h2>
        <form action="" onsubmit="sendMessage(event)">
            
            Send
        </form>
        
        
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8000/ws/${client_id}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    
</html>
"""

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")
```

Чтобы воспроизвести пример:

* Откройте приложение в нескольких вкладках браузера.
* Отправьте из них сообщения.
* Затем закройте одну из вкладок.

Это вызовет исключение `WebSocketDisconnect`, и все остальные клиенты получат следующее сообщение:

```
Client #1596980209979 left the chat
```

**Подсказка:**

Приложение выше - это минимальный и простой пример, демонстрирующий обработку и рассылку сообщений нескольким WebSocket-соединениям.

Но имейте в виду, что, так как всё обрабатывается в памяти, в простом списке, это будет работать только пока процесс запущен и только с одним процессом.

Если нужно что-то легко интегрируемое с FastAPI, но более надежное и с поддержкой Redis, PostgreSQL или другого, то можно воспользоваться [encode/broadcaster](https://github.com/encode/broadcaster).

## Дополнительная информация { #more-info }

Для более глубокого изучения возможностей воспользуйтесь документацией Starlette:

* [Класс `WebSocket`](https://starlette.dev/websockets/).
* [Обработка WebSocket на основе классов](https://starlette.dev/endpoints/#websocketendpoint).
