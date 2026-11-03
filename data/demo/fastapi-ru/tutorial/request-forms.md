# Данные формы { #form-data }

Когда вам нужно получить поля формы вместо JSON, вы можете использовать `Form`.

**Примечание:**

Чтобы использовать формы, сначала установите [`python-multipart`](https://github.com/Kludex/python-multipart).

Добавьте его в свой проект:

```console
$ uv add python-multipart
```

## Импорт `Form` { #import-form }

Импортируйте `Form` из `fastapi`:

```python
from typing import Annotated

from fastapi import FastAPI, Form

app = FastAPI()

@app.post("/login/")
async def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    return {"username": username}
```

## Определение параметров `Form` { #define-form-parameters }

Создайте параметры формы так же, как это делается для `Body` или `Query`:

```python
from typing import Annotated

from fastapi import FastAPI, Form

app = FastAPI()

@app.post("/login/")
async def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    return {"username": username}
```

Например, в одном из способов использования спецификации OAuth2 (называемом «password flow» - аутентификация по паролю) требуется отправить `username` и `password` в виде полей формы.

спецификация требует, чтобы поля были строго названы `username` и `password` и отправлялись как поля формы, а не JSON.

С помощью `Form` вы можете объявить те же настройки, что и с `Body` (и `Query`, `Path`, `Cookie`), включая валидацию, примеры, псевдоним (например, `user-name` вместо `username`) и т.д.

**Примечание:**

`Form` — это класс, который наследуется непосредственно от `Body`.

**Подсказка:**

Чтобы объявлять тела формы, вам нужно явно использовать `Form`, иначе параметры будут интерпретированы как параметры строки запроса или параметры тела запроса (JSON).

## Булевы поля формы { #boolean-form-fields }

При отправке HTML-форм браузеры пропускают неотмеченные флажки. Объявите булев параметр формы со значением по умолчанию `False`, чтобы получать `False`, когда флажок не отмечен:

```python
from typing import Annotated

from fastapi import FastAPI, Form

app = FastAPI()

@app.post("/preferences/")
async def update_preferences(subscribe: Annotated[bool, Form()] = False):
    return {"subscribe": subscribe}
```

Отмеченный флажок отправляет своё значение, которое по умолчанию равно `"on"`. **FastAPI** принимает `"on"` как `True`.

## О «полях формы» { #about-form-fields }

Обычно способ, которым HTML-формы (`<form></form>`) отправляют данные на сервер, использует «специальное» кодирование для этих данных, отличное от JSON.

**FastAPI** гарантирует, что эти данные будут прочитаны из нужного места, а не из JSON.

**Технические детали:**

Данные из форм обычно кодируются с использованием «типа содержимого» `application/x-www-form-urlencoded`.

Но когда форма содержит файлы, она кодируется как `multipart/form-data`. О работе с файлами вы прочтёте в следующей главе.

Вы можете использовать `Form(media_type="multipart/form-data")`, чтобы описать составную форму в OpenAPI. При объединении параметров или моделей формы достаточно указать это для одного параметра.

Если вы хотите узнать больше про эти кодировки и поля формы, обратитесь к [MDN (Mozilla Developer Network - Сеть разработчиков Mozilla) веб-документации для `POST`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/POST).

**Предупреждение:**

Вы можете объявлять несколько параметров `Form` в *операции пути*, но вы не можете одновременно объявлять поля `Body`, которые вы ожидаете получить в виде JSON, так как HTTP-запрос будет иметь тело, закодированное с использованием `application/x-www-form-urlencoded`, а не `application/json`.

Это не ограничение **FastAPI**, это часть протокола HTTP.

## Резюме { #recap }

Используйте `Form` для объявления входных параметров данных формы.
