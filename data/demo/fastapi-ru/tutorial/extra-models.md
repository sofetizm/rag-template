# Дополнительные модели { #extra-models }

В продолжение прошлого примера будет уже обычным делом иметь несколько связанных между собой моделей.

Это особенно применимо в случае моделей пользователя, потому что:

* **Модель для ввода** должна иметь возможность содержать пароль.
* **Модель для вывода** не должна содержать пароль.
* **Модель для базы данных**, возможно, должна содержать хэшированный пароль.

**Внимание:**

Никогда не храните пароли пользователей в чистом виде. Всегда храните "безопасный хэш", который вы затем сможете проверить.

Если вам это не знакомо, вы можете узнать про "хэш пароля" в [главах о безопасности](security/simple-oauth2.md#password-hashing).

## Множественные модели { #multiple-models }

Ниже изложена основная идея того, как могут выглядеть эти модели с полями для паролей, а также описаны места, где они используются:

```python
from fastapi import FastAPI
from pydantic import BaseModel, EmailStr

app = FastAPI()

class UserIn(BaseModel):
    username: str
    password: str
    email: EmailStr
    full_name: str | None = None

class UserOut(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None

class UserInDB(BaseModel):
    username: str
    hashed_password: str
    email: EmailStr
    full_name: str | None = None

def fake_password_hasher(raw_password: str):
    return "supersecret" + raw_password

def fake_save_user(user_in: UserIn):
    hashed_password = fake_password_hasher(user_in.password)
    user_in_db = UserInDB(**user_in.model_dump(), hashed_password=hashed_password)
    print("User saved! ..not really")
    return user_in_db

@app.post("/user/", response_model=UserOut)
async def create_user(user_in: UserIn):
    user_saved = fake_save_user(user_in)
    return user_saved
```

### Про `**user_in.model_dump()` { #about-user-in-model-dump }

#### `.model_dump()` из Pydantic { #pydantics-model-dump }

`user_in` — это Pydantic-модель класса `UserIn`.

У Pydantic-моделей есть метод `.model_dump()`, который возвращает `dict` с данными модели.

Поэтому, если мы создадим Pydantic-объект `user_in` таким способом:

```python
user_in = UserIn(username="john", password="secret", email="john.doe@example.com")
```

и затем вызовем:

```python
user_dict = user_in.model_dump()
```

то теперь у нас есть `dict` с данными в переменной `user_dict` (это `dict` вместо объекта Pydantic-модели).

И если мы вызовем:

```python
print(user_dict)
```

мы получим Python `dict` с:

```python
{
    "username": "john",
    "password": "secret",
    "email": "john.doe@example.com",
    "full_name": None,
}
```

#### Распаковка `dict` { #unpacking-a-dict }

Если мы возьмём `dict` наподобие `user_dict` и передадим его в функцию (или класс), используя `**user_dict`, Python его "распакует". Он передаст ключи и значения `user_dict` напрямую как аргументы типа ключ-значение.

Поэтому, продолжая описанный выше пример с `user_dict`, написание такого кода:

```python
UserInDB(**user_dict)
```

будет эквивалентно:

```python
UserInDB(
    username="john",
    password="secret",
    email="john.doe@example.com",
    full_name=None,
)
```

Или, более точно, если использовать `user_dict` напрямую, с любым содержимым, которое он может иметь в будущем:

```python
UserInDB(
    username=user_dict["username"],
    password=user_dict["password"],
    email=user_dict["email"],
    full_name=user_dict["full_name"],
)
```

#### Pydantic-модель из содержимого другой { #a-pydantic-model-from-the-contents-of-another }

Как в примере выше мы получили `user_dict` из `user_in.model_dump()`, этот код:

```python
user_dict = user_in.model_dump()
UserInDB(**user_dict)
```

будет равнозначен такому:

```python
UserInDB(**user_in.model_dump())
```

...потому что `user_in.model_dump()` — это `dict`, и затем мы указываем, чтобы Python его "распаковал", когда передаём его в `UserInDB` с префиксом `**`.

Таким образом мы получаем Pydantic-модель на основе данных из другой Pydantic-модели.

#### Распаковка `dict` и дополнительные именованные аргументы { #unpacking-a-dict-and-extra-keywords }

И затем, если мы добавим дополнительный именованный аргумент `hashed_password=hashed_password` как здесь:

```python
UserInDB(**user_in.model_dump(), hashed_password=hashed_password)
```

...то в итоге получится что-то подобное:

```python
UserInDB(
    username=user_dict["username"],
    password=user_dict["password"],
    email=user_dict["email"],
    full_name=user_dict["full_name"],
    hashed_password=hashed_password,
)
```

**Предупреждение:**

Вспомогательные дополнительные функции `fake_password_hasher` и `fake_save_user` используются только для демонстрации возможного потока данных и, конечно, не обеспечивают настоящую безопасность.

## Сократите дублирование { #reduce-duplication }

Сокращение дублирования кода — это одна из главных идей **FastAPI**.

Поскольку дублирование кода повышает риск появления багов, проблем с безопасностью, проблем десинхронизации кода (когда вы обновляете код в одном месте, но не обновляете в другом), и т.д.

А все описанные выше модели используют много общих данных и дублируют названия атрибутов и типов.

Мы можем это улучшить.

Мы можем объявить модель `UserBase`, которая будет базовой для остальных моделей. И затем мы можем создать подклассы этой модели, которые будут наследовать её атрибуты (объявления типов, валидацию, и т.п.).

Все операции конвертации, валидации, документации, и т.п. будут по-прежнему работать нормально.

В этом случае мы можем объявить только различия между моделями (с `password` в чистом виде, с `hashed_password` и без пароля):

```python
from fastapi import FastAPI
from pydantic import BaseModel, EmailStr

app = FastAPI()

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None

class UserIn(UserBase):
    password: str

class UserOut(UserBase):
    pass

class UserInDB(UserBase):
    hashed_password: str

def fake_password_hasher(raw_password: str):
    return "supersecret" + raw_password

def fake_save_user(user_in: UserIn):
    hashed_password = fake_password_hasher(user_in.password)
    user_in_db = UserInDB(**user_in.model_dump(), hashed_password=hashed_password)
    print("User saved! ..not really")
    return user_in_db

@app.post("/user/", response_model=UserOut)
async def create_user(user_in: UserIn):
    user_saved = fake_save_user(user_in)
    return user_saved
```

## `Union` или `anyOf` { #union-or-anyof }

Вы можете объявить HTTP-ответ как `Union` из двух или более типов. Это означает, что HTTP-ответ может быть любым из них.

Он будет определён в OpenAPI как `anyOf`.

Для этого используйте стандартную аннотацию типов в Python [`typing.Union`](https://docs.python.org/3/library/typing.html#typing.Union):

**Примечание:**

При объявлении [`Union`](https://pydantic.dev/docs/validation/latest/concepts/unions/) сначала указывайте наиболее специфичный тип, затем менее специфичный. В примере ниже более специфичный `PlaneItem` стоит перед `CarItem` в `Union[PlaneItem, CarItem]`.

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class BaseItem(BaseModel):
    description: str
    type: str

class CarItem(BaseItem):
    type: str = "car"

class PlaneItem(BaseItem):
    type: str = "plane"
    size: int

items = {
    "item1": {"description": "All my friends drive a low rider", "type": "car"},
    "item2": {
        "description": "Music is my aeroplane, it's my aeroplane",
        "type": "plane",
        "size": 5,
    },
}

@app.get("/items/{item_id}", response_model=PlaneItem | CarItem)
async def read_item(item_id: str):
    return items[item_id]
```

### `Union` в Python 3.10 { #union-in-python-3-10 }

В этом примере мы передаём `Union[PlaneItem, CarItem]` в качестве значения аргумента `response_model`.

Поскольку мы передаём его как **значение аргумента** вместо того, чтобы поместить его в **аннотацию типа**, нам придётся использовать `Union` даже в Python 3.10.

Если оно было бы указано в аннотации типа, то мы могли бы использовать вертикальную черту как в примере:

```python
some_variable: PlaneItem | CarItem
```

Но если мы поместим это в присваивание `response_model=PlaneItem | CarItem`, мы получим ошибку, потому что Python попытается произвести **некорректную операцию** между `PlaneItem` и `CarItem` вместо того, чтобы интерпретировать это как аннотацию типа.

## Список моделей { #list-of-models }

Таким же образом вы можете объявлять HTTP-ответы, возвращающие списки объектов.

Для этого используйте стандартный `list` в Python:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str

items = [
    {"name": "Foo", "description": "There comes my hero"},
    {"name": "Red", "description": "It's my aeroplane"},
]

@app.get("/items/", response_model=list[Item])
async def read_items():
    return items
```

## Ответ с произвольным `dict` { #response-with-arbitrary-dict }

Вы также можете объявить HTTP-ответ, используя обычный произвольный `dict`, объявив только тип ключей и значений, без использования Pydantic-модели.

Это полезно, если вы заранее не знаете корректных названий полей/атрибутов (которые будут нужны при использовании Pydantic-модели).

В этом случае вы можете использовать `dict`:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/keyword-weights/", response_model=dict[str, float])
async def read_keyword_weights():
    return {"foo": 2.3, "bar": 3.4}
```

## Резюме { #recap }

Используйте несколько Pydantic-моделей и свободно применяйте наследование для каждого случая.

Вам не обязательно иметь единственную модель данных для каждой сущности, если эта сущность должна иметь возможность быть в разных "состояниях". **Пользователь** — пример такой "сущности", с состояниями, которые включают `password`, `password_hash` или отсутствие пароля.
