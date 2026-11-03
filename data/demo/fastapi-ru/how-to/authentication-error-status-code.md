# Использование старых статус-кодов ошибок аутентификации 403 { #use-old-403-authentication-error-status-codes }

До версии FastAPI `0.122.0`, когда встроенные утилиты безопасности возвращали ошибку клиенту после неудачной аутентификации, они использовали HTTP статус-код `403 Forbidden`.

Начиная с версии FastAPI `0.122.0`, используется более подходящий HTTP статус-код `401 Unauthorized`, и в ответе возвращается имеющий смысл HTTP-заголовок `WWW-Authenticate` в соответствии со спецификациями HTTP, [RFC 7235](https://datatracker.ietf.org/doc/html/rfc7235#section-3.1), [RFC 9110](https://datatracker.ietf.org/doc/html/rfc9110#name-401-unauthorized).

Но если по какой-то причине ваши клиенты зависят от старого поведения, вы можете вернуть его, переопределив метод `make_not_authenticated_error` в ваших Security-классах.

Например, вы можете создать подкласс `HTTPBearer`, который будет возвращать ошибку `403 Forbidden` вместо стандартной `401 Unauthorized`:

```python
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

app = FastAPI()

class HTTPBearer403(HTTPBearer):
    def make_not_authenticated_error(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated"
        )

CredentialsDep = Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer403())]

@app.get("/me")
def read_me(credentials: CredentialsDep):
    return {"message": "You are authenticated", "token": credentials.credentials}
```

**Совет:**

Обратите внимание, что функция возвращает экземпляр исключения, не вызывает его. Выброс выполняется остальным внутренним кодом.
