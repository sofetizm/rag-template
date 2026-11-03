# Модели Header-параметров { #header-parameter-models }

Если у вас есть группа связанных **header-параметров**, то вы можете объединить их в одну **Pydantic-модель**.

Это позволит вам **переиспользовать модель** в **разных местах**, а также задать валидацию и метаданные сразу для всех параметров. 😎

**Заметка:**

Этот функционал доступен в FastAPI начиная с версии `0.115.0`. 🤓

## Header-параметры в виде Pydantic-модели { #header-parameters-with-a-pydantic-model }

Объявите нужные **header-параметры** в **Pydantic-модели** и затем аннотируйте параметр как `Header`:

```python
from typing import Annotated

from fastapi import FastAPI, Header
from pydantic import BaseModel

app = FastAPI()

class CommonHeaders(BaseModel):
    host: str
    save_data: bool
    if_modified_since: str | None = None
    traceparent: str | None = None
    x_tag: list[str] = []

@app.get("/items/")
async def read_items(headers: Annotated[CommonHeaders, Header()]):
    return headers
```

**FastAPI** **извлечёт** данные для **каждого поля** из **HTTP-заголовков** HTTP-запроса и выдаст заданную вами Pydantic-модель.

## Проверьте документацию { #check-the-docs }

Вы можете посмотреть обязательные HTTP-заголовки в графическом интерфейсе документации по пути `/docs`:

## Как запретить дополнительные HTTP-заголовки { #forbid-extra-headers }

В некоторых случаях (не особо часто встречающихся) вам может понадобиться **ограничить** HTTP-заголовки, которые вы хотите получать.

Вы можете использовать возможности конфигурации Pydantic-модели для того, чтобы запретить (`forbid`) любые дополнительные (`extra`) поля:

```python
from typing import Annotated

from fastapi import FastAPI, Header
from pydantic import BaseModel

app = FastAPI()

class CommonHeaders(BaseModel):
    model_config = {"extra": "forbid"}

    host: str
    save_data: bool
    if_modified_since: str | None = None
    traceparent: str | None = None
    x_tag: list[str] = []

@app.get("/items/")
async def read_items(headers: Annotated[CommonHeaders, Header()]):
    return headers
```

Если клиент попробует отправить **дополнительные HTTP-заголовки**, то в ответ он получит **ошибку**.

Например, если клиент попытается отправить HTTP-заголовок `tool` со значением `plumbus`, то в ответ он получит **ошибку**, сообщающую ему, что header-параметр `tool` не разрешен:

```json
{
    "detail": [
        {
            "type": "extra_forbidden",
            "loc": ["header", "tool"],
            "msg": "Extra inputs are not permitted",
            "input": "plumbus",
        }
    ]
}
```

## Как отключить автоматическое преобразование подчеркиваний { #disable-convert-underscores }

Как и в случае с обычными header-параметрами, если у вас в именах параметров имеются символы подчеркивания, они **автоматически преобразовываются в дефис**.

Например, если в коде есть header-параметр `save_data`, то ожидаемый HTTP-заголовок будет `save-data` и именно так он будет отображаться в документации.

Если по каким-то причинам вам нужно отключить данное автоматическое преобразование, это можно сделать и для Pydantic-моделей для header-параметров.

```python
from typing import Annotated

from fastapi import FastAPI, Header
from pydantic import BaseModel

app = FastAPI()

class CommonHeaders(BaseModel):
    host: str
    save_data: bool
    if_modified_since: str | None = None
    traceparent: str | None = None
    x_tag: list[str] = []

@app.get("/items/")
async def read_items(
    headers: Annotated[CommonHeaders, Header(convert_underscores=False)],
):
    return headers
```

**Внимание:**

Перед тем как устанавливать для параметра `convert_underscores` значение `False`, имейте в виду, что некоторые HTTP-прокси и серверы не разрешают использовать HTTP-заголовки с символами подчеркивания.

## Комбинирование моделей параметров { #combine-parameter-models }

Вы можете комбинировать несколько моделей header-параметров с отдельными header-параметрами и зависимостями. Данные для каждой модели извлекаются и валидируются независимо, как описано для [моделей query-параметров](query-param-models.md#combine-parameter-models).

Настройка `extra` каждой модели применяется ко всем header-параметрам, включая объявленные в других моделях или зависимостях. При `extra="forbid"` любой HTTP-заголовок, не входящий в эту модель, отклоняется. При `extra="allow"` такие HTTP-заголовки включаются в модель как дополнительные поля.

Каждая модель использует собственную настройку `Header(convert_underscores=...)` как при чтении HTTP-запроса, так и при генерации OpenAPI. Явно заданные псевдонимы полей остаются именами HTTP-заголовков без преобразований.

## Необязательные модели header-параметров { #optional-header-parameter-models }

Объявите модель header-параметров с `| None` и значением по умолчанию `None`, чтобы сделать группу необязательной.

```python
from typing import Annotated

from fastapi import FastAPI, Header
from pydantic import BaseModel

app = FastAPI()

class ClientHeaders(BaseModel):
    x_client_name: str
    x_client_version: str

@app.get("/items/")
async def read_items(client: Annotated[ClientHeaders | None, Header()] = None):
    return client
```

Если не отправлен ни `x-client-name`, ни `x-client-version`, значение `client` равно `None`. Если отправлен хотя бы один из них, FastAPI валидирует модель и требует оба поля.

Для значений по умолчанию, дополнительных полей и OpenAPI действуют те же правила, что и для [необязательных моделей query-параметров](query-param-models.md#optional-query-parameter-models).

HTTP-заголовки, такие как `Host`, также подчиняются настройке `extra` модели. При `extra="allow"` их наличие приводит к созданию модели, даже если ни одно из объявленных полей не передано.

## Резюме { #summary }

Вы можете использовать **Pydantic-модели** для объявления **HTTP-заголовков** в **FastAPI**. 😎
