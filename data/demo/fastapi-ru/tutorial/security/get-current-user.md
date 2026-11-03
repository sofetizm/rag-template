# Получить текущего пользователя { #get-current-user }

В предыдущей главе система безопасности (основанная на системе внедрения зависимостей) передавала *функции-обработчику пути* `token` типа `str`:

```python
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/items/")
async def read_items(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}
```

Но это всё ещё не слишком полезно.

Сделаем так, чтобы она возвращала текущего пользователя.

## Создать модель пользователя { #create-a-user-model }

Сначала создадим Pydantic-модель пользователя.

Точно так же, как мы используем Pydantic для объявления тел запросов, мы можем использовать его где угодно:

```python
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

def fake_decode_token(token):
    return User(
        username=token + "fakedecoded", email="john@example.com", full_name="John Doe"
    )

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    return user

@app.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
```

## Создать зависимость `get_current_user` { #create-a-get-current-user-dependency }

Давайте создадим зависимость `get_current_user`.

Помните, что у зависимостей могут быть подзависимости?

`get_current_user` будет иметь зависимость от того же `oauth2_scheme`, который мы создали ранее.

Аналогично тому, как мы делали ранее прямо в *операции пути*, новая зависимость `get_current_user` получит `token` типа `str` от подзависимости `oauth2_scheme`:

```python
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

def fake_decode_token(token):
    return User(
        username=token + "fakedecoded", email="john@example.com", full_name="John Doe"
    )

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    return user

@app.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
```

## Получить пользователя { #get-the-user }

`get_current_user` будет использовать созданную нами (ненастоящую) вспомогательную функцию, которая принимает токен типа `str` и возвращает нашу Pydantic-модель `User`:

```python
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

def fake_decode_token(token):
    return User(
        username=token + "fakedecoded", email="john@example.com", full_name="John Doe"
    )

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    return user

@app.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
```

## Внедрить текущего пользователя { #inject-the-current-user }

Теперь мы можем использовать тот же `Depends` с нашей `get_current_user` в *операции пути*:

```python
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

def fake_decode_token(token):
    return User(
        username=token + "fakedecoded", email="john@example.com", full_name="John Doe"
    )

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    return user

@app.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
```

Обратите внимание, что мы объявляем тип `current_user` как Pydantic-модель `User`.

Это поможет внутри функции с автозавершением и проверками типов.

**Подсказка:**

Возможно, вы помните, что тела запросов также объявляются с помощью Pydantic-моделей.

Здесь **FastAPI** не запутается, потому что вы используете `Depends`.

**Подсказка:**

То, как устроена эта система зависимостей, позволяет иметь разные зависимости (разные "dependables"), которые все возвращают модель `User`.

Мы не ограничены наличием только одной зависимости, которая может возвращать такой тип данных.

## Другие модели { #other-models }

Теперь вы можете получать текущего пользователя напрямую в *функциях-обработчиках пути* и работать с механизмами безопасности на уровне **внедрения зависимостей**, используя `Depends`.

И вы можете использовать любую модель или данные для требований безопасности (в данном случае Pydantic-модель `User`).

Но вы не ограничены использованием какой-то конкретной модели данных, класса или типа.

Хотите, чтобы в модели были `id` и `email`, но не было `username`? Пожалуйста. Можно использовать те же инструменты.

Хотите просто `str`? Или просто `dict`? Или напрямую экземпляр класса модели базы данных? Всё работает одинаково.

У вас вообще нет пользователей, которые входят в приложение, а есть роботы, боты или другие системы, у которых есть только токен доступа? Снова — всё работает так же.

Просто используйте любую модель, любой класс, любую базу данных, которые нужны вашему приложению. Система внедрения зависимостей **FastAPI** поможет вам в этом.

## Размер кода { #code-size }

Этот пример может показаться многословным. Имейте в виду, что в одном файле мы смешиваем безопасность, модели данных, вспомогательные функции и *операции пути*.

Но вот ключевой момент.

Всё, что касается безопасности и внедрения зависимостей, пишется один раз.

И вы можете сделать это настолько сложным, насколько захотите. И всё равно это будет написано только один раз, в одном месте. Со всей гибкостью.

При этом у вас могут быть тысячи эндпоинтов (*операций пути*), использующих одну и ту же систему безопасности.

И все они (или любая их часть по вашему желанию) могут воспользоваться преимуществами повторного использования этих зависимостей или любых других зависимостей, которые вы создадите.

И все эти тысячи *операций пути* могут состоять всего из 3 строк:

```python
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

def fake_decode_token(token):
    return User(
        username=token + "fakedecoded", email="john@example.com", full_name="John Doe"
    )

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    return user

@app.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
```

## Резюме { #recap }

Теперь вы можете получать текущего пользователя прямо в своей *функции-обработчике пути*.

Мы уже на полпути.

Нужно лишь добавить *операцию пути*, чтобы пользователь/клиент мог отправить `username` и `password`.

Это будет дальше.
