# Тело запроса { #request-body }

Когда вам необходимо отправить данные из клиента (например, браузера) в ваш API, вы отправляете их как **тело запроса**.

Тело **запроса** — это данные, отправляемые клиентом в ваш API. Тело **ответа** — это данные, которые ваш API отправляет клиенту.

Ваш API почти всегда должен отправлять тело **ответа**. Но клиентам не обязательно всегда отправлять **тело запроса**: иногда они запрашивают только путь, возможно с некоторыми параметрами запроса, но без тела.

Чтобы объявить тело **запроса**, используйте модели [Pydantic](https://pydantic.dev/docs/), со всей их мощью и преимуществами.

**Заметка:**

Чтобы отправить данные, используйте один из методов: `POST` (чаще всего), `PUT`, `DELETE` или `PATCH`.

Отправка тела с запросом `GET` имеет неопределённое поведение в спецификациях, тем не менее это поддерживается FastAPI, но только для очень сложных/крайних случаев использования.

Поскольку это не рекомендуется, интерактивная документация со Swagger UI не будет отображать информацию для тела при использовании `GET`, а промежуточные прокси-серверы могут не поддерживать такой вариант запроса.

## Импортируйте `BaseModel` из Pydantic { #import-pydantics-basemodel }

Первое, что нужно сделать, — импортировать `BaseModel` из пакета `pydantic`:

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

app = FastAPI()

@app.post("/items/")
async def create_item(item: Item):
    return item
```

## Создайте модель данных { #create-your-data-model }

Затем опишите свою модель данных как класс, наследующийся от `BaseModel`.

Используйте стандартные типы Python для всех атрибутов:

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

app = FastAPI()

@app.post("/items/")
async def create_item(item: Item):
    return item
```

Так же, как при объявлении параметров запроса: когда атрибут модели имеет значение по умолчанию, он не обязателен. Иначе он обязателен. Используйте `None`, чтобы сделать его просто необязательным.

Например, модель выше описывает такой JSON "`object`" (или Python `dict`):

```json
{
    "name": "Foo",
    "description": "An optional description",
    "price": 45.2,
    "tax": 3.5
}
```

...так как `description` и `tax` являются необязательными (со значением по умолчанию `None`), такой JSON "`object`" тоже будет корректным:

```json
{
    "name": "Foo",
    "price": 45.2
}
```

## Объявите её как параметр { #declare-it-as-a-parameter }

Чтобы добавить её в вашу *операцию пути*, объявите её так же, как вы объявляли параметры пути и параметры запроса:

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

app = FastAPI()

@app.post("/items/")
async def create_item(item: Item):
    return item
```

...и укажите тип параметра как созданную вами модель, `Item`.

## Результаты { #results }

Всего лишь с этой аннотацией типов Python **FastAPI**:

* Считает тело запроса как JSON.
* Приведёт данные к соответствующим типам (если потребуется).
* Проведёт валидацию данных.
    * Если данные некорректны, вернёт понятную и наглядную ошибку, указывающую, где именно и что было некорректно.
* Передаст полученные данные в параметр `item`.
    * Поскольку внутри функции вы объявили его с типом `Item`, у вас будет поддержка со стороны редактора кода (автозавершение и т.п.) для всех атрибутов и их типов.
* Сгенерирует определения [JSON Schema](https://json-schema.org) для вашей модели; вы можете использовать их и в других местах, если это имеет смысл для вашего проекта.
* Эти схемы будут частью сгенерированной схемы OpenAPI и будут использоваться автоматической документацией UIs (User Interfaces - Пользовательские интерфейсы).

## Автоматическая документация { #automatic-docs }

JSON Schema ваших моделей будет частью сгенерированной схемы OpenAPI и будет отображаться в интерактивной документации API:

А также они будут использоваться в документации API внутри каждой *операции пути*, где это требуется:

## Поддержка редактора кода { #editor-support }

В вашем редакторе кода внутри функции вы получите подсказки по типам и автозавершение повсюду (этого бы не было, если бы вы получали `dict` вместо модели Pydantic):

Также вы получите проверку ошибок при некорректных операциях с типами:

Это не случайность — весь фреймворк построен вокруг такого дизайна.

И это было тщательно протестировано ещё на этапе проектирования, до реализации, чтобы убедиться, что всё будет работать со всеми редакторами.

В сам Pydantic даже были внесены некоторые изменения для поддержки этого.

Предыдущие скриншоты сделаны в [Visual Studio Code](https://code.visualstudio.com).

Но вы получите такую же поддержку редактора кода в [PyCharm](https://www.jetbrains.com/pycharm/) и большинстве других редакторов Python:

**Совет:**

Если вы используете [PyCharm](https://www.jetbrains.com/pycharm/) в качестве редактора кода, вы можете использовать плагин [Pydantic PyCharm Plugin](https://github.com/koxudaxi/pydantic-pycharm-plugin/).

Он улучшает поддержку моделей Pydantic в редакторе кода, включая:

* автозавершение
* проверки типов
* рефакторинг
* поиск
* инспекции

## Использование модели { #use-the-model }

Внутри функции вам доступны все атрибуты объекта модели напрямую:

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

app = FastAPI()

@app.post("/items/")
async def create_item(item: Item):
    item_dict = item.model_dump()
    if item.tax is not None:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    return item_dict
```

## Тело запроса + параметры пути { #request-body-path-parameters }

Вы можете одновременно объявить параметры пути и тело запроса.

**FastAPI** распознает, что параметры функции, соответствующие параметрам пути, должны быть **получены из пути**, а параметры функции, объявленные как модели Pydantic, должны быть **получены из тела запроса**.

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

app = FastAPI()

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    return {"item_id": item_id, **item.model_dump()}
```

## Тело запроса + параметры пути + параметры запроса { #request-body-path-query-parameters }

Вы также можете одновременно объявить параметры **тела**, **пути** и **запроса**.

**FastAPI** распознает каждый из них и возьмёт данные из правильного источника.

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

app = FastAPI()

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item, q: str | None = None):
    result = {"item_id": item_id, **item.model_dump()}
    if q:
        result.update({"q": q})
    return result
```

Параметры функции будут распознаны следующим образом:

* Если параметр также объявлен в **пути**, он будет использоваться как path-параметр.
* Если параметр имеет **скалярный тип** (например, `int`, `float`, `str`, `bool` и т.п.), он будет интерпретирован как параметр **запроса**.
* Если параметр объявлен как тип **модели Pydantic**, он будет интерпретирован как **тело** запроса.

**Заметка:**

FastAPI понимает, что значение `q` не является обязательным из-за значения по умолчанию `= None`.

Аннотация типов `str | None` не используется FastAPI для определения обязательности; он узнает, что параметр не обязателен, потому что у него есть значение по умолчанию `= None`.

Но добавление аннотаций типов позволит вашему редактору кода лучше вас поддерживать и обнаруживать ошибки.

## Без Pydantic { #without-pydantic }

Если вы не хотите использовать модели Pydantic, вы также можете использовать параметры **Body**. См. раздел документации [Тело запроса - Несколько параметров: Единичные значения в теле](body-multiple-params.md#singular-values-in-body).
