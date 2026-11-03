# Query-параметры { #query-parameters }

Когда вы объявляете параметры функции, которые не являются частью path-параметров, они автоматически интерпретируются как "query"-параметры.

```python
from fastapi import FastAPI

app = FastAPI()

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

@app.get("/items/")
async def read_item(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]
```

Query — это набор пар ключ-значение, которые идут после знака `?` в URL-адресе, разделенные символами `&`.

Например, в этом URL-адресе:

```
http://127.0.0.1:8000/items/?skip=0&limit=10
```

...query-параметры такие:

* `skip`: со значением `0`
* `limit`: со значением `10`

Будучи частью URL-адреса, они "естественным образом" являются строками.

Но когда вы объявляете их с использованием типов Python (в примере выше, как `int`), они конвертируются в указанный тип данных и проходят проверку на соответствие ему.

Все те же процессы, которые применяются к path-параметрам, также применяются и к query-параметрам:

* Поддержка от редактора кода (очевидно)
* "Парсинг" данных
* Валидация данных
* Автоматическая документация

## Значения по умолчанию { #defaults }

Поскольку query-параметры не являются фиксированной частью пути, они могут быть необязательными и иметь значения по умолчанию.

В примере выше значения по умолчанию равны `skip=0` и `limit=10`.

Таким образом, результат перехода по URL-адресу:

```
http://127.0.0.1:8000/items/
```

будет таким же, как если перейти по:

```
http://127.0.0.1:8000/items/?skip=0&limit=10
```

Но если вы перейдёте, например, по:

```
http://127.0.0.1:8000/items/?skip=20
```

Значения параметров в вашей функции будут:

* `skip=20`: потому что вы установили это в URL-адресе
* `limit=10`: потому что это было значение по умолчанию

## Необязательные параметры { #optional-parameters }

Аналогично, вы можете объявлять необязательные query-параметры, установив их значение по умолчанию, равное `None`:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: str, q: str | None = None):
    if q:
        return {"item_id": item_id, "q": q}
    return {"item_id": item_id}
```

В этом случае параметр функции `q` будет необязательным и будет иметь значение `None` по умолчанию.

**Подсказка:**

Также обратите внимание, что **FastAPI** достаточно умён, чтобы заметить, что path-параметр `item_id` является path-параметром, а `q` — нет, поэтому это query-параметр.

## Преобразование типа query-параметра { #query-parameter-type-conversion }

Вы также можете объявлять типы `bool`, и они будут преобразованы:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: str, q: str | None = None, short: bool = False):
    item = {"item_id": item_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item
```

В этом случае, если вы перейдёте по:

```
http://127.0.0.1:8000/items/foo?short=1
```

или

```
http://127.0.0.1:8000/items/foo?short=True
```

или

```
http://127.0.0.1:8000/items/foo?short=true
```

или

```
http://127.0.0.1:8000/items/foo?short=on
```

или

```
http://127.0.0.1:8000/items/foo?short=yes
```

или в любом другом варианте написания (в верхнем регистре, с заглавной буквой и т.п.), внутри вашей функции параметр `short` будет иметь значение `True` типа данных `bool`.

Значения вроде `0`, `false`, `off` и `no` (включая варианты с разным регистром) преобразуются в `False`.

Если `short` не указан, **FastAPI** использует его значение по умолчанию, которое в этом примере равно `False`.

Пустое значение (`?short=`) или нераспознанное значение (например, `?short=maybe`) приводит к ошибке валидации `422`.

## Несколько path-параметров и query-параметров { #multiple-path-and-query-parameters }

Вы можете объявлять несколько path-параметров и query-параметров одновременно, **FastAPI** знает, что чем является.

И вы не обязаны объявлять их в каком-либо определенном порядке.

Они будут обнаружены по именам:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(
    user_id: int, item_id: str, q: str | None = None, short: bool = False
):
    item = {"item_id": item_id, "owner_id": user_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item
```

## Обязательные query-параметры { #required-query-parameters }

Когда вы объявляете значение по умолчанию для параметра, который не является path-параметром (в этом разделе мы пока что рассмотрели только query-параметры), то он не является обязательным.

Если вы не хотите задавать конкретное значение, но хотите просто сделать параметр необязательным, установите значение по умолчанию равным `None`.

Но если вы хотите сделать query-параметр обязательным, вы можете просто не указывать значение по умолчанию:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def read_user_item(item_id: str, needy: str):
    item = {"item_id": item_id, "needy": needy}
    return item
```

Здесь query-параметр `needy` является обязательным query-параметром с типом данных `str`.

Если вы откроете в браузере URL-адрес вроде:

```
http://127.0.0.1:8000/items/foo-item
```

...без добавления обязательного параметра `needy`, вы увидите ошибку вроде:

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": [
        "query",
        "needy"
      ],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

Поскольку `needy` является обязательным параметром, вам необходимо указать его в URL-адресе:

```
http://127.0.0.1:8000/items/foo-item?needy=sooooneedy
```

...это будет работать:

```json
{
    "item_id": "foo-item",
    "needy": "sooooneedy"
}
```

И, конечно, вы можете определить некоторые параметры как обязательные, некоторые — со значением по умолчанию, а некоторые — полностью необязательные:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def read_user_item(
    item_id: str, needy: str, skip: int = 0, limit: int | None = None
):
    item = {"item_id": item_id, "needy": needy, "skip": skip, "limit": limit}
    return item
```

В этом случае есть 3 query-параметра:

* `needy`, обязательный `str`.
* `skip`, `int` со значением по умолчанию `0`.
* `limit`, необязательный `int`.

**Подсказка:**

Вы можете использовать `Enum` так же, как ранее применяли его с [Path-параметрами](path-params.md#predefined-values).
