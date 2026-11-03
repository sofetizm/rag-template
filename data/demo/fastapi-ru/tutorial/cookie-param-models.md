# Модели параметров cookie { #cookie-parameter-models }

Если у вас есть группа **cookies**, которые связаны между собой, вы можете создать **Pydantic-модель** для их объявления. 🍪

Это позволит вам **переиспользовать модель** в **разных местах**, а также объявить проверки и метаданные сразу для всех параметров. 😎

**Заметка:**

Этот функционал доступен с версии FastAPI `0.115.0`. 🤓

**Совет:**

Такой же подход применяется для `Query`, `Cookie` и `Header`. 😎

## Pydantic-модель для cookies { #cookies-with-a-pydantic-model }

Объявите параметры **cookie**, которые вам нужны, в **Pydantic-модели**, а затем объявите параметр как `Cookie`:

```python
from typing import Annotated

from fastapi import Cookie, FastAPI
from pydantic import BaseModel

app = FastAPI()

class Cookies(BaseModel):
    session_id: str
    fatebook_tracker: str | None = None
    googall_tracker: str | None = None

@app.get("/items/")
async def read_items(cookies: Annotated[Cookies, Cookie()]):
    return cookies
```

**FastAPI** **извлечёт** данные для **каждого поля** из **cookies**, полученных в HTTP-запросе, и выдаст вам объявленную Pydantic-модель.

## Проверка сгенерированной документации { #check-the-docs }

Вы можете посмотреть объявленные cookies в графическом интерфейсе Документации по пути `/docs`:

**Заметка:**

Имейте в виду, что, поскольку **браузеры обрабатывают cookies** особым образом и под капотом, они **не** позволят **JavaScript** легко получить доступ к ним.

Если вы перейдёте к **графическому интерфейсу документации API** по пути `/docs`, то сможете увидеть **документацию** по cookies для ваших *операций пути*.

Но даже если вы **заполните данные** и нажмёте "Execute", поскольку графический интерфейс Документации работает с **JavaScript**, cookies не будут отправлены, и вы увидите сообщение об **ошибке** как будто не указывали никаких значений.

## Запрет дополнительных cookies { #forbid-extra-cookies }

В некоторых случаях (не особо часто встречающихся) вам может понадобиться **ограничить** cookies, которые вы хотите получать.

Теперь у вашего API есть возможность контролировать своё согласие на использование cookie. 🤪🍪

Вы можете сконфигурировать Pydantic-модель так, чтобы запретить (`forbid`) любые дополнительные (`extra`) поля:

```python
from typing import Annotated

from fastapi import Cookie, FastAPI
from pydantic import BaseModel

app = FastAPI()

class Cookies(BaseModel):
    model_config = {"extra": "forbid"}

    session_id: str
    fatebook_tracker: str | None = None
    googall_tracker: str | None = None

@app.get("/items/")
async def read_items(cookies: Annotated[Cookies, Cookie()]):
    return cookies
```

Если клиент попробует отправить **дополнительные cookies**, то получит HTTP-ответ с **ошибкой**.

Бедные баннеры cookies, они всеми силами пытаются получить ваше согласие — и всё ради того, чтобы API его отклонил. 🍪

Например, если клиент попытается отправить cookie `santa_tracker` со значением `good-list-please`, то получит HTTP-ответ с **ошибкой**, сообщающей ему, что `santa_tracker` cookie не разрешён:

```json
{
    "detail": [
        {
            "type": "extra_forbidden",
            "loc": ["cookie", "santa_tracker"],
            "msg": "Extra inputs are not permitted",
            "input": "good-list-please",
        }
    ]
}
```

## Комбинирование моделей параметров { #combine-parameter-models }

Вы можете комбинировать несколько моделей параметров cookie с отдельными параметрами cookie и зависимостями. Данные для каждой модели извлекаются и валидируются независимо, как описано для [моделей query-параметров](query-param-models.md#combine-parameter-models).

Настройка `extra` каждой модели применяется ко всем параметрам cookie, включая объявленные в других моделях или зависимостях. При `extra="forbid"` любой cookie, не входящий в эту модель, отклоняется. При `extra="allow"` такие cookies включаются в модель как дополнительные поля.

## Необязательные модели параметров cookie { #optional-cookie-parameter-models }

Объявите модель параметров cookie с `| None` и значением по умолчанию `None`, чтобы сделать группу необязательной.

```python
from typing import Annotated

from fastapi import Cookie, FastAPI
from pydantic import BaseModel

app = FastAPI()

class Preferences(BaseModel):
    theme: str
    locale: str

@app.get("/items/")
async def read_items(preferences: Annotated[Preferences | None, Cookie()] = None):
    return preferences
```

Если ни `theme`, ни `locale` не переданы, `preferences` равен `None`. Если передан хотя бы один из них, FastAPI валидирует модель и требует оба поля.

Применяются те же правила для значений по умолчанию, дополнительных полей и OpenAPI, что и для [необязательных моделей query-параметров](query-param-models.md#optional-query-parameter-models).

## Заключение { #summary }

Вы можете использовать **Pydantic-модели** для объявления **cookies** в **FastAPI**. 😎
