# Загрузка файлов { #request-files }

Используя класс `File`, мы можем позволить клиентам загружать файлы.

**Примечание:**

Чтобы получать загруженные файлы, сначала установите [`python-multipart`](https://github.com/Kludex/python-multipart).

Добавьте его в свой проект:

```console
$ uv add python-multipart
```

Это связано с тем, что загружаемые файлы передаются как "данные формы".

## Импорт `File` { #import-file }

Импортируйте `File` и `UploadFile` из модуля `fastapi`:

```python
from typing import Annotated

from fastapi import FastAPI, File, UploadFile

app = FastAPI()

@app.post("/files/")
async def create_file(file: Annotated[bytes, File()]):
    return {"file_size": len(file)}

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    return {"filename": file.filename}
```

## Определите параметры `File` { #define-file-parameters }

Создайте параметры `File` так же, как вы это делаете для `Body` или `Form`:

```python
from typing import Annotated

from fastapi import FastAPI, File, UploadFile

app = FastAPI()

@app.post("/files/")
async def create_file(file: Annotated[bytes, File()]):
    return {"file_size": len(file)}

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    return {"filename": file.filename}
```

**Примечание:**

`File` - это класс, который наследуется непосредственно от `Form`.

Но помните, что когда вы импортируете `Query`, `Path`, `File` и другие из `fastapi`, на самом деле это функции, которые возвращают специальные классы.

**Подсказка:**

Чтобы объявить файлы в теле запроса, необходимо использовать `File`, поскольку иначе параметры будут интерпретироваться как параметры запроса или body-параметры (JSON).

Файлы будут загружены как "данные формы".

Если вы объявите тип параметра у *функции-обработчика пути* как `bytes`, то **FastAPI** прочитает файл за вас, и вы получите его содержимое в виде `bytes`.

Следует иметь в виду, что все содержимое будет храниться в памяти. Это хорошо подходит для небольших файлов.

Однако возможны случаи, когда использование `UploadFile` может оказаться полезным.

## Параметры файла с `UploadFile` { #file-parameters-with-uploadfile }

Определите параметр файла с типом `UploadFile`:

```python
from typing import Annotated

from fastapi import FastAPI, File, UploadFile

app = FastAPI()

@app.post("/files/")
async def create_file(file: Annotated[bytes, File()]):
    return {"file_size": len(file)}

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    return {"filename": file.filename}
```

Использование `UploadFile` имеет ряд преимуществ перед `bytes`:

* Использовать `File()` в значении параметра по умолчанию не обязательно.
* При этом используется "буферный" файл:
    * Файл, хранящийся в памяти до максимального предела размера, после преодоления которого он будет храниться на диске.
* Это означает, что он будет хорошо работать с большими файлами, такими как изображения, видео, большие бинарные файлы и т.д., не потребляя при этом всю память.
* Из загруженного файла можно получить метаданные.
* Он реализует [file-like](https://docs.python.org/3/glossary.html#term-file-like-object) `async` интерфейс.
* Он предоставляет реальный объект Python [`SpooledTemporaryFile`](https://docs.python.org/3/library/tempfile.html#tempfile.SpooledTemporaryFile), который вы можете передать непосредственно другим библиотекам, которые ожидают file-like объект.

### `UploadFile` { #uploadfile }

`UploadFile` имеет следующие атрибуты:

* `filename`: Строка `str` с исходным именем файла, который был загружен (например, `myimage.jpg`).
* `content_type`: Строка `str` с типом содержимого (MIME-тип / тип содержимого) (например, `image/jpeg`).
* `file`: [`SpooledTemporaryFile`](https://docs.python.org/3/library/tempfile.html#tempfile.SpooledTemporaryFile) ([file-like](https://docs.python.org/3/glossary.html#term-file-like-object) объект). Это фактический файл Python, который можно передавать непосредственно другим функциям или библиотекам, ожидающим file-like объект.

`UploadFile` имеет следующие методы `async`. Все они вызывают соответствующие файловые методы (используя внутренний `SpooledTemporaryFile`).

* `write(data)`: Записать данные `data` (`str` или `bytes`) в файл.
* `read(size)`: Прочитать количество `size` (`int`) байт/символов из файла.
* `seek(offset)`: Перейти к байту на позиции `offset` (`int`) в файле.
    * Например, `await myfile.seek(0)` перейдет к началу файла.
    * Это особенно удобно, если вы один раз выполнили команду `await myfile.read()`, а затем вам нужно прочитать содержимое файла еще раз.
* `close()`: Закрыть файл.

Поскольку все эти методы являются `async` методами, вам следует использовать "await" вместе с ними.

Например, внутри `async` *функции-обработчика пути* можно получить содержимое с помощью:

```python
contents = await myfile.read()
```

Если вы находитесь внутри обычной `def` *функции-обработчика пути*, можно получить прямой доступ к файлу `UploadFile.file`, например:

```python
contents = myfile.file.read()
```

**Технические детали `async`:**

При использовании методов `async` **FastAPI** запускает файловые методы в пуле потоков и ожидает их.

**Технические детали Starlette:**

`UploadFile` из **FastAPI** наследуется непосредственно от `UploadFile` из **Starlette**, но добавляет некоторые необходимые части для совместимости с **Pydantic** и другими частями FastAPI.

## Что такое «данные формы» { #what-is-form-data }

Способ, которым HTML-формы (`<form></form>`) отправляют данные на сервер, обычно использует "специальную" кодировку для этих данных, отличную от JSON.

**FastAPI** позаботится о том, чтобы считать эти данные из нужного места, а не из JSON.

**Технические детали:**

Данные из форм обычно кодируются с использованием типа содержимого `application/x-www-form-urlencoded`, когда они не включают файлы.

Но когда форма включает файлы, она кодируется как `multipart/form-data`. Если вы используете `File`, **FastAPI** будет знать, что ему нужно получить файлы из нужной части тела запроса.

Если вы хотите узнать больше об этих кодировках и полях форм, перейдите к [веб-документации MDN (Mozilla Developer Network - Сеть разработчиков Mozilla) по `POST`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/POST).

**Внимание:**

В *операции пути* можно объявить несколько параметров `File` и `Form`, но нельзя также объявлять поля `Body`, которые предполагается получить в виде JSON, поскольку HTTP-запрос будет иметь тело, закодированное с помощью `multipart/form-data`, а не `application/json`.

Это не является ограничением **FastAPI**, это часть протокола HTTP.

## Необязательная загрузка файлов { #optional-file-upload }

Вы можете сделать загрузку файла необязательной, используя стандартные аннотации типов и установив значение по умолчанию `None`:

```python
from typing import Annotated

from fastapi import FastAPI, File, UploadFile

app = FastAPI()

@app.post("/files/")
async def create_file(file: Annotated[bytes | None, File()] = None):
    if not file:
        return {"message": "No file sent"}
    else:
        return {"file_size": len(file)}

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile | None = None):
    if not file:
        return {"message": "No upload file sent"}
    else:
        return {"filename": file.filename}
```

## `UploadFile` с дополнительными метаданными { #uploadfile-with-additional-metadata }

Вы также можете использовать `File()` вместе с `UploadFile`, например, для установки дополнительных метаданных:

```python
from typing import Annotated

from fastapi import FastAPI, File, UploadFile

app = FastAPI()

@app.post("/files/")
async def create_file(file: Annotated[bytes, File(description="A file read as bytes")]):
    return {"file_size": len(file)}

@app.post("/uploadfile/")
async def create_upload_file(
    file: Annotated[UploadFile, File(description="A file read as UploadFile")],
):
    return {"filename": file.filename}
```

## Загрузка нескольких файлов { #multiple-file-uploads }

Можно одновременно загружать несколько файлов.

Они будут связаны с одним и тем же "полем формы", отправляемым с помощью "данных формы".

Для этого необходимо объявить список `bytes` или `UploadFile`:

```python
from typing import Annotated

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.post("/files/")
async def create_files(files: Annotated[list[bytes], File()]):
    return {"file_sizes": [len(file) for file in files]}

@app.post("/uploadfiles/")
async def create_upload_files(files: list[UploadFile]):
    return {"filenames": [file.filename for file in files]}

@app.get("/")
async def main():
    content = """

<form action="/files/" enctype="multipart/form-data" method="post">

</form>
<form action="/uploadfiles/" enctype="multipart/form-data" method="post">

</form>

    """
    return HTMLResponse(content=content)
```

Вы получите, как и было объявлено, список `list` из `bytes` или объектов `UploadFile`.

**Технические детали:**

Можно также использовать `from starlette.responses import HTMLResponse`.

**FastAPI** предоставляет тот же `starlette.responses`, что и `fastapi.responses`, просто для удобства разработчика. Однако большинство доступных ответов поступает непосредственно из Starlette.

### Загрузка нескольких файлов с дополнительными метаданными { #multiple-file-uploads-with-additional-metadata }

Так же, как и раньше, вы можете использовать `File()` для задания дополнительных параметров, даже для `UploadFile`:

```python
from typing import Annotated

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.post("/files/")
async def create_files(
    files: Annotated[list[bytes], File(description="Multiple files as bytes")],
):
    return {"file_sizes": [len(file) for file in files]}

@app.post("/uploadfiles/")
async def create_upload_files(
    files: Annotated[
        list[UploadFile], File(description="Multiple files as UploadFile")
    ],
):
    return {"filenames": [file.filename for file in files]}

@app.get("/")
async def main():
    content = """

<form action="/files/" enctype="multipart/form-data" method="post">

</form>
<form action="/uploadfiles/" enctype="multipart/form-data" method="post">

</form>

    """
    return HTMLResponse(content=content)
```

## Резюме { #recap }

Используйте `File`, `bytes` и `UploadFile`, чтобы объявлять файлы для загрузки в HTTP-запросе, передаваемые как данные формы.
