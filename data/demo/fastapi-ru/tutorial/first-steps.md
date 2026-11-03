# Первые шаги { #first-steps }

Самый простой файл FastAPI может выглядеть так:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

Скопируйте это в файл `main.py`.

**Подсказка:**

У FastAPI есть [официальное расширение для VS Code](https://marketplace.visualstudio.com/items?itemName=FastAPILabs.fastapi-vscode) (и Cursor), которое предоставляет множество функций, включая обозреватель операций пути, поиск операций пути, навигацию CodeLens в тестах (переход к определению из тестов), а также развертывание и логи FastAPI Cloud — всё из вашего редактора кода.

Запустите сервер в режиме реального времени:

```console
$ uv run fastapi dev

   FastAPI   Starting development server 🚀

             Searching for package file structure from directories
             with __init__.py files
             Importing from /home/user/code/awesomeapp

    module   🐍 main.py

      code   Importing the FastAPI app object from the module with
             the following code:

             from main import app

       app   Using import string: main:app

    server   Server started at http://127.0.0.1:8000
    server   Documentation at http://127.0.0.1:8000/docs

       tip   Running in development mode, for production use:
             fastapi run

             Logs:

      INFO   Will watch for changes in these directories:
             ['/home/user/code/awesomeapp']
      INFO   Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C
             to quit)
      INFO   Started reloader process [383138] using WatchFiles
      INFO   Started server process [383153]
      INFO   Waiting for application startup.
      INFO   Application startup complete.
```

В выводе будет строка примерно такого вида:

```hl_lines
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Эта строка показывает URL, по которому ваше приложение доступно на локальной машине.

### Проверьте { #check-it }

Откройте браузер по адресу: [http://127.0.0.1:8000](http://127.0.0.1:8000).

Вы увидите JSON-ответ вида:

```json
{"message": "Hello World"}
```

### Интерактивная документация API { #interactive-api-docs }

Теперь перейдите по адресу: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

Вы увидите автоматически сгенерированную интерактивную документацию по API (предоставлено [Swagger UI](https://github.com/swagger-api/swagger-ui)):

![Swagger UI](https://fastapi.tiangolo.com/img/index/index-01-swagger-ui-simple.png)

### Альтернативная документация API { #alternative-api-docs }

И теперь перейдите по адресу [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc).

Вы увидите альтернативную автоматически сгенерированную документацию (предоставлено [ReDoc](https://github.com/Redocly/redoc)):

![ReDoc](https://fastapi.tiangolo.com/img/index/index-02-redoc-simple.png)

### OpenAPI { #openapi }

**FastAPI** генерирует «схему» всего вашего API, используя стандарт **OpenAPI** для описания API.

#### «Схема» { #schema }

«Схема» — это определение или описание чего-либо. Не код, который это реализует, а только абстрактное описание.

#### «Схема» API { #api-schema }

В данном случае [OpenAPI](https://github.com/OAI/OpenAPI-Specification) — это спецификация, которая определяет, как описывать схему вашего API.

Это определение схемы включает пути вашего API, возможные параметры, которые они принимают, и т.п.

#### «Схема» данных { #data-schema }

Термин «схема» также может относиться к форме некоторых данных, например, к содержимому JSON.

В таком случае это будут атрибуты JSON, их типы данных и т.п.

#### OpenAPI и JSON Schema { #openapi-and-json-schema }

OpenAPI определяет схему API для вашего API. И эта схема включает определения (или «схемы») данных, отправляемых и получаемых вашим API, с использованием стандарта **JSON Schema** для схем данных JSON.

#### Посмотрите `openapi.json` { #check-the-openapi-json }

Если вам интересно, как выглядит исходная схема OpenAPI, FastAPI автоматически генерирует JSON (схему) с описанием всего вашего API.

Вы можете посмотреть её напрямую по адресу: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json).

Вы увидите JSON, начинающийся примерно так:

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
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {

...
```

#### Для чего нужен OpenAPI { #what-is-openapi-for }

Схема OpenAPI является основой для обеих включённых систем интерактивной документации.

Есть десятки альтернатив, все основаны на OpenAPI. Вы можете легко добавить любую из них в ваше приложение, созданное с **FastAPI**.

Вы также можете использовать её для автоматической генерации кода для клиентов, которые взаимодействуют с вашим API. Например, для фронтенд-, мобильных или IoT-приложений.

### Настройте app `entrypoint` в `pyproject.toml` { #configure-the-app-entrypoint-in-pyproject-toml }

Вы можете указать расположение вашего приложения в файле `pyproject.toml`, например:

```toml
[tool.fastapi]
entrypoint = "main:app"
```

Этот `entrypoint` подскажет команде `fastapi`, что приложение нужно импортировать так:

```python
from main import app
```

Если структура вашего кода выглядит так:

```
.
├── backend
│   ├── main.py
│   ├── __init__.py
```

Тогда следует указать такой `entrypoint`:

```toml
[tool.fastapi]
entrypoint = "backend.main:app"
```

что будет эквивалентно:

```python
from backend.main import app
```

### `fastapi dev` с путём или с опцией CLI `--entrypoint` { #fastapi-dev-with-path-or-with-entrypoint-cli-option }

Вы также можете передать путь к файлу в команду `fastapi dev`, и она попытается определить объект приложения FastAPI для использования:

```console
$ uv run fastapi dev main.py
```

Или вы можете передать опцию `--entrypoint` команде `fastapi dev`:

```console
$ uv run fastapi dev --entrypoint main:app
```

Но в этом случае вам придётся каждый раз помнить о передаче корректного пути/entrypoint при вызове команды `fastapi`.

Кроме того, другие инструменты могут его не найти, например [Расширение VS Code](../editor-support.md) или [FastAPI Cloud](https://fastapicloud.com), поэтому рекомендуется использовать `entrypoint` в `pyproject.toml`.

### Разверните приложение (необязательно) { #deploy-your-app-optional }

При желании вы можете развернуть своё приложение FastAPI в [FastAPI Cloud](https://fastapicloud.com) одной командой. 🚀

```console
$ uv run fastapi deploy

Deploying to FastAPI Cloud...

✅ Deployment successful!

🐔 Ready the chicken! Your app is ready at https://myapp.fastapicloud.dev
```

CLI автоматически определит ваше приложение FastAPI и развернёт его в облаке. Если вы не вошли в систему, откроется браузер для завершения процесса аутентификации.

Готово! Теперь вы можете открыть своё приложение по этому URL. ✨

## Рассмотрим поэтапно { #recap-step-by-step }

### Шаг 1: импортируйте `FastAPI` { #step-1-import-fastapi }

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

`FastAPI` — это класс на Python, который предоставляет всю функциональность для вашего API.

**Технические детали:**

`FastAPI` — это класс, который напрямую наследуется от `Starlette`.

Вы можете использовать весь функционал [Starlette](https://starlette.dev/) и в `FastAPI`.

### Шаг 2: создайте экземпляр `FastAPI` { #step-2-create-a-fastapi-instance }

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

Здесь переменная `app` будет экземпляром класса `FastAPI`.

Это будет основная точка взаимодействия для создания всего вашего API.

### Шаг 3: создайте *операцию пути* { #step-3-create-a-path-operation }

#### Путь { #path }

Здесь «путь» — это последняя часть URL, начиная с первого символа `/`.

Итак, в таком URL:

```
https://example.com/items/foo
```

...путь будет:

```
/items/foo
```

**Примечание:**

«Путь» также часто называют «эндпоинт» или «маршрут».

При создании API «путь» — это основной способ разделения «задач» и «ресурсов».

#### Операция { #operation }

«Операция» здесь — это один из HTTP-«методов».

Один из:

* `POST`
* `GET`
* `PUT`
* `DELETE`

...и более экзотические:

* `OPTIONS`
* `HEAD`
* `PATCH`
* `TRACE`

В протоколе HTTP можно обращаться к каждому пути, используя один (или несколько) из этих «методов».

---

При создании API обычно используют конкретные HTTP-методы для выполнения конкретных действий.

Обычно используют:

* `POST`: создать данные.
* `GET`: прочитать данные.
* `PUT`: обновить данные.
* `DELETE`: удалить данные.

Таким образом, в OpenAPI каждый HTTP-метод называется «операцией».

Мы тоже будем называть их «**операциями**».

#### Определите *декоратор операции пути* { #define-a-path-operation-decorator }

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

`@app.get("/")` сообщает **FastAPI**, что функция прямо под ним отвечает за обработку HTTP-запросов, поступающих:

* по пути `/`
* с использованием операции get

**Информация о `@decorator`:**

Синтаксис `@something` в Python называется «декоратор».

Его размещают над функцией. Как красивая декоративная шляпа (кажется, отсюда и пошёл термин).

«Декоратор» берёт функцию ниже и делает с ней что-то.

В нашем случае этот декоратор сообщает **FastAPI**, что функция ниже соответствует **пути** `/` с **операцией** `get`.

Это и есть «декоратор операции пути».

Можно также использовать другие операции:

* `@app.post()`
* `@app.put()`
* `@app.delete()`

И более экзотические:

* `@app.options()`
* `@app.head()`
* `@app.patch()`
* `@app.trace()`

**Подсказка:**

Вы можете использовать каждый метод (HTTP-операцию) так, как считаете нужным.

**FastAPI** не навязывает какого-либо конкретного смысла.

Эта информация дана как рекомендация, а не требование.

Например, при использовании GraphQL обычно все действия выполняются только с помощью POST-операций.

### Шаг 4: определите **функцию-обработчик пути** { #step-4-define-the-path-operation-function }

Вот наша «**функция-обработчик пути**»:

* **путь**: `/`.
* **операция**: `get`.
* **функция**: функция ниже «декоратора» (ниже `@app.get("/")`).

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

Это функция на Python.

**FastAPI** будет вызывать её каждый раз, когда получает HTTP-запрос к URL «`/`» с операцией `GET`.

В данном случае это асинхронная (`async`) функция.

---

Вы также можете определить её как обычную функцию вместо `async def`:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}
```

**Примечание:**

Если вы не знаете, в чём разница, посмотрите [Асинхронность: *"Нет времени?"*](../async.md#in-a-hurry).

### Шаг 5: верните содержимое { #step-5-return-the-content }

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

Вы можете вернуть `dict`, `list`, отдельные значения `str`, `int` и т.д.

Также можно вернуть модели Pydantic (подробнее об этом позже).

Многие другие объекты и модели будут автоматически преобразованы в JSON (включая ORM и т.п.). Попробуйте использовать те, что вам привычнее, с высокой вероятностью они уже поддерживаются.

### Шаг 6: разверните приложение { #step-6-deploy-it }

Разверните приложение в **[FastAPI Cloud](https://fastapicloud.com)** одной командой: `fastapi deploy`. 🎉

#### О FastAPI Cloud { #about-fastapi-cloud }

**[FastAPI Cloud](https://fastapicloud.com)** создан тем же автором и командой, что и **FastAPI**.

Он упрощает процесс **создания образа**, **развертывания** и **доступа** к API с минимальными усилиями.

Он переносит тот же **опыт разработчика** при создании приложений с FastAPI на их **развертывание** в облаке. 🎉

FastAPI Cloud — основной спонсор и источник финансирования для open-source проектов *FastAPI и друзья*. ✨

#### Развертывание у других облачных провайдеров { #deploy-to-other-cloud-providers }

FastAPI — open-source и основан на стандартах. Вы можете развернуть приложения FastAPI у любого облачного провайдера по вашему выбору.

Следуйте руководствам вашего облачного провайдера, чтобы развернуть приложения FastAPI у них. 🤓

## Резюме { #recap }

* Импортируйте `FastAPI`.
* Создайте экземпляр `app`.
* Напишите **декоратор операции пути**, например `@app.get("/")`.
* Определите **функцию-обработчик пути**; например, `def root(): ...`.
* Запустите сервер разработки командой `fastapi dev`.
* При желании разверните приложение командой `fastapi deploy`.
