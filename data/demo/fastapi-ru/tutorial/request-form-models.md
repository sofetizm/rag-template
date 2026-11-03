# Модели форм { #form-models }

Вы можете использовать **Pydantic-модели** для объявления **полей формы** в FastAPI.

**Заметка:**

Чтобы использовать формы, сначала установите [`python-multipart`](https://github.com/Kludex/python-multipart).

Добавьте его в ваш проект:

```console
$ uv add python-multipart
```

**Заметка:**

Этот функционал доступен начиная с версии FastAPI `0.113.0`. 🤓

## Pydantic-модели для форм { #pydantic-models-for-forms }

Вам просто нужно объявить **Pydantic-модель** с полями, которые вы хотите получить как **поля формы**, а затем объявить параметр как `Form`:

```python
from typing import Annotated

from fastapi import FastAPI, Form
from pydantic import BaseModel

app = FastAPI()

class FormData(BaseModel):
    username: str
    password: str

@app.post("/login/")
async def login(data: Annotated[FormData, Form()]):
    return data
```

**FastAPI** **извлечёт** данные для **каждого поля** из **данных формы** в HTTP-запросе и выдаст вам объявленную Pydantic-модель.

Для [HTML-флажков](request-forms.md#boolean-form-fields) объявляйте булевы поля со значением по умолчанию `False`.

## Проверьте документацию { #check-the-docs }

Вы можете проверить это в интерфейсе документации по адресу `/docs`:

## Запрет дополнительных полей формы { #forbid-extra-form-fields }

В некоторых случаях (не особо часто встречающихся) вам может понадобиться **ограничить** поля формы только теми, которые объявлены в Pydantic-модели. И **запретить** любые **дополнительные** поля.

**Заметка:**

Этот функционал доступен начиная с версии FastAPI `0.114.0`. 🤓

Вы можете сконфигурировать Pydantic-модель так, чтобы запретить (`forbid`) все дополнительные (`extra`) поля:

```python
from typing import Annotated

from fastapi import FastAPI, Form
from pydantic import BaseModel

app = FastAPI()

class FormData(BaseModel):
    username: str
    password: str
    model_config = {"extra": "forbid"}

@app.post("/login/")
async def login(data: Annotated[FormData, Form()]):
    return data
```

Если клиент попробует отправить дополнительные данные, то он получит HTTP-ответ с **ошибкой**.

Например, если клиент попытается отправить поля формы:

* `username`: `Rick`
* `password`: `Portal Gun`
* `extra`: `Mr. Poopybutthole`

Он получит HTTP-ответ с ошибкой, сообщающий ему, что поле `extra` не разрешено:

```json
{
    "detail": [
        {
            "type": "extra_forbidden",
            "loc": ["body", "extra"],
            "msg": "Extra inputs are not permitted",
            "input": "Mr. Poopybutthole"
        }
    ]
}
```

## Комбинирование моделей форм { #combine-form-models }

Вы можете комбинировать несколько моделей форм с отдельными параметрами `Form`.

```python
from typing import Annotated

from fastapi import FastAPI, Form
from pydantic import BaseModel

app = FastAPI()

class Profile(BaseModel):
    name: str

class Preferences(BaseModel):
    tags: list[str] = []

@app.post("/profiles/")
async def create_profile(
    profile: Annotated[Profile, Form()],
    preferences: Annotated[Preferences, Form()],
    token: Annotated[str, Form()],
):
    return {"profile": profile, "preferences": preferences, "token": token}
```

Клиент отправляет `name`, `tags` и `token` как поля формы. Каждая модель валидирует поля формы независимо.

Настройка `extra` каждой модели применяется ко всем полям формы, включая поля и файлы, объявленные в других параметрах или зависимостях. При `extra="forbid"` любое поле, не входящее в эту модель, отклоняется. При `extra="allow"` такие поля включаются в модель как дополнительные.

Если несколько объявлений используют одно и то же имя поля формы, каждое из них валидирует значение этого поля. Используйте совместимые типы и ограничения для общих полей, чтобы схема OpenAPI могла описывать их согласованно.

## Необязательные модели форм { #optional-form-models }

Объявите модель формы с `| None` и значением по умолчанию `None`, чтобы сделать группу полей необязательной.

```python
from typing import Annotated

from fastapi import FastAPI, Form
from pydantic import BaseModel

app = FastAPI()

class Profile(BaseModel):
    name: str
    age: int

@app.post("/profiles/")
async def create_profile(
    token: Annotated[str, Form()],
    profile: Annotated[Profile | None, Form()] = None,
):
    return {"token": token, "profile": profile}
```

Если ни `name`, ни `age` не отправлены, `profile` имеет значение `None`. Если отправлено хотя бы одно из них, FastAPI валидирует модель и требует оба поля. Отправленное пустое значение также считается передачей поля.

При использовании `| None` без значения по умолчанию параметр по-прежнему остаётся обязательным.

Дополнительные поля обрабатываются согласно настройке `extra` модели. Игнорируемые дополнительные поля не делают модель переданной.

Необязательная модель, содержащая только неотмеченные флажки, считается не переданной. Отправьте значение, например `enabled=false`, чтобы передать её явно.

## Необязательные объединения моделей форм { #optional-unions-of-form-models }

Вы также можете использовать необязательное объединение моделей.

```python
from typing import Annotated, Literal

from fastapi import FastAPI, Form
from pydantic import BaseModel

app = FastAPI()

class Person(BaseModel):
    kind: Literal["person"]
    name: str

class Company(BaseModel):
    kind: Literal["company"]
    company_name: str

@app.post("/contacts/")
async def create_contact(
    contact: Annotated[Person | Company | None, Form(discriminator="kind")] = None,
):
    return contact
```

Если поля формы не отправлены, `contact` имеет значение `None`. Отправьте `kind=person` вместе с `name` или `kind=company` вместе с `company_name`. Дискриминатор выбирает, какую модель валидировать.

## Комбинирование объединений моделей форм { #combine-unions-of-form-models }

Вы можете комбинировать объединения с другими моделями форм, отдельными параметрами `Form` и параметрами `File`. Каждое объединение валидируется независимо.

```python
from typing import Annotated, Literal

from fastapi import FastAPI, Form
from pydantic import BaseModel

app = FastAPI()

class Person(BaseModel):
    contact_type: Literal["person"]
    name: str

class Company(BaseModel):
    contact_type: Literal["company"]
    company_name: str

class Email(BaseModel):
    notification_type: Literal["email"]
    email: str

class SMS(BaseModel):
    notification_type: Literal["sms"]
    phone: str

@app.post("/contacts/")
async def create_contact(
    contact: Annotated[Person | Company, Form(discriminator="contact_type")],
    token: Annotated[str, Form()],
    notification: Annotated[
        Email | SMS | None, Form(discriminator="notification_type")
    ] = None,
):
    return {"contact": contact, "notification": notification, "token": token}
```

Отправляйте все поля в одной форме. Например, отправьте `contact_type=person`, `name=Rick`, `notification_type=email`, `email=rick@example.com` и `token=secret`.

Не отправляйте поля уведомлений, чтобы оставить `notification` со значением `None`.

## Модели форм и файлы { #form-models-and-files }

Вы также можете комбинировать модель формы с [параметрами файлов](request-files.md).

```python
from typing import Annotated

from fastapi import FastAPI, Form, UploadFile
from pydantic import BaseModel

app = FastAPI()

class Profile(BaseModel):
    name: str

@app.post("/profiles/")
async def create_profile(profile: Annotated[Profile, Form()], avatar: UploadFile):
    return {"profile": profile, "filename": avatar.filename}
```

Здесь клиент отправляет поле `name` и файл `avatar`, используя `multipart/form-data`.

## Итоги { #summary }

Вы можете использовать Pydantic-модели для объявления полей форм в FastAPI. 😎
