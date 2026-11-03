# Простая авторизация OAuth2 с паролем и «Bearer» { #simple-oauth2-with-password-and-bearer }

Теперь, отталкиваясь от предыдущей главы, добавим недостающие части, чтобы получить полный поток безопасности.

## Получение `username` и `password` { #get-the-username-and-password }

Для получения `username` и `password` мы будем использовать утилиты безопасности **FastAPI**.

OAuth2 определяет, что при использовании "password flow" (аутентификация по паролю - именно его мы используем) клиент/пользователь должен передавать поля `username` и `password` в полях формы.

В спецификации сказано, что поля должны быть названы именно так. Поэтому `user-name` или `email` работать не будут.

Но не волнуйтесь, вы можете отобразить это конечным пользователям во фронтенде в том виде, в котором хотите.

А ваши модели баз данных могут использовать любые другие имена.

Но для *операции пути* входа в систему нам нужно использовать именно эти имена, чтобы быть совместимыми со спецификацией (и иметь возможность, например, использовать встроенную систему документации API).

В спецификации также указано, что `username` и `password` должны передаваться в виде данных формы (так что никакого JSON здесь нет).

### `scope` { #scope }

В спецификации также говорится, что клиент может передать еще одно поле формы — `scope`.

Имя поля формы — `scope` (в единственном числе), но на самом деле это длинная строка, состоящая из отдельных "scopes", разделенных пробелами.

Каждый "scope" — это просто строка (без пробелов).

Обычно они используются для указания уровней доступа, например:

* `users:read` или `users:write` — распространенные примеры.
* `instagram_basic` используется Facebook / Instagram.
* `https://www.googleapis.com/auth/drive` используется Google.

**Примечание:**
В OAuth2 "scope" — это просто строка, которая указывает требуемое конкретное разрешение.

Не имеет значения, содержит ли она другие символы, например `:`, или является ли это URL.

Эти детали зависят от реализации.

Для OAuth2 это просто строки.

## Код для получения `username` и `password` { #code-to-get-the-username-and-password }

Теперь воспользуемся утилитами, предоставляемыми **FastAPI**, чтобы обработать это.

### `OAuth2PasswordRequestForm` { #oauth2passwordrequestform }

Сначала импортируйте `OAuth2PasswordRequestForm` и затем используйте её как зависимость с `Depends` в *операции пути* для `/token`:

```python
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": True,
    },
}

app = FastAPI()

def fake_hash_password(password: str):
    return "fakehashed" + password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def fake_decode_token(token):
    # This doesn't provide any security at all
    # Check the next version
    user = get_user(fake_users_db, token)
    return user

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user
```

`OAuth2PasswordRequestForm` — это зависимость-класс, которая объявляет тело формы со следующими полями:

* `username`.
* `password`.
* Необязательное поле `scope` в виде большой строки, состоящей из строк, разделенных пробелами.
* Необязательное поле `grant_type`.

**Подсказка:**
По спецификации OAuth2 поле `grant_type` *обязательно* и содержит фиксированное значение `password`, но `OAuth2PasswordRequestForm` это не проверяет строго.

Если вам нужно это строгое требование, используйте `OAuth2PasswordRequestFormStrict` вместо `OAuth2PasswordRequestForm`.

* Необязательное поле `client_id` (в нашем примере оно не нужно).
* Необязательное поле `client_secret` (в нашем примере оно не нужно).

**Примечание:**
`OAuth2PasswordRequestForm` — это не специальный класс для **FastAPI**, как `OAuth2PasswordBearer`.

`OAuth2PasswordBearer` сообщает **FastAPI**, что это схема безопасности. Поэтому она добавляется в OpenAPI соответствующим образом.

А `OAuth2PasswordRequestForm` — это просто зависимость-класс, которую вы могли бы написать сами, или вы могли бы объявить параметры `Form` напрямую.

Но так как это распространённый вариант использования, он предоставлен **FastAPI** напрямую, чтобы упростить задачу.

### Использование данных формы { #use-the-form-data }

**Подсказка:**
У экземпляра зависимости `OAuth2PasswordRequestForm` не будет атрибута `scope` с длинной строкой, разделенной пробелами. Вместо этого будет атрибут `scopes` со списком отдельных строк — по одной для каждого переданного scope.

В данном примере мы не используем `scopes`, но если вам это необходимо, функциональность есть.

Теперь получим данные о пользователе из (ненастоящей) базы данных, используя `username` из поля формы.

Если такого пользователя нет, то мы возвращаем ошибку "Incorrect username or password".

Для ошибки используем исключение `HTTPException`:

```python
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": True,
    },
}

app = FastAPI()

def fake_hash_password(password: str):
    return "fakehashed" + password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def fake_decode_token(token):
    # This doesn't provide any security at all
    # Check the next version
    user = get_user(fake_users_db, token)
    return user

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user
```

### Проверка пароля { #check-the-password }

На данный момент у нас есть данные о пользователе из нашей базы данных, но мы еще не проверили пароль.

Давайте сначала поместим эти данные в Pydantic-модель `UserInDB`.

Никогда нельзя сохранять пароли в открытом виде, поэтому мы будем использовать (пока что ненастоящую) систему хеширования паролей.

Если пароли не совпадают, мы возвращаем ту же ошибку.

#### Хеширование паролей { #password-hashing }

"Хеширование" означает: преобразование некоторого содержимого (в данном случае пароля) в последовательность байтов (просто строку), которая выглядит как тарабарщина.

Каждый раз, когда вы передаете точно такое же содержимое (точно такой же пароль), вы получаете точно такую же тарабарщину.

Но преобразовать тарабарщину обратно в пароль невозможно.

##### Зачем использовать хеширование паролей { #why-use-password-hashing }

Если вашу базу данных украдут, у злоумышленника не будет паролей пользователей в открытом виде, только хэши.

Таким образом, он не сможет попробовать использовать эти же пароли в другой системе (поскольку многие пользователи используют один и тот же пароль повсеместно, это было бы опасно).

```python
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": True,
    },
}

app = FastAPI()

def fake_hash_password(password: str):
    return "fakehashed" + password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def fake_decode_token(token):
    # This doesn't provide any security at all
    # Check the next version
    user = get_user(fake_users_db, token)
    return user

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user
```

#### Про `**user_dict` { #about-user-dict }

`UserInDB(**user_dict)` означает:

*Передать ключи и значения `user_dict` непосредственно как аргументы ключ-значение, эквивалентно:*

```python
UserInDB(
    username=user_dict["username"],
    email=user_dict["email"],
    full_name=user_dict["full_name"],
    disabled=user_dict["disabled"],
    hashed_password=user_dict["hashed_password"],
)
```

**Примечание:**
Более полное объяснение `**user_dict` можно найти в [документации к **Дополнительным моделям**](../extra-models.md#about-user-in-model-dump).

## Возврат токена { #return-the-token }

HTTP-ответ эндпоинта `token` должен быть объектом JSON.

В нём должен быть `token_type`. В нашем случае, поскольку мы используем токены типа "Bearer", тип токена должен быть `bearer`.

И в нём должен быть `access_token` — строка, содержащая наш токен доступа.

В этом простом примере мы намеренно поступим небезопасно и вернём тот же `username` в качестве токена.

**Подсказка:**
В следующей главе вы увидите реальную защищённую реализацию с хешированием паролей и токенами JWT (JSON Web Tokens - JSON веб-токены).

Но пока давайте сосредоточимся на необходимых нам деталях.

```python
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": True,
    },
}

app = FastAPI()

def fake_hash_password(password: str):
    return "fakehashed" + password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def fake_decode_token(token):
    # This doesn't provide any security at all
    # Check the next version
    user = get_user(fake_users_db, token)
    return user

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user
```

**Подсказка:**
Согласно спецификации, вы должны возвращать JSON с `access_token` и `token_type`, как в данном примере.

Это то, что вы должны сделать сами в своём коде и убедиться, что вы используете именно эти JSON-ключи.

Это практически единственное, о чём нужно не забыть, чтобы соответствовать спецификациям.

Остальное за вас сделает **FastAPI**.

## Обновление зависимостей { #update-the-dependencies }

Теперь мы обновим наши зависимости.

Мы хотим получить `current_user` *только* если этот пользователь активен.

Поэтому мы создаём дополнительную зависимость `get_current_active_user`, которая, в свою очередь, использует в качестве зависимости `get_current_user`.

Обе эти зависимости просто вернут HTTP-ошибку, если пользователь не существует или неактивен.

Таким образом, в нашем эндпоинте мы получим пользователя только в том случае, если он существует, корректно аутентифицирован и активен:

```python
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": True,
    },
}

app = FastAPI()

def fake_hash_password(password: str):
    return "fakehashed" + password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def fake_decode_token(token):
    # This doesn't provide any security at all
    # Check the next version
    user = get_user(fake_users_db, token)
    return user

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user
```

**Примечание:**
Дополнительный HTTP-заголовок `WWW-Authenticate` со значением `Bearer`, который мы здесь возвращаем, также является частью спецификации.

Любой HTTP статус-код ошибки 401 "UNAUTHORIZED" должен также возвращать HTTP-заголовок `WWW-Authenticate`.

В случае с bearer-токенами (наш случай) значение этого HTTP-заголовка должно быть `Bearer`.

Фактически, этот дополнительный HTTP-заголовок можно опустить, и всё будет работать.

Но он приведён здесь для соответствия спецификациям.

Кроме того, могут существовать инструменты, которые ожидают его и могут использовать (сейчас или в будущем), и это может быть полезно для вас или ваших пользователей — сейчас или в будущем.

В этом и заключается преимущество стандартов...

## Посмотрим, как это работает { #see-it-in-action }

Откройте интерактивную документацию: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### Аутентификация { #authenticate }

Нажмите кнопку "Authorize".

Используйте учётные данные:

Пользователь: `johndoe`

Пароль: `secret`

После аутентификации вы увидите следующее:

### Получение собственных пользовательских данных { #get-your-own-user-data }

Теперь используйте операцию `GET` с путём `/users/me`.

Вы получите свои пользовательские данные, например:

```json
{
  "username": "johndoe",
  "email": "johndoe@example.com",
  "full_name": "John Doe",
  "disabled": false,
  "hashed_password": "fakehashedsecret"
}
```

Если щёлкнуть на значке замка и выйти из системы, а затем попробовать выполнить ту же операцию ещё раз, будет выдана ошибка HTTP 401:

```json
{
  "detail": "Not authenticated"
}
```

### Неактивный пользователь { #inactive-user }

Теперь попробуйте с неактивным пользователем, аутентифицируйтесь с:

Пользователь: `alice`

Пароль: `secret2`

И попробуйте использовать операцию `GET` с путём `/users/me`.

Вы получите ошибку "Inactive user", как здесь:

```json
{
  "detail": "Inactive user"
}
```

## Резюме { #recap }

Теперь у вас есть инструменты для реализации полноценной системы безопасности на основе `username` и `password` для вашего API.

Используя эти средства, можно сделать систему безопасности совместимой с любой базой данных и с любой моделью пользователя или моделью данных.

Единственная деталь, которой не хватает, — система пока ещё не "защищена" по-настоящему.

В следующей главе вы увидите, как использовать библиотеку безопасного хеширования паролей и токены JWT (JSON Web Tokens - JSON веб-токены).
