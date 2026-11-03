# Потоковая передача данных { #stream-data }

Если вам нужно передавать потоковые данные, которые можно представить как JSON, воспользуйтесь [стримингом JSON Lines](../tutorial/stream-json-lines.md).

Но если вы хотите передавать в потоке **чистые бинарные данные** или строки, ниже показано, как это сделать.

**Примечание:**

Добавлено в FastAPI 0.134.0.

## Варианты использования { #use-cases }

Это можно использовать, если вы хотите стримить чистые строки, например, напрямую из вывода сервиса **AI LLM**.

Также вы можете стримить **большие бинарные файлы**, передавая каждый чанк данных по мере чтения, без необходимости загружать всё в память сразу.

Аналогично можно стримить **видео** или **аудио** — данные могут даже генерироваться по мере обработки и отправки.

## «`StreamingResponse` с `yield`» { #a-streamingresponse-with-yield }

Если вы укажете `response_class=StreamingResponse` в своей *функции-обработчике пути*, вы можете использовать `yield`, чтобы по очереди отправлять каждый чанк данных.

```python
from collections.abc import AsyncIterable, Iterable

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

message = """
Rick: (stumbles in drunkenly, and turns on the lights) Morty! You gotta come on. You got--... you gotta come with me.
Morty: (rubs his eyes) What, Rick? What's going on?
Rick: I got a surprise for you, Morty.
Morty: It's the middle of the night. What are you talking about?
Rick: (spills alcohol on Morty's bed) Come on, I got a surprise for you. (drags Morty by the ankle) Come on, hurry up. (pulls Morty out of his bed and into the hall)
Morty: Ow! Ow! You're tugging me too hard!
Rick: We gotta go, gotta get outta here, come on. Got a surprise for you Morty.
"""

@app.get("/story/stream", response_class=StreamingResponse)
async def stream_story() -> AsyncIterable[str]:
    for line in message.splitlines():
        yield line
```

FastAPI будет передавать каждый чанк данных в `StreamingResponse` как есть, не пытаясь конвертировать его в JSON или что-то подобное.

### Не-async *функции-обработчики пути* { #non-async-path-operation-functions }

Можно использовать и обычные функции `def` (без `async`) и точно так же применять `yield`.

```python
@app.get("/story/stream-no-async", response_class=StreamingResponse)
def stream_story_no_async() -> Iterable[str]:
    for line in message.splitlines():
        yield line
```

### Без аннотации { #no-annotation }

Для потоковой передачи бинарных данных вам не нужно указывать аннотацию типа возвращаемого значения.

Поскольку FastAPI не будет пытаться конвертировать данные в JSON с помощью Pydantic или сериализовать их каким-либо образом, в данном случае аннотация типа нужна только для вашего редактора кода и инструментов, FastAPI её использовать не будет.

```python
@app.get("/story/stream-no-annotation", response_class=StreamingResponse)
async def stream_story_no_annotation():
    for line in message.splitlines():
        yield line
```

Это также означает, что с `StreamingResponse` у вас есть и **свобода**, и **ответственность** — производить и кодировать байты данных ровно в том виде, в котором они должны быть отправлены, независимо от аннотаций типов. 🤓

### Потоковая передача байтов { #stream-bytes }

Один из основных сценариев — стримить `bytes` вместо строк, и, конечно, это можно сделать.

```python
@app.get("/story/stream-bytes", response_class=StreamingResponse)
async def stream_story_bytes() -> AsyncIterable[bytes]:
    for line in message.splitlines():
        yield line.encode("utf-8")
```

## Пользовательский `PNGStreamingResponse` { #a-custom-pngstreamingresponse }

В примерах выше байты данных передавались потоком, но в ответе не было HTTP-заголовка `Content-Type`, поэтому клиент не знал, какой тип данных он получает.

Вы можете создать пользовательский подкласс `StreamingResponse`, который устанавливает HTTP-заголовок `Content-Type` в тип данных, которые вы стримите.

Например, вы можете создать `PNGStreamingResponse`, который устанавливает HTTP-заголовок `Content-Type` в `image/png` с помощью атрибута `media_type`:

```python
from fastapi.responses import StreamingResponse
# ...
class PNGStreamingResponse(StreamingResponse):
    media_type = "image/png"
```

Затем вы можете использовать этот новый класс в `response_class=PNGStreamingResponse` в своей *функции-обработчике пути*:

```python
@app.get("/image/stream", response_class=PNGStreamingResponse)
async def stream_image() -> AsyncIterable[bytes]:
    with read_image() as image_file:
        for chunk in image_file:
            yield chunk
```

### Симулировать файл { #simulate-a-file }

В этом примере мы симулируем файл с помощью `io.BytesIO` — это «файлоподобный» объект, который существует только в памяти, но позволяет использовать тот же интерфейс.

Например, мы можем итерироваться по нему, чтобы потреблять его содержимое, как и по обычному файлу.

```python
import base64
from collections.abc import AsyncIterable, Iterable
from io import BytesIO

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAB0AAAAdCAYAAABWk2cPAAAAbnpUWHRSYXcgcHJvZmlsZSB0eXBlIGV4aWYAAHjadYzRDYAwCET/mcIRDoq0jGOiJm7g+NJK0vjhS4DjIEfHfZ20DKqSrrWZmyFQV5ctRMOLACxglNCcXk7zVqFzJzF8kV6R5vOJ97yVH78HjfYAtg0ged033ZgAAAoCaVRYdFhNTDpjb20uYWRvYmUueG1wAAAAAAA8P3hwYWNrZXQgYmVnaW49Iu+7vyIgaWQ9Ilc1TTBNcENlaGlIenJlU3pOVGN6a2M5ZCI/Pgo8eDp4bXBtZXRhIHhtbG5zOng9ImFkb2JlOm5zOm1ldGEvIiB4OnhtcHRrPSJYTVAgQ29yZSA0LjQuMC1FeGl2MiI+CiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPgogIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PSIiCiAgICB4bWxuczpleGlmPSJodHRwOi8vbnMuYWRvYmUuY29tL2V4aWYvMS4wLyIKICAgIHhtbG5zOnRpZmY9Imh0dHA6Ly9ucy5hZG9iZS5jb20vdGlmZi8xLjAvIgogICBleGlmOlBpeGVsWERpbWVuc2lvbj0iMjkiCiAgIGV4aWY6UGl4ZWxZRGltZW5zaW9uPSIyOSIKICAgdGlmZjpJbWFnZVdpZHRoPSIyOSIKICAgdGlmZjpJbWFnZUxlbmd0aD0iMjkiCiAgIHRpZmY6T3JpZW50YXRpb249IjEiLz4KIDwvcmRmOlJERj4KPC94OnhtcG1ldGE+CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAKPD94cGFja2V0IGVuZD0idyI/PnQkBZAAAAAEc0JJVAgICAh8CGSIAAABoklEQVRIx8VXwY7FIAjE5iXWU+P/f6RHPNW9LIaOoHYP+0yMShVkwNGG1lqjfy4HfaF0oyEEt+oSQqBaa//m9Wd6PlqhhbRMDiEQM3e59FNKw5qZHpnQfuPaW6lazsztvu/eElFj5j63lNLlMz2ttbZtVMu1MTGo5Sujn93gMzOllKiUQjHGB9QxxneZhJ5iwZ1rL2fwenoGeL0q3wVGhBPHMz0PeFccIfASEeWcO8xEROd50q6eAV6s1s5XXoncas1EKqVQznnwUBdJJmm1l3hmmdlOMrGO8Vl5gZ56Y0y8IZF0BuqkQWM4B6HXrRCKa1SEqyzEo7KK59RT/VHDjX3ZvSefeW3CO6O6vsiA1NrwVkxxAcYTCcHyTjZmJd00pugBQoTnzjvn+kzLBh9GtRDjhleZFwbx3kugP3GvFzdkqRlbDYw0u/HxKjuOw2QxZCGL5V5f4l7cd6qsffUa1DcLM9N1XcTMvep5ul1e4jNPtZfWGIkE6dI8MquXg/dS2CGVJQ2ushd5GmlxFdOw+1tRa32MY4zDQ9yaZ60J3/iX+QG4U3qGrFHmswAAAABJRU5ErkJggg=="
binary_image = base64.b64decode(image_base64)

def read_image() -> BytesIO:
    return BytesIO(binary_image)

app = FastAPI()

class PNGStreamingResponse(StreamingResponse):
    media_type = "image/png"

@app.get("/image/stream", response_class=PNGStreamingResponse)
async def stream_image() -> AsyncIterable[bytes]:
    with read_image() as image_file:
        for chunk in image_file:
            yield chunk
```

**Технические детали:**

Две другие переменные, `image_base64` и `binary_image`, — это изображение, закодированное в Base64, а затем преобразованное в байты, после чего переданное в `io.BytesIO`.

Только для того, чтобы всё помещалось в одном файле для этого примера, и вы могли скопировать код и запустить его как есть. 🥚

Используя блок `with`, мы гарантируем, что объект, ведущий себя как файл, будет закрыт после завершения работы функции‑генератора (функции с `yield`). То есть после того, как она закончит отправку ответа.

В этом конкретном примере это не столь важно, потому что это «фейковый» файл в памяти (`io.BytesIO`), но для реального файла важно удостовериться, что файл закрыт после завершения работы с ним.

### Файлы и async { #files-and-async }

В большинстве случаев «файлоподобные» объекты по умолчанию не совместимы с async и await.

Например, у них нет `await file.read()` или `async for chunk in file`.

И во многих случаях чтение таких объектов будет блокирующей операцией (которая может заблокировать цикл событий), потому что данные читаются с диска или из сети.

**Примечание:**

Приведённый выше пример — исключение, потому что объект `io.BytesIO` уже находится в памяти, поэтому чтение ничего не блокирует.

Но во многих случаях чтение файла или «файлоподобного» объекта будет блокировать.

Чтобы не блокировать цикл событий, вы можете просто объявить *функцию-обработчик пути* обычной `def` вместо `async def`. Тогда FastAPI выполнит её в воркере из пула потоков (threadpool), чтобы не блокировать основной цикл.

```python
@app.get("/image/stream-no-async", response_class=PNGStreamingResponse)
def stream_image_no_async() -> Iterable[bytes]:
    with read_image() as image_file:
        for chunk in image_file:
            yield chunk
```

**Совет:**

Если вам нужно вызвать блокирующий код изнутри async-функции, или async-функцию изнутри блокирующей функции, вы можете использовать [Asyncer](https://asyncer.tiangolo.com), родственную библиотеку к FastAPI.

### `yield from` { #yield-from }

Когда вы итерируетесь по чему‑то, например, по «файлоподобному» объекту, и делаете `yield` для каждого элемента, вы можете также использовать `yield from`, чтобы отдавать каждый элемент напрямую и не писать цикл `for`.

Это не специфично для FastAPI, это просто Python, но полезный приём. 😎

```python
@app.get("/image/stream-no-async-yield-from", response_class=PNGStreamingResponse)
def stream_image_no_async_yield_from() -> Iterable[bytes]:
    with read_image() as image_file:
        yield from image_file
```
