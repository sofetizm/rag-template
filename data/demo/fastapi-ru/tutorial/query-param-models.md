# Модели Query-Параметров { #query-parameter-models }

Если у вас есть группа связанных **query-параметров**, то вы можете объединить их в одну **Pydantic-модель**.

Это позволит вам **переиспользовать модель** в **разных местах**, объявлять правила валидации и метаданные сразу для всех параметров. 😎

**Заметка:**

Это поддерживается начиная с версии FastAPI `0.115.0`. 🤓

## Pydantic-Модель для Query-Параметров { #query-parameters-with-a-pydantic-model }

Объявите нужные **query-параметры** в **Pydantic-модели**, а после объявите параметр как `Query`:

```python
from typing import Annotated, Literal

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

app = FastAPI()

class FilterParams(BaseModel):
    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []

@app.get("/items/")
async def read_items(filter_query: Annotated[FilterParams, Query()]):
    return filter_query
```

**FastAPI извлечёт** данные, соответствующие **каждому полю модели**, из **query-параметров** HTTP-запроса и выдаст вам объявленную Pydantic-модель, заполненную ими.

## Проверьте Сгенерированную Документацию { #check-the-docs }

Вы можете посмотреть query-параметры в графическом интерфейсе сгенерированной документации по пути `/docs`:

## Запретить Дополнительные Query-Параметры { #forbid-extra-query-parameters }

В некоторых случаях (не особо часто встречающихся) вам может понадобиться **ограничить** query-параметры, которые вы хотите получить.

Вы можете сконфигурировать Pydantic-модель так, чтобы запретить (`forbid`) все дополнительные (`extra`) поля:

```python
from typing import Annotated, Literal

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

app = FastAPI()

class FilterParams(BaseModel):
    model_config = {"extra": "forbid"}

    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []

@app.get("/items/")
async def read_items(filter_query: Annotated[FilterParams, Query()]):
    return filter_query
```

Если клиент попробует отправить **дополнительные** данные в **query-параметрах**, то он получит HTTP-ответ с **ошибкой**.

Например, если клиент попытается отправить query-параметр `tool` со значением `plumbus`, в виде:

```http
https://example.com/items/?limit=10&tool=plumbus
```

То он получит HTTP-ответ с **ошибкой**, сообщающей ему, что query-параметр `tool` не разрешен:

```json
{
    "detail": [
        {
            "type": "extra_forbidden",
            "loc": ["query", "tool"],
            "msg": "Extra inputs are not permitted",
            "input": "plumbus"
        }
    ]
}
```

## Комбинирование Моделей Параметров { #combine-parameter-models }

Вы можете объявить несколько моделей query-параметров и комбинировать их с отдельными query-параметрами или зависимостями.

```python
from typing import Annotated

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

app = FastAPI()

class Pagination(BaseModel):
    limit: int = Field(10, ge=1)
    offset: int = Field(0, ge=0)

class Filters(BaseModel):
    tags: list[str] = []

@app.get("/items/")
def read_items(
    pagination: Annotated[Pagination, Query()],
    filters: Annotated[Filters, Query()],
    search: str | None = None,
):
    return {"pagination": pagination, "filters": filters, "search": search}
```

Параметры HTTP-запроса остаются на одном уровне.

```http
https://example.com/items/?limit=5&offset=10&tags=red&tags=blue&search=shirt
```

В строке запроса нет ключей `pagination` или `filters`. Каждая модель независимо валидирует query-параметры, используя собственные значения по умолчанию, валидаторы полей и валидаторы модели. То же самое происходит, когда модели или отдельные параметры объявлены в зависимостях.

Если модели используют одно и то же имя или псевдоним параметра, каждая модель независимо валидирует этот параметр HTTP-запроса. Используйте разные имена или псевдонимы для независимых значений. OpenAPI отображает общий параметр один раз, как и в случае параметров, общих с зависимостями, поэтому объявления общего параметра должны описывать одинаковые тип и ограничения.

Настройка `extra` каждой модели применяется ко всем query-параметрам, включая объявленные в других моделях или зависимостях. При `extra="forbid"` любой параметр, не входящий в эту модель, отклоняется. При `extra="allow"` такие параметры включаются в модель как дополнительные поля.

Это также работает для моделей `Header` и `Cookie`.

## Необязательные Модели Query-Параметров { #optional-query-parameter-models }

Объявите модель query-параметров с `| None` и значением по умолчанию `None`, чтобы сделать группу необязательной.

```python
from datetime import date
from typing import Annotated

from fastapi import FastAPI, Query
from pydantic import BaseModel

app = FastAPI()

class DateRange(BaseModel):
    start: date
    end: date

@app.get("/items/")
async def read_items(
    limit: int = 10,
    date_range: Annotated[DateRange | None, Query()] = None,
):
    return {"limit": limit, "date_range": date_range}
```

Если ни `start`, ни `end` не переданы, `date_range` равен `None`. Если передан хотя бы один из них, FastAPI валидирует модель и требует оба поля.

При использовании `| None` без значения по умолчанию параметр остаётся обязательным.

Дополнительные параметры обрабатываются согласно настройке `extra` модели. Игнорируемые дополнительные параметры не приводят к созданию экземпляра модели.

OpenAPI отображает поля группы по отдельности и помечает их как необязательные.

Вы также можете объявлять необязательные [модели параметров HTTP-заголовков](header-param-models.md#optional-header-parameter-models) и [модели cookie-параметров](cookie-param-models.md#optional-cookie-parameter-models).

## Заключение { #summary }

Вы можете использовать **Pydantic-модели** для объявления **query-параметров** в **FastAPI**. 😎

**Совет:**

Спойлер: вы также можете использовать Pydantic-модели, чтобы объявлять cookies и HTTP-заголовки, но об этом вы прочитаете позже в руководстве. 🤫
