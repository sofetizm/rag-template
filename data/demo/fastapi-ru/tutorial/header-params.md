# Header-параметры { #header-parameters }

Вы можете определить параметры заголовка таким же образом, как вы определяете параметры `Query`, `Path` и `Cookie`.

## Импорт `Header` { #import-header }

Сперва импортируйте `Header`:

```python
from typing import Annotated

from fastapi import FastAPI, Header

app = FastAPI()

@app.get("/items/")
async def read_items(user_agent: Annotated[str | None, Header()] = None):
    return {"User-Agent": user_agent}
```

## Объявление параметров `Header` { #declare-header-parameters }

Затем объявите параметры заголовка, используя ту же структуру, что и с `Path`, `Query` и `Cookie`.

Первое значение является значением по умолчанию, вы можете передать все дополнительные параметры валидации или аннотации:

```python
from typing import Annotated

from fastapi import FastAPI, Header

app = FastAPI()

@app.get("/items/")
async def read_items(user_agent: Annotated[str | None, Header()] = None):
    return {"User-Agent": user_agent}
```

**Технические детали:**

`Header` - это "родственный" класс `Path`, `Query` и `Cookie`. Он также наследуется от того же общего класса `Param`.

Но помните, что когда вы импортируете `Query`, `Path`, `Header` и другие из `fastapi`, на самом деле это функции, которые возвращают специальные классы.

**Примечание:**

Чтобы объявить заголовки, важно использовать `Header`, иначе параметры интерпретируются как query-параметры.

## Автоматическое преобразование { #automatic-conversion }

`Header` обладает небольшой дополнительной функциональностью в дополнение к тому, что предоставляют `Path`, `Query` и `Cookie`.

Большинство стандартных заголовков разделены символом "дефис", также известным как "минус" (`-`).

Но переменная вроде `user-agent` недопустима в Python.

По умолчанию `Header` преобразует символы имен параметров из символа подчеркивания (`_`) в дефис (`-`) для извлечения и документирования заголовков.

Кроме того, HTTP-заголовки не чувствительны к регистру, поэтому вы можете объявить их в стандартном стиле Python (также известном как "snake_case").

Таким образом вы можете использовать `user_agent`, как обычно, в коде Python, вместо того, чтобы вводить заглавные буквы как `User_Agent` или что-то подобное.

Если по какой-либо причине вам необходимо отключить автоматическое преобразование подчеркиваний в дефисы, установите для параметра `convert_underscores` в `Header` значение `False`:

```python
from typing import Annotated

from fastapi import FastAPI, Header

app = FastAPI()

@app.get("/items/")
async def read_items(
    strange_header: Annotated[str | None, Header(convert_underscores=False)] = None,
):
    return {"strange_header": strange_header}
```

**Внимание:**

Прежде чем установить для `convert_underscores` значение `False`, имейте в виду, что некоторые HTTP-прокси и серверы запрещают использование заголовков с подчеркиванием.

## Повторяющиеся заголовки { #duplicate-headers }

Есть возможность получать несколько заголовков с одним и тем же именем, но разными значениями.

Вы можете определить эти случаи, используя список в объявлении типа.

Вы получите все значения из повторяющегося заголовка в виде `list` Python.

Например, чтобы объявить заголовок `X-Token`, который может появляться более одного раза, вы можете написать:

```python
from typing import Annotated

from fastapi import FastAPI, Header

app = FastAPI()

@app.get("/items/")
async def read_items(x_token: Annotated[list[str] | None, Header()] = None):
    return {"X-Token values": x_token}
```

Если вы взаимодействуете с этой *операцией пути*, отправляя два HTTP-заголовка, таких как:

```
X-Token: foo
X-Token: bar
```

Ответ был бы таким:

```json
{
    "X-Token values": [
        "bar",
        "foo"
    ]
}
```

## Резюме { #recap }

Объявляйте заголовки с помощью `Header`, используя тот же общий шаблон, как при `Query`, `Path` и `Cookie`.

И не беспокойтесь о символах подчеркивания в ваших переменных, **FastAPI** позаботится об их преобразовании.
