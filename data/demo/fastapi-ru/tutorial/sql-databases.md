# SQL (реляционные) базы данных { #sql-relational-databases }

**FastAPI** не требует использовать SQL (реляционную) базу данных. Но вы можете использовать **любую базу данных**, которую хотите.

Здесь мы рассмотрим пример с использованием [SQLModel](https://sqlmodel.tiangolo.com/).

**SQLModel** построен поверх [SQLAlchemy](https://www.sqlalchemy.org/) и Pydantic. Его создал тот же автор, что и **FastAPI**, чтобы он идеально подходил для приложений FastAPI, которым нужны **SQL базы данных**.

**Подсказка:**

Вы можете использовать любую другую библиотеку для работы с SQL или NoSQL базами данных (иногда их называют "ORMs" (Object Relational Mapper - Объектно-реляционный маппер: красивый термин для библиотеки, где некоторые классы представляют SQL-таблицы, а экземпляры представляют строки в этих таблицах)), FastAPI ничего не навязывает. 😎

Так как SQLModel основан на SQLAlchemy, вы можете легко использовать **любую поддерживаемую** SQLAlchemy базу данных (а значит, и поддерживаемую SQLModel), например:

* PostgreSQL
* MySQL
* SQLite
* Oracle
* Microsoft SQL Server, и т.д.

В этом примере мы будем использовать **SQLite**, потому что она использует один файл и имеет встроенную поддержку в Python. Так что вы можете скопировать этот пример и запустить его как есть.

Позже, для продакшн-приложения, возможно, вы захотите использовать серверную базу данных, например **PostgreSQL**.

**Подсказка:**

Существует официальный генератор проектов на **FastAPI** и **PostgreSQL**, включающий frontend и другие инструменты: [https://github.com/fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template)

Это очень простое и короткое руководство. Если вы хотите узнать больше о базах данных в целом, об SQL или о более продвинутых возможностях, обратитесь к [документации SQLModel](https://sqlmodel.tiangolo.com/).

## Установка `SQLModel` { #install-sqlmodel }

Добавьте `sqlmodel` в свой проект:

```console
$ uv add sqlmodel
---> 100%
```

## Создание приложения с единственной моделью { #create-the-app-with-a-single-model }

Сначала мы создадим самую простую первую версию приложения с одной моделью **SQLModel**.

Позже мы улучшим его, повысив безопасность и универсальность, добавив **несколько моделей**. 🤓

### Создание моделей { #create-models }

Импортируйте `SQLModel` и создайте модель базы данных:

```python
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
    secret_name: str
```

Класс `Hero` очень похож на модель Pydantic (фактически, под капотом, это и есть модель Pydantic).

Есть несколько отличий:

* `table=True` сообщает SQLModel, что это *модель-таблица*, она должна представлять **таблицу** в SQL базе данных, это не просто *модель данных* (как обычный класс Pydantic).

* `Field(primary_key=True)` сообщает SQLModel, что `id` — это **первичный ключ** в SQL базе данных (подробнее о первичных ключах SQL можно узнать в документации SQLModel).

    **Примечание:** Мы используем `int | None` для поля первичного ключа, чтобы в Python-коде можно было *создать объект без `id`* (`id=None`), предполагая, что база данных *сгенерирует его при сохранении*. SQLModel понимает, что база данных предоставит `id`, и *определяет столбец как `INTEGER` (не `NULL`)* в схеме базы данных. См. [документацию SQLModel о первичных ключах](https://sqlmodel.tiangolo.com/tutorial/create-db-and-table/#primary-key-id) для подробностей.

* `Field(index=True)` сообщает SQLModel, что нужно создать **SQL индекс** для этого столбца, что позволит быстрее выполнять выборки при чтении данных, отфильтрованных по этому столбцу.

    SQLModel будет знать, что объявленное как `str` станет SQL-столбцом типа `TEXT` (или `VARCHAR`, в зависимости от базы данных).

### Создание Engine { #create-an-engine }

Объект `engine` в SQLModel (под капотом это `engine` из SQLAlchemy) **удерживает соединения** с базой данных.

У вас должен быть **один объект `engine`** для всей кодовой базы, чтобы подключаться к одной и той же базе данных.

```python
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)
```

Параметр `check_same_thread=False` позволяет FastAPI использовать одну и ту же базу данных SQLite в разных потоках. Это необходимо, так как **один запрос** может использовать **больше одного потока** (например, в зависимостях).

Не волнуйтесь, с такой структурой кода мы позже обеспечим использование **одной сессии SQLModel на запрос**, по сути именно этого и добивается `check_same_thread`.

### Создание таблиц { #create-the-tables }

Далее мы добавим функцию, которая использует `SQLModel.metadata.create_all(engine)`, чтобы **создать таблицы** для всех *моделей-таблиц*.

```python
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
```

### Создание зависимости Session { #create-a-session-dependency }

**`Session`** хранит **объекты в памяти** и отслеживает необходимые изменения в данных, затем **использует `engine`** для общения с базой данных.

Мы создадим **зависимость** FastAPI с `yield`, которая будет предоставлять новую `Session` для каждого запроса. Это и обеспечивает использование одной сессии на запрос. 🤓

Затем мы создадим объявленную (`Annotated`) зависимость `SessionDep`, чтобы упростить остальной код, который будет использовать эту зависимость.

```python
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
```

### Создание таблиц базы данных при старте { #create-database-tables-on-startup }

Мы создадим таблицы базы данных при запуске приложения.

```python
app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
```

Здесь мы создаём таблицы в обработчике события запуска приложения.

Для продакшн вы, вероятно, будете использовать скрипт миграций, который выполняется до запуска приложения. 🤓

**Подсказка:**

В SQLModel появятся утилиты миграций — обёртки над Alembic, но пока вы можете использовать [Alembic](https://alembic.sqlalchemy.org/en/latest/) напрямую.

### Создание героя (Hero) { #create-a-hero }

Так как каждая модель SQLModel также является моделью Pydantic, вы можете использовать её в тех же **аннотациях типов**, в которых используете модели Pydantic.

Например, если вы объявите параметр типа `Hero`, он будет прочитан из **JSON-тела запроса**.

Аналогично вы можете объявить её как **тип возвращаемого значения** функции, и тогда форма данных отобразится в автоматически сгенерированном UI документации API.

```python
@app.post("/heroes/")
def create_hero(hero: Hero, session: SessionDep) -> Hero:
    session.add(hero)
    session.commit()
    session.refresh(hero)
    return hero
```

Здесь мы используем зависимость `SessionDep` (это `Session`), чтобы добавить нового `Hero` в экземпляр `Session`, зафиксировать изменения в базе данных, обновить данные в `hero` и затем вернуть его.

### Чтение героев { #read-heroes }

Мы можем **читать** записи `Hero` из базы данных с помощью `select()`. Можно добавить `limit` и `offset` для постраничного вывода результатов.

```python
@app.get("/heroes/")
def read_heroes(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Hero]:
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes
```

### Чтение одного героя { #read-one-hero }

Мы можем **прочитать** одного `Hero`.

```python
@app.get("/heroes/{hero_id}")
def read_hero(hero_id: int, session: SessionDep) -> Hero:
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero
```

### Удаление героя { #delete-a-hero }

Мы также можем **удалить** `Hero`.

```python
@app.delete("/heroes/{hero_id}")
def delete_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)
    session.commit()
    return {"ok": True}
```

### Запуск приложения { #run-the-app }

Вы можете запустить приложение:

```console
$ uv run fastapi dev

INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Затем перейдите в UI `/docs`. Вы увидите, что **FastAPI** использует эти **модели** для **документирования** API, а также для **сериализации** и **валидации** данных.

## Обновление приложения с несколькими моделями { #update-the-app-with-multiple-models }

Теперь давайте немного **отрефакторим** приложение, чтобы повысить **безопасность** и **универсальность**.

Если вы посмотрите на предыдущую версию, в UI видно, что до сих пор клиент мог сам задавать `id` создаваемого `Hero`. 😱

Так делать нельзя, иначе они могли бы перезаписать `id`, который уже присвоен в БД. Решение по `id` должно приниматься **бэкендом** или **базой данных**, а **не клиентом**.

Кроме того, мы создаём для героя `secret_name`, но пока что возвращаем его повсюду — это не очень **секретно**... 😅

Мы исправим это, добавив несколько **дополнительных моделей**. Здесь SQLModel раскроется во всей красе. ✨

### Создание нескольких моделей { #create-multiple-models }

В **SQLModel** любая модель с `table=True` — это **модель-таблица**.

Любая модель без `table=True` — это **модель данных**, по сути обычная модель Pydantic (с парой небольших дополнений). 🤓

С SQLModel мы можем использовать **наследование**, чтобы **избежать дублирования** полей.

#### `HeroBase` — базовый класс { #herobase-the-base-class }

Начнём с модели `HeroBase`, которая содержит **общие поля** для всех моделей:

* `name`
* `age`

```python
class HeroBase(SQLModel):
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
```

#### `Hero` — *модель-таблица* { #hero-the-table-model }

Далее создадим `Hero`, фактическую *модель-таблицу*, с **дополнительными полями**, которых может не быть в других моделях:

* `id`
* `secret_name`

Так как `Hero` наследуется от `HeroBase`, он **также** имеет **поля**, объявленные в `HeroBase`, поэтому все поля `Hero`:

* `id`
* `name`
* `age`
* `secret_name`

```python
class HeroBase(SQLModel):
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)

class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    secret_name: str
```

#### `HeroPublic` — публичная *модель данных* { #heropublic-the-public-data-model }

Далее мы создадим модель `HeroPublic`, именно она будет **возвращаться** клиентам API.

У неё те же поля, что и у `HeroBase`, поэтому она не включает `secret_name`.

Наконец-то личность наших героев защищена! 🥷

Также здесь заново объявляется `id: int`. Тем самым мы заключаем **контракт** с клиентами API: они всегда могут рассчитывать, что поле `id` присутствует и это `int` (никогда не `None`).

**Подсказка:**

Гарантия того, что в модели ответа значение всегда присутствует и это `int` (не `None`), очень полезна для клиентов API — так можно писать гораздо более простой код.

Кроме того, **автоматически сгенерированные клиенты** будут иметь более простые интерфейсы, и разработчикам, взаимодействующим с вашим API, будет работать значительно комфортнее. 😎

Все поля `HeroPublic` такие же, как в `HeroBase`, а `id` объявлен как `int` (не `None`):

* `id`
* `name`
* `age`

```python
class HeroBase(SQLModel):
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)

class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    secret_name: str

class HeroPublic(HeroBase):
    id: int
```

#### `HeroCreate` — *модель данных* для создания героя { #herocreate-the-data-model-to-create-a-hero }

Теперь создадим модель `HeroCreate`, она будет **валидировать** данные от клиентов.

У неё те же поля, что и у `HeroBase`, а также есть `secret_name`.

Теперь, когда клиенты **создают нового героя**, они будут отправлять `secret_name`, он сохранится в базе данных, но не будет возвращаться клиентам в API.

**Подсказка:**

Так следует обрабатывать **пароли**: принимать их, но не возвращать в API.

Также перед сохранением значения паролей нужно **хэшировать**, **никогда не храните их в открытом виде**.

Поля `HeroCreate`:

* `name`
* `age`
* `secret_name`

```python
class HeroBase(SQLModel):
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)

class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    secret_name: str

class HeroPublic(HeroBase):
    id: int

class HeroCreate(HeroBase):
    secret_name: str
```

#### `HeroUpdate` — *модель данных* для обновления героя { #heroupdate-the-data-model-to-update-a-hero }

В предыдущей версии приложения у нас не было способа **обновлять героя**, но теперь, с **несколькими моделями**, мы можем это сделать. 🎉

*Модель данных* `HeroUpdate` особенная: у неё **те же поля**, что и для создания нового героя, но все поля **необязательные** (у всех есть значение по умолчанию). Таким образом, при обновлении героя можно отправлять только те поля, которые нужно изменить.

Поскольку **фактически меняются все поля** (их тип теперь включает `None`, и по умолчанию они равны `None`), нам нужно **переобъявить** их.

Наследоваться от `HeroBase` не обязательно, так как мы заново объявляем все поля. Я оставлю наследование для единообразия, но это не необходимо. Скорее дело вкуса. 🤷

Поля `HeroUpdate`:

* `name`
* `age`
* `secret_name`

```python
class HeroBase(SQLModel):
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)

class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    secret_name: str

class HeroPublic(HeroBase):
    id: int

class HeroCreate(HeroBase):
    secret_name: str

class HeroUpdate(HeroBase):
    name: str | None = None
    age: int | None = None
    secret_name: str | None = None
```

### Создание с `HeroCreate` и возврат `HeroPublic` { #create-with-herocreate-and-return-a-heropublic }

Теперь, когда у нас есть **несколько моделей**, мы можем обновить части приложения, которые их используют.

Мы получаем в запросе *модель данных* `HeroCreate` и на её основе создаём *модель-таблицу* `Hero`.

Новая *модель-таблица* `Hero` будет иметь поля, отправленные клиентом, а также `id`, сгенерированный базой данных.

Затем возвращаем из функции ту же *модель-таблицу* `Hero` как есть. Но так как мы объявили `response_model` с *моделью данных* `HeroPublic`, **FastAPI** использует `HeroPublic` для валидации и сериализации данных.

```python
@app.post("/heroes/", response_model=HeroPublic)
def create_hero(hero: HeroCreate, session: SessionDep):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero
```

**Подсказка:**

Теперь мы используем `response_model=HeroPublic` вместо **аннотации типа возвращаемого значения** `-> HeroPublic`, потому что фактически возвращаемое значение — это *не* `HeroPublic`.

Если бы мы объявили `-> HeroPublic`, ваш редактор кода и линтер справедливо пожаловались бы, что вы возвращаете `Hero`, а не `HeroPublic`.

Объявляя модель в `response_model`, мы говорим **FastAPI** сделать своё дело, не вмешиваясь в аннотации типов и работу редактора кода и других инструментов.

### Чтение героев с `HeroPublic` { #read-heroes-with-heropublic }

Аналогично мы можем **читать** `Hero` — снова используем `response_model=list[HeroPublic]`, чтобы данные валидировались и сериализовались корректно.

```python
@app.get("/heroes/", response_model=list[HeroPublic])
def read_heroes(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes
```

### Чтение одного героя с `HeroPublic` { #read-one-hero-with-heropublic }

Мы можем **прочитать** одного героя:

```python
@app.get("/heroes/{hero_id}", response_model=HeroPublic)
def read_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero
```

### Обновление героя с `HeroUpdate` { #update-a-hero-with-heroupdate }

Мы можем **обновить героя**. Для этого используем HTTP операцию `PATCH`.

В коде мы получаем `dict` со всеми данными, отправленными клиентом — **только с данными, отправленными клиентом**, исключая любые значения, которые были бы там лишь как значения по умолчанию. Для этого мы используем `exclude_unset=True`. Это главный трюк. 🪄

Затем мы используем `hero_db.sqlmodel_update(hero_data)`, чтобы обновить `hero_db` данными из `hero_data`.

```python
@app.patch("/heroes/{hero_id}", response_model=HeroPublic)
def update_hero(hero_id: int, hero: HeroUpdate, session: SessionDep):
    hero_db = session.get(Hero, hero_id)
    if not hero_db:
        raise HTTPException(status_code=404, detail="Hero not found")
    hero_data = hero.model_dump(exclude_unset=True)
    hero_db.sqlmodel_update(hero_data)
    session.add(hero_db)
    session.commit()
    session.refresh(hero_db)
    return hero_db
```

### Снова удаление героя { #delete-a-hero-again }

Операция **удаления** героя остаётся практически прежней.

Желание *«отрефакторить всё»* на этот раз останется неудовлетворённым. 😅

```python
@app.delete("/heroes/{hero_id}")
def delete_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)
    session.commit()
    return {"ok": True}
```

### Снова запустим приложение { #run-the-app-again }

Вы можете снова запустить приложение:

```console
$ uv run fastapi dev

INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Если вы перейдёте в UI API `/docs`, вы увидите, что он обновился: теперь при создании героя он не ожидает получить `id` от клиента и т.д.

## Резюме { #recap }

Вы можете использовать [**SQLModel**](https://sqlmodel.tiangolo.com/) для взаимодействия с SQL базой данных и упростить код с помощью *моделей данных* и *моделей-таблиц*.

Гораздо больше вы можете узнать в документации **SQLModel**, там есть более подробное мини-[руководство по использованию SQLModel с **FastAPI**](https://sqlmodel.tiangolo.com/tutorial/fastapi/). 🚀
