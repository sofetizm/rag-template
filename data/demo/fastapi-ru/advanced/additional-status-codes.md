# Дополнительные статус-коды { #additional-status-codes }

По умолчанию **FastAPI** будет возвращать ответы, используя `JSONResponse`, помещая содержимое, которое вы возвращаете из вашей *операции пути*, внутрь этого `JSONResponse`.

Он будет использовать статус-код по умолчанию или тот, который вы укажете в вашей *операции пути*.

## Дополнительные статус-коды { #additional-status-codes_1 }

Если вы хотите возвращать дополнительные статус-коды помимо основного, вы можете сделать это, возвращая `Response` напрямую, например `JSONResponse`, и устанавливая дополнительный статус-код напрямую.

Например, предположим, что вы хотите иметь *операцию пути*, которая позволяет обновлять элементы и возвращает HTTP статус-код 200 «OK» при успешном выполнении.

Но вы также хотите, чтобы она принимала новые элементы. И если элементы ранее не существовали, она создаёт их и возвращает HTTP статус-код 201 «Created».

Чтобы добиться этого, импортируйте `JSONResponse` и верните туда свой контент напрямую, установив нужный вам `status_code`:

```python
from typing import Annotated

from fastapi import Body, FastAPI, status
from fastapi.responses import JSONResponse

app = FastAPI()

items = {"foo": {"name": "Fighters", "size": 6}, "bar": {"name": "Tenders", "size": 3}}

@app.put("/items/{item_id}")
async def upsert_item(
    item_id: str,
    name: Annotated[str | None, Body()] = None,
    size: Annotated[int | None, Body()] = None,
):
    if item_id in items:
        item = items[item_id]
        item["name"] = name
        item["size"] = size
        return item
    else:
        item = {"name": name, "size": size}
        items[item_id] = item
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=item)
```

**Внимание:**

Когда вы возвращаете `Response` напрямую, как в примере выше, он будет возвращён как есть.

Он не будет сериализован с помощью модели и т.п.

Убедитесь, что в нём именно те данные, которые вы хотите, и что значения являются валидным JSON (если вы используете `JSONResponse`).

**Технические детали:**

Вы также можете использовать `from starlette.responses import JSONResponse`.

**FastAPI** предоставляет тот же `starlette.responses` через `fastapi.responses` просто для вашего удобства как разработчика. Но большинство доступных Response-классов приходят напрямую из Starlette. То же самое со `status`.

## OpenAPI и документация API { #openapi-and-api-docs }

Если вы возвращаете дополнительные статус-коды и ответы напрямую, они не будут включены в схему OpenAPI (документацию API), потому что у FastAPI нет способа заранее знать, что вы собираетесь вернуть.

Но вы можете задокументировать это в своём коде, используя: [Дополнительные ответы](additional-responses.md).
