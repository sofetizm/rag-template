# Настройка Swagger UI { #configure-swagger-ui }

Вы можете настроить дополнительные [параметры Swagger UI](https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/).

Чтобы настроить их, передайте аргумент `swagger_ui_parameters` при создании объекта приложения `FastAPI()` или в функцию `get_swagger_ui_html()`.

`swagger_ui_parameters` принимает словарь с настройками, которые передаются в Swagger UI напрямую.

FastAPI преобразует эти настройки в **JSON**, чтобы они были совместимы с JavaScript, поскольку именно это требуется Swagger UI.

## Отключить подсветку синтаксиса { #disable-syntax-highlighting }

Например, вы можете отключить подсветку синтаксиса в Swagger UI.

Без изменения настроек подсветка синтаксиса включена по умолчанию:

Но вы можете отключить её, установив `syntaxHighlight` в `False`:

```python
from fastapi import FastAPI

app = FastAPI(swagger_ui_parameters={"syntaxHighlight": False})

@app.get("/users/{username}")
async def read_user(username: str):
    return {"message": f"Hello {username}"}
```

…и после этого Swagger UI больше не будет показывать подсветку синтаксиса:

## Изменить тему { #change-the-theme }

Аналогично вы можете задать тему подсветки синтаксиса с ключом `"syntaxHighlight.theme"` (обратите внимание, что посередине стоит точка):

```python
from fastapi import FastAPI

app = FastAPI(swagger_ui_parameters={"syntaxHighlight": {"theme": "obsidian"}})

@app.get("/users/{username}")
async def read_user(username: str):
    return {"message": f"Hello {username}"}
```

Эта настройка изменит цветовую тему подсветки синтаксиса:

## Изменить параметры Swagger UI по умолчанию { #change-default-swagger-ui-parameters }

FastAPI включает некоторые параметры конфигурации по умолчанию, подходящие для большинства случаев.

Это включает следующие настройки по умолчанию:

Вы можете переопределить любую из них, указав другое значение в аргументе `swagger_ui_parameters`.

Например, чтобы отключить `deepLinking`, можно передать такие настройки в `swagger_ui_parameters`:

```python
from fastapi import FastAPI

app = FastAPI(swagger_ui_parameters={"deepLinking": False})

@app.get("/users/{username}")
async def read_user(username: str):
    return {"message": f"Hello {username}"}
```

## Другие параметры Swagger UI { #other-swagger-ui-parameters }

Чтобы увидеть все остальные возможные настройки, прочитайте официальную [документацию по параметрам Swagger UI](https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/).

## Настройки только для JavaScript { #javascript-only-settings }

Swagger UI также допускает другие настройки, которые являются **чисто JavaScript-объектами** (например, JavaScript-функциями).

FastAPI также включает следующие настройки `presets` (только для JavaScript):

```javascript
presets: [
    SwaggerUIBundle.presets.apis,
    SwaggerUIBundle.SwaggerUIStandalonePreset
]
```

Это объекты **JavaScript**, а не строки, поэтому напрямую передать их из Python-кода нельзя.

Если вам нужны такие настройки только для JavaScript, используйте один из методов выше. Переопределите *операцию пути* Swagger UI и вручную напишите любой необходимый JavaScript.
