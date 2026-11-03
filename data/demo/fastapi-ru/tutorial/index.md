# Учебник - Руководство пользователя { #tutorial-user-guide }

This tutorial shows you how to use **FastAPI** with most of its features, step by step.

Каждый раздел постепенно основывается на предыдущих, но структура разделяет темы, так что вы можете сразу перейти к нужной теме для решения ваших конкретных задач по API.

Он также создан как справочник на будущее, чтобы вы могли вернуться и посмотреть именно то, что вам нужно.

## Запустите код { #run-the-code }

Все блоки кода можно копировать и использовать напрямую (это действительно протестированные файлы Python).

Чтобы запустить любой из примеров, скопируйте код в файл `main.py` и запустите `fastapi dev` с помощью `uv run`:

```console
$ uv run fastapi dev

   FastAPI   Starting development server 🚀

             Searching for package file structure from directories
             with __init__.py files
             Importing from /home/user/code/awesomeapp

    module   🐍 main.py

      code   Importing the FastAPI app object from the module with
             the following code:

             from main import app

       app   Using import string: main:app

    server   Server started at http://127.0.0.1:8000
    server   Documentation at http://127.0.0.1:8000/docs

       tip   Running in development mode, for production use:
             fastapi run

             Logs:

      INFO   Will watch for changes in these directories:
             ['/home/user/code/awesomeapp']
      INFO   Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C
             to quit)
      INFO   Started reloader process [383138] using WatchFiles
      INFO   Started server process [383153]
      INFO   Waiting for application startup.
      INFO   Application startup complete.
```

**НАСТОЯТЕЛЬНО рекомендуется** написать или скопировать код, отредактировать его и запустить локально.

Использование кода в вашем редакторе кода — это то, что действительно показывает преимущества FastAPI: вы увидите, как мало кода нужно написать, все проверки типов, автозавершение и т.д.

---

## Установка FastAPI { #install-fastapi }

Первый шаг — настроить ваш проект и добавить FastAPI.

Установите [`uv`](https://docs.astral.sh/uv/getting-started/installation/), затем создайте проект и добавьте FastAPI:

```console
$ uv init awesome-project --bare
$ cd awesome-project
$ uv add "fastapi[standard]"

---> 100%
```

`uv add` создаёт виртуальное окружение проекта в `.venv`, добавляет FastAPI в `pyproject.toml` и создаёт `uv.lock`, чтобы те же версии пакетов можно было установить позже.

**Что делают эти команды:**

* `uv init`: создаёт новый Python-проект.
* `awesome-project`: создаёт проект в новой директории с этим именем.
* `--bare`: создаёт только минимальный файл `pyproject.toml`, без генерации примерного `main.py`, `README.md` или других файлов. Файлы приложения вы создадите самостоятельно на следующих этапах этого руководства.

Затем `cd awesome-project` переходит в директорию нового проекта перед добавлением FastAPI.

`uv` будет использовать совместимую версию Python, уже установленную в вашей системе, или скачает её при необходимости.

Когда вы запускаете `uv add`, он выбирает совместимые версии FastAPI и всех пакетов, от которых зависит FastAPI. Он записывает точные версии в `uv.lock`, что позволяет позже установить те же версии пакетов на другом компьютере или при развертывании приложения.

Создание или обновление этого файла называется [**закреплением** зависимостей проекта](https://docs.astral.sh/uv/concepts/projects/sync/). `uv` делает это автоматически, когда вы добавляете пакет.

**Варианты установки FastAPI:**

При установке с помощью `uv add "fastapi[standard]"` добавляются некоторые стандартные необязательные зависимости по умолчанию, включая `fastapi-cloud-cli`, который позволяет развернуть приложение на [FastAPI Cloud](https://fastapicloud.com).

Если вы не хотите иметь эти необязательные зависимости, вместо этого можно установить `uv add fastapi`.

Если вы хотите установить стандартные зависимости, но без `fastapi-cloud-cli`, можно установить с помощью `uv add "fastapi[standard-no-fastapi-cloud-cli]"`.

**Использование `pip` как альтернативы:**

Если вы предпочитаете управлять виртуальным окружением и пакетами вручную, создайте и активируйте виртуальное окружение, а затем установите FastAPI с помощью `pip install "fastapi[standard]"`.

Подробные шаги читайте в [руководстве по виртуальным окружениям](https://tiangolo.com/guides/virtual-environments/).

## Навыки AI-агента { #ai-agent-skills }

FastAPI включает официальный навык для AI-агентов для написания кода. Он поставляется вместе с пакетом, поэтому его рекомендации остаются согласованными с версией FastAPI, установленной в вашем проекте, и обновляются при обновлении FastAPI.

После установки FastAPI в вашем проекте вы можете установить навык с помощью [Library Skills](https://library-skills.io):

```bash
uvx library-skills
```

**Примечание:**

`uvx` — это псевдоним для `uv tool run`. Он запускает Library Skills во временном изолированном окружении, пока Library Skills сканирует пакеты, установленные в вашем проекте.

Навык совместим с Codex, Claude Code, Cursor, GitHub Copilot, Gemini CLI, Pi, OpenCode и большинством других агентов для написания кода. Для Claude Code выберите `.claude/skills`, когда вас спросят, куда установить навык.

## Продвинутое руководство пользователя { #advanced-user-guide }

Существует также **Продвинутое руководство пользователя**, которое вы сможете прочитать после **Учебник - Руководство пользователя**.

**Продвинутое руководство пользователя** основано на этом, использует те же концепции и обучает некоторым дополнительным функциям.

Но сначала вам следует прочитать **Учебник - Руководство пользователя** (то, что вы читаете прямо сейчас).

Оно спроектировано так, что вы можете создать полноценное приложение, используя только **Учебник - Руководство пользователя**, а затем расширить его различными способами, в зависимости от ваших потребностей, используя дополнительные идеи из **Продвинутого руководства пользователя**.
