# Body - Множество параметров { #body-multiple-parameters }

Теперь, когда мы увидели, как использовать `Path` и `Query` параметры, давайте рассмотрим более продвинутые примеры объявления тела запроса.

## Объединение `Path`, `Query` и параметров тела запроса { #mix-path-query-and-body-parameters }

Во-первых, конечно, вы можете объединять параметры `Path`, `Query` и объявления тела запроса в своих функциях обработки, **FastAPI** автоматически определит, что с ними нужно делать.

Вы также можете объявить параметры тела запроса как необязательные, установив значение по умолчанию, равное `None`:

```python
from typing import Annotated

from fastapi import FastAPI, Path
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

@app.put("/items/{item_id}")
async def update_item(
    item_id: Annotated[int, Path(title="The ID of the item to get", ge=0, le=1000)],
    q: str | None = None,
    item: Item | None = None,
):
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})
    if item:
        results.update({"item": item})
    return results
```

**Заметка:**

Заметьте, что в данном случае параметр `item`, который будет взят из тела запроса, необязателен. Так как было установлено значение `None` по умолчанию.

## Несколько параметров тела запроса { #multiple-body-parameters }

В предыдущем примере, *операции пути* ожидали тело запроса в формате JSON, с параметрами, соответствующими атрибутам `Item`, например:

```json
{
    "name": "Foo",
    "description": "The pretender",
    "price": 42.0,
    "tax": 3.2
}
```

Но вы также можете объявить множество параметров тела запроса, например `item` и `user`:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

class User(BaseModel):
    username: str
    full_name: str | None = None

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item, user: User):
    results = {"item_id": item_id, "item": item, "user": user}
    return results
```

В этом случае **FastAPI** заметит, что в функции есть более одного параметра тела (два параметра, которые являются Pydantic-моделями).

Таким образом, имена параметров будут использоваться в качестве ключей (имён полей) в теле запроса, и будет ожидаться запрос следующего формата:

```json
{
    "item": {
        "name": "Foo",
        "description": "The pretender",
        "price": 42.0,
        "tax": 3.2
    },
    "user": {
        "username": "dave",
        "full_name": "Dave Grohl"
    }
}
```

**Заметка:**

Обратите внимание, что хотя параметр `item` был объявлен таким же способом, как и раньше, теперь предполагается, что он находится внутри тела с ключом `item`.

**FastAPI** сделает автоматическое преобразование из запроса, так что параметр `item` получит своё конкретное содержимое, и то же самое происходит с пользователем `user`.

Произойдёт проверка составных данных, и создание документации в схеме OpenAPI и автоматических документах.

## Отдельные значения в теле запроса { #singular-values-in-body }

Точно так же, как `Query` и `Path` используются для определения дополнительных данных для query и path параметров, **FastAPI** предоставляет аналогичный инструмент - `Body`.

Например, расширяя предыдущую модель, вы можете решить, что вам нужен еще один ключ `importance` в том же теле запроса, помимо параметров `item` и `user`.

Если вы объявите его без указания, какой именно объект (Path, Query, Body и т.п.) ожидаете, то, поскольку это является простым типом данных, **FastAPI** будет считать, что это query-параметр.

Но вы можете указать **FastAPI** обрабатывать его, как ещё один ключ тела запроса, используя `Body`:

```python
from typing import Annotated

from fastapi import Body, FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

class User(BaseModel):
    username: str
    full_name: str | None = None

@app.put("/items/{item_id}")
async def update_item(
    item_id: int, item: Item, user: User, importance: Annotated[int, Body()]
):
    results = {"item_id": item_id, "item": item, "user": user, "importance": importance}
    return results
```

В этом случае, **FastAPI** будет ожидать тело запроса в формате:

```json
{
    "item": {
        "name": "Foo",
        "description": "The pretender",
        "price": 42.0,
        "tax": 3.2
    },
    "user": {
        "username": "dave",
        "full_name": "Dave Grohl"
    },
    "importance": 5
}
```

И всё будет работать так же - преобразование типов данных, валидация, документирование и т.д.

## Множество body и query параметров { #multiple-body-params-and-query }

Конечно, вы также можете объявлять query-параметры в любое время, дополнительно к любым body-параметрам.

Поскольку по умолчанию, отдельные значения интерпретируются как query-параметры, вам не нужно явно добавлять `Query`, вы можете просто сделать так:

```python
q: str | None = None
```

Например:

```python
from typing import Annotated

from fastapi import Body, FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

class User(BaseModel):
    username: str
    full_name: str | None = None

@app.put("/items/{item_id}")
async def update_item(
    *,
    item_id: int,
    item: Item,
    user: User,
    importance: Annotated[int, Body(gt=0)],
    q: str | None = None,
):
    results = {"item_id": item_id, "item": item, "user": user, "importance": importance}
    if q:
        results.update({"q": q})
    return results
```

**Заметка:**

`Body` также имеет все те же дополнительные параметры валидации и метаданных, как у `Query`, `Path` и других, которые вы увидите позже.

## Вложить один body-параметр { #embed-a-single-body-parameter }

Предположим, у вас есть только один body-параметр `item` из Pydantic-модели `Item`.

По умолчанию, **FastAPI** ожидает получить тело запроса напрямую.

Но если вы хотите чтобы он ожидал JSON с ключом `item` с содержимым модели внутри, также как это происходит при объявлении дополнительных body-параметров, вы можете использовать специальный параметр `embed` у типа `Body`:

```python
item: Annotated[Item, Body(embed=True)]
```

так же, как в этом примере:

```python
from typing import Annotated

from fastapi import Body, FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Annotated[Item, Body(embed=True)]):
    results = {"item_id": item_id, "item": item}
    return results
```

В этом случае **FastAPI** будет ожидать тело запроса в формате:

```json
{
    "item": {
        "name": "Foo",
        "description": "The pretender",
        "price": 42.0,
        "tax": 3.2
    }
}
```

вместо этого:

```json
{
    "name": "Foo",
    "description": "The pretender",
    "price": 42.0,
    "tax": 3.2
}
```

## Резюме { #recap }

Вы можете добавлять несколько body-параметров вашей *функции-обработчика пути*, несмотря даже на то, что запрос может содержать только одно тело.

Но **FastAPI** справится с этим, предоставит правильные данные в вашей функции, а также сделает валидацию и документацию правильной схемы *операции пути*.

Вы также можете объявить отдельные значения для получения в рамках тела запроса.

И вы можете настроить **FastAPI** таким образом, чтобы включить тело запроса в ключ, даже если объявлен только один параметр.
