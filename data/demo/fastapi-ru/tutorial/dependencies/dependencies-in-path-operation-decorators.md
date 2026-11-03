# Зависимости в декораторах операции пути { #dependencies-in-path-operation-decorators }

В некоторых случаях, возвращаемое значение зависимости не используется внутри *функции операции пути*.

Или же зависимость не возвращает никакого значения.

Но вам всё-таки нужно, чтобы она выполнилась.

Для таких ситуаций, вместо объявления *функции операции пути* с параметром `Depends`, вы можете добавить список зависимостей `dependencies` в *декоратор операции пути*.

## Добавление `dependencies` (зависимостей) в *декоратор операции пути* { #add-dependencies-to-the-path-operation-decorator }

*Декоратор операции пути* получает необязательный аргумент `dependencies`.

Это должен быть `list` состоящий из `Depends()`:

```python
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI()

async def verify_token(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")

async def verify_key(x_key: Annotated[str, Header()]):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key

@app.get("/items/", dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]
```

Зависимости из dependencies выполнятся так же, как и обычные зависимости. Но их значения (если они были) не будут переданы в *функцию операции пути*.

**Подсказка:**

Некоторые редакторы кода определяют неиспользуемые параметры функций и подсвечивают их как ошибку.

Использование `dependencies` в *декораторе операции пути* гарантирует выполнение зависимостей, избегая при этом предупреждений редактора кода и других инструментов.

Это также должно помочь предотвратить путаницу у начинающих разработчиков, которые видят неиспользуемые параметры в коде и могут подумать что в них нет необходимости.

**Примечание:**

В этом примере мы используем выдуманные пользовательские HTTP-заголовки `X-Key` и `X-Token`.

Но в реальных проектах, при внедрении системы безопасности, вы получите больше пользы используя интегрированные [средства защиты (следующая глава)](../security/index.md).

## Ошибки в зависимостях и возвращаемые значения { #dependencies-errors-and-return-values }

Вы можете использовать те же *функции* зависимостей, что и обычно.

### Требования к зависимостям { #dependency-requirements }

Они могут объявлять требования к запросу (например HTTP-заголовки) или другие подзависимости:

```python
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI()

async def verify_token(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")

async def verify_key(x_key: Annotated[str, Header()]):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key

@app.get("/items/", dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]
```

### Вызов исключений { #raise-exceptions }

Зависимости из dependencies могут вызывать исключения с помощью `raise`, как и обычные зависимости:

```python
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI()

async def verify_token(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")

async def verify_key(x_key: Annotated[str, Header()]):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key

@app.get("/items/", dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]
```

### Возвращаемые значения { #return-values }

И они могут возвращать значения или нет, эти значения использоваться не будут.

Таким образом, вы можете переиспользовать обычную зависимость (возвращающую значение), которую вы уже используете где-то в другом месте, и хотя значение не будет использоваться, зависимость будет выполнена:

```python
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI()

async def verify_token(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")

async def verify_key(x_key: Annotated[str, Header()]):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key

@app.get("/items/", dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]
```

## Зависимости для группы *операций путей* { #dependencies-for-a-group-of-path-operations }

Позже, читая о том как структурировать большие приложения ([Большие приложения — несколько файлов](../../tutorial/bigger-applications.md)), возможно, многофайловые, вы узнаете как объявить единый параметр `dependencies` для всей группы *операций путей*.

## Глобальные Зависимости { #global-dependencies }

Далее мы увидим, как можно добавить dependencies для всего `FastAPI` приложения, так чтобы они применялись к каждой *операции пути*.
