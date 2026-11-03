# Глобальные зависимости { #global-dependencies }

Для некоторых типов приложений может потребоваться добавить зависимости ко всему приложению.

Подобно тому, как вы можете [добавлять `dependencies` (зависимости) в *декораторах операций пути*](dependencies-in-path-operation-decorators.md), вы можете добавлять зависимости сразу ко всему `FastAPI` приложению.

В этом случае они будут применяться ко всем *операциям пути* в приложении:

```python
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException

async def verify_token(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")

async def verify_key(x_key: Annotated[str, Header()]):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key

app = FastAPI(dependencies=[Depends(verify_token), Depends(verify_key)])

@app.get("/items/")
async def read_items():
    return [{"item": "Portal Gun"}, {"item": "Plumbus"}]

@app.get("/users/")
async def read_users():
    return [{"username": "Rick"}, {"username": "Morty"}]
```

Все способы [добавления `dependencies` (зависимостей) в *декораторах операций пути*](dependencies-in-path-operation-decorators.md) по-прежнему применимы, но в данном случае зависимости применяются ко всем *операциям пути* приложения.

## Зависимости для групп *операций пути* { #dependencies-for-groups-of-path-operations }

Позднее, читая о том, как структурировать более крупные приложения ([Более крупные приложения - несколько файлов](../../tutorial/bigger-applications.md)), возможно, состоящие из нескольких файлов, вы узнаете, как объявить один параметр `dependencies` для целой группы *операций пути*.
