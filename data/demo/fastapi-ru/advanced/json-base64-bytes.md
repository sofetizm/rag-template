# JSON с байтами в Base64 { #json-with-bytes-as-base64 }

Если вашему приложению нужно принимать и отправлять JSON-данные, но при этом необходимо включать в них бинарные данные, вы можете кодировать их в base64.

## Base64 и файлы { #base64-vs-files }

Сначала рассмотрите возможность использовать [Файлы в запросе](../tutorial/request-files.md) для загрузки бинарных данных и [Пользовательский HTTP-ответ — FileResponse](./custom-response.md#fileresponse) для отправки бинарных данных вместо кодирования их в JSON.

JSON может содержать только строки в кодировке UTF-8, поэтому он не может содержать «сырые» байты.

Base64 может кодировать бинарные данные в строки, но для этого используется больше символов, чем в исходных бинарных данных, поэтому обычно это менее эффективно, чем обычные файлы.

Используйте base64 только если вам действительно нужно включать бинарные данные в JSON и вы не можете использовать файлы для этого.

## Pydantic `bytes` { #pydantic-bytes }

Вы можете объявить Pydantic-модель с полями `bytes`, а затем использовать `val_json_bytes` в конфиге модели, чтобы указать использовать base64 для *валидации* входящих JSON-данных; как часть этой валидации строка base64 будет декодирована в байты.

```python
from fastapi import FastAPI
from pydantic import BaseModel

class DataInput(BaseModel):
    description: str
    data: bytes

    model_config = {"val_json_bytes": "base64"}
# ...
app = FastAPI()

@app.post("/data")
def post_data(body: DataInput):
    content = body.data.decode("utf-8")
    return {"description": body.description, "content": content}
```

Если вы откроете `/docs`, вы увидите, что поле `data` ожидает байты, закодированные в base64:

Вы можете отправить такой HTTP-запрос:

```json
{
    "description": "Some data",
    "data": "aGVsbG8="
}
```

**Совет:**

`aGVsbG8=` — это base64-кодирование строки `hello`.

Затем Pydantic декодирует строку base64 и передаст вам исходные байты в поле `data` модели.

Вы получите такой HTTP-ответ:

```json
{
  "description": "Some data",
  "content": "hello"
}
```

## Pydantic `bytes` для выходных данных { #pydantic-bytes-for-output-data }

Вы также можете использовать поля `bytes` с `ser_json_bytes` в конфиге модели для выходных данных, и Pydantic будет *сериализовать* байты в base64 при формировании JSON-ответа.

```python
from fastapi import FastAPI
from pydantic import BaseModel
# ...
class DataOutput(BaseModel):
    description: str
    data: bytes

    model_config = {"ser_json_bytes": "base64"}
# ...
app = FastAPI()
# ...
@app.get("/data")
def get_data() -> DataOutput:
    data = "hello".encode("utf-8")
    return DataOutput(description="A plumbus", data=data)
```

## Pydantic `bytes` для входных и выходных данных { #pydantic-bytes-for-input-and-output-data }

И, конечно, вы можете использовать одну и ту же модель, настроенную на использование base64, чтобы обрабатывать и входящие данные (*валидировать*) с `val_json_bytes`, и исходящие данные (*сериализовать*) с `ser_json_bytes` при приеме и отправке JSON-данных.

```python
from fastapi import FastAPI
from pydantic import BaseModel
# ...
class DataInputOutput(BaseModel):
    description: str
    data: bytes

    model_config = {
        "val_json_bytes": "base64",
        "ser_json_bytes": "base64",
    }
# ...
app = FastAPI()
# ...
@app.post("/data-in-out")
def post_data_in_out(body: DataInputOutput) -> DataInputOutput:
    return body
```
