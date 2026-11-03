# URL-адреса метаданных и документации { #metadata-and-docs-urls }

Вы можете настроить несколько конфигураций метаданных в вашем **FastAPI** приложении.

## Метаданные для API { #metadata-for-api }

Вы можете задать следующие поля, которые используются в спецификации OpenAPI и в UI автоматической документации API:

| Параметр | Тип | Описание |
|------------|------|-------------|
| `title` | `str` | Заголовок API. |
| `summary` | `str` | Краткое резюме API. Доступно начиная с OpenAPI 3.1.0, FastAPI 0.99.0. |
| `description` | `str` | Краткое описание API. Может быть использован Markdown. |
| `version` | `str` | Версия API. Версия вашего собственного приложения, а не OpenAPI. К примеру `2.5.0`. |
| `terms_of_service` | `str` | Ссылка на условия пользования API. Если указано, то это должен быть URL-адрес. |
| `contact` | `dict` | Контактная информация для открытого API. Может содержать несколько полей. <details><summary>поля contact</summary>ПараметрТипОписаниеnamestrИдентификационное имя контактного лица/организации.urlstrURL, указывающий на контактную информацию. ДОЛЖЕН быть в формате URL.emailstrEmail-адрес контактного лица/организации. ДОЛЖЕН быть в формате email-адреса.</details> |
| `license_info` | `dict` | Информация о лицензии открытого API. Может содержать несколько полей. <details><summary>поля license_info</summary>ПараметрТипОписаниеnamestrОБЯЗАТЕЛЬНО (если установлен параметр license_info). Название лицензии, используемой для API.identifierstrВыражение лицензии [SPDX](https://spdx.org/licenses/) для API. Поле identifier является взаимоисключающим с полем url. Доступно начиная с OpenAPI 3.1.0, FastAPI 0.99.0.urlstrURL, указывающий на лицензию, используемую для API. ДОЛЖЕН быть в формате URL.</details> |

Вы можете задать их следующим образом:

```python
from fastapi import FastAPI

description = """
ChimichangApp API helps you do awesome stuff. 🚀

## Items

You can **read items**.

## Users

You will be able to:

* **Create users** (_not implemented_).
* **Read users** (_not implemented_).
"""

app = FastAPI(
    title="ChimichangApp",
    description=description,
    summary="Deadpool's favorite app. Nuff said.",
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Deadpoolio the Amazing",
        "url": "http://x-force.example.com/contact/",
        "email": "dp@x-force.example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

@app.get("/items/")
async def read_items():
    return [{"name": "Katana"}]
```

**Подсказка:**

Вы можете использовать Markdown в поле `description`, и оно будет отображено в выводе.

С этой конфигурацией автоматическая документация API будет выглядеть так:

## Идентификатор лицензии { #license-identifier }

Начиная с OpenAPI 3.1.0 и FastAPI 0.99.0, вы также можете задать `license_info` с помощью `identifier` вместо `url`.

К примеру:

```python
from fastapi import FastAPI

description = """
ChimichangApp API helps you do awesome stuff. 🚀

## Items

You can **read items**.

## Users

You will be able to:

* **Create users** (_not implemented_).
* **Read users** (_not implemented_).
"""

app = FastAPI(
    title="ChimichangApp",
    description=description,
    summary="Deadpool's favorite app. Nuff said.",
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Deadpoolio the Amazing",
        "url": "http://x-force.example.com/contact/",
        "email": "dp@x-force.example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "identifier": "Apache-2.0",
    },
)

@app.get("/items/")
async def read_items():
    return [{"name": "Katana"}]
```

## Метаданные для тегов { #metadata-for-tags }

Вы также можете добавить дополнительные метаданные для различных тегов, используемых для группировки ваших операций пути с помощью параметра `openapi_tags`.

Он принимает список, содержащий один словарь для каждого тега.

Каждый словарь может содержать в себе:

* `name` (**обязательно**): `str`-значение с тем же именем тега, которое вы используете в параметре `tags` в ваших *операциях пути* и `APIRouter`ах.
* `description`: `str`-значение с кратким описанием для тега. Может содержать Markdown и будет отображаться в UI документации.
* `externalDocs`:  `dict`-значение, описывающее внешнюю документацию. Включает в себя:
    * `description`: `str`-значение с кратким описанием для внешней документации.
    * `url` (**обязательно**): `str`-значение с URL-адресом для внешней документации.

### Создание метаданных для тегов { #create-metadata-for-tags }

Давайте попробуем сделать это на примере с тегами для `users` и `items`.

Создайте метаданные для ваших тегов и передайте их в параметре `openapi_tags`:

```python
from fastapi import FastAPI

tags_metadata = [
    {
        "name": "users",
        "description": "Operations with users. The **login** logic is also here.",
    },
    {
        "name": "items",
        "description": "Manage items. So _fancy_ they have their own docs.",
        "externalDocs": {
            "description": "Items external docs",
            "url": "https://fastapi.tiangolo.com/",
        },
    },
]

app = FastAPI(openapi_tags=tags_metadata)

@app.get("/users/", tags=["users"])
async def get_users():
    return [{"name": "Harry"}, {"name": "Ron"}]

@app.get("/items/", tags=["items"])
async def get_items():
    return [{"name": "wand"}, {"name": "flying broom"}]
```

Помните, что вы можете использовать Markdown внутри описания, к примеру "login" будет отображен жирным шрифтом (**login**) и "fancy" будет отображаться курсивом (_fancy_).

**Подсказка:**

Вам необязательно добавлять метаданные для всех используемых тегов.

### Используйте собственные теги { #use-your-tags }

Используйте параметр `tags` с вашими *операциями пути* (и `APIRouter`ами), чтобы присвоить им различные теги:

```python
from fastapi import FastAPI

tags_metadata = [
    {
        "name": "users",
        "description": "Operations with users. The **login** logic is also here.",
    },
    {
        "name": "items",
        "description": "Manage items. So _fancy_ they have their own docs.",
        "externalDocs": {
            "description": "Items external docs",
            "url": "https://fastapi.tiangolo.com/",
        },
    },
]

app = FastAPI(openapi_tags=tags_metadata)

@app.get("/users/", tags=["users"])
async def get_users():
    return [{"name": "Harry"}, {"name": "Ron"}]

@app.get("/items/", tags=["items"])
async def get_items():
    return [{"name": "wand"}, {"name": "flying broom"}]
```

**Примечание:**

Узнайте больше о тегах в [Конфигурации операции пути](path-operation-configuration.md#tags).

### Проверьте документацию { #check-the-docs }

Теперь, если вы проверите документацию, вы увидите всю дополнительную информацию:

### Порядок расположения тегов { #order-of-tags }

Порядок расположения словарей метаданных для каждого тега определяет также порядок, отображаемый в UI документации.

К примеру, несмотря на то, что `users` будут идти после `items` в алфавитном порядке, они отображаются раньше, потому что мы добавляем свои метаданные в качестве первого словаря в списке.

## URL-адрес OpenAPI { #openapi-url }

По умолчанию схема OpenAPI отдаётся по адресу `/openapi.json`.

Но вы можете изменить это с помощью параметра `openapi_url`.

К примеру, чтобы задать её отдачу по адресу `/api/v1/openapi.json`:

```python
from fastapi import FastAPI

app = FastAPI(openapi_url="/api/v1/openapi.json")

@app.get("/items/")
async def read_items():
    return [{"name": "Foo"}]
```

Если вы хотите отключить схему OpenAPI полностью, вы можете задать `openapi_url=None`, это также отключит пользовательские интерфейсы документации, которые её используют.

## URL-адреса документации { #docs-urls }

Вы можете изменить конфигурацию двух включённых пользовательских интерфейсов документации:

* **Swagger UI**: отдаётся по адресу `/docs`.
    * Вы можете задать его URL с помощью параметра `docs_url`.
    * Вы можете отключить это с помощью настройки `docs_url=None`.
* **ReDoc**: отдаётся по адресу `/redoc`.
    * Вы можете задать его URL с помощью параметра `redoc_url`.
    * Вы можете отключить это с помощью настройки `redoc_url=None`.

К примеру, чтобы настроить отдачу Swagger UI по адресу `/documentation` и отключить ReDoc:

```python
from fastapi import FastAPI

app = FastAPI(docs_url="/documentation", redoc_url=None)

@app.get("/items/")
async def read_items():
    return [{"name": "Foo"}]
```
