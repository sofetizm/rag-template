# Серверные воркеры — Uvicorn с воркерами { #server-workers-uvicorn-with-workers }

Давайте снова вспомним те концепции деплоя, о которых говорили ранее:

* Безопасность — HTTPS
* Запуск при старте
* Перезапуски
* **Репликация (количество запущенных процессов)**
* Память
* Предварительные шаги перед запуском

До этого момента, следуя руководствам в документации, вы, вероятно, запускали **серверную программу**, например с помощью команды `fastapi`, которая запускает Uvicorn в **одном процессе**.

При деплое приложения вам, скорее всего, захочется использовать **репликацию процессов**, чтобы задействовать **несколько ядер** и иметь возможность обрабатывать больше запросов.

Как вы видели в предыдущей главе о [Концепциях деплоя](concepts.md), существует несколько стратегий.

Здесь я покажу, как использовать **Uvicorn** с **воркер-процессами** через команду `fastapi` или напрямую через команду `uvicorn`.

**Примечание:**

Если вы используете контейнеры, например Docker или Kubernetes, я расскажу об этом подробнее в следующей главе: [FastAPI в контейнерах — Docker](docker.md).

В частности, при запуске в **Kubernetes** вам, скорее всего, **не** понадобится использовать воркеры — вместо этого запускайте **один процесс Uvicorn на контейнер**, но об этом подробнее далее в той главе.

## Несколько воркеров { #multiple-workers }

Можно запустить несколько воркеров с помощью опции командной строки `--workers`:

**`fastapi`:**

Если вы используете команду `fastapi`:

```console
$ fastapi run --workers 4 main.py

   FastAPI   Starting production server 🚀

             Searching for package file structure from directories with
             __init__.py files
             Importing from /home/user/code/awesomeapp

    module   🐍 main.py

      code   Importing the FastAPI app object from the module with the
             following code:

             from main import app

       app   Using import string: main:app

    server   Server started at http://0.0.0.0:8000
    server   Documentation at http://0.0.0.0:8000/docs

             Logs:

      INFO   Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to
             quit)
      INFO   Started parent process [27365]
      INFO   Started server process [27368]
      INFO   Started server process [27369]
      INFO   Started server process [27370]
      INFO   Started server process [27367]
      INFO   Waiting for application startup.
      INFO   Waiting for application startup.
      INFO   Waiting for application startup.
      INFO   Waiting for application startup.
      INFO   Application startup complete.
      INFO   Application startup complete.
      INFO   Application startup complete.
      INFO   Application startup complete.
```

**`uvicorn`:**

Если вы предпочитаете использовать команду `uvicorn` напрямую:

```console
$ uv run uvicorn main:app --host 0.0.0.0 --port 8080 --workers 4
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     Started parent process [27365]
INFO:     Started server process [27368]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Started server process [27369]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Started server process [27370]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Started server process [27367]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Единственная новая опция здесь — `--workers`, она говорит Uvicorn запустить 4 воркер-процесса.

Также видно, что выводится **PID** каждого процесса: `27365` — для родительского процесса (это **менеджер процессов**) и по одному для каждого воркер-процесса: `27368`, `27369`, `27370` и `27367`.

## Концепции деплоя { #deployment-concepts }

Здесь вы увидели, как использовать несколько **воркеров**, чтобы **распараллелить** выполнение приложения, задействовать **несколько ядер** CPU и обслуживать **больше запросов**.

Из списка концепций деплоя выше использование воркеров в основном помогает с **репликацией**, и немного — с **перезапусками**, но об остальных по-прежнему нужно позаботиться:

* **Безопасность — HTTPS**
* **Запуск при старте**
* ***Перезапуски***
* Репликация (количество запущенных процессов)
* **Память**
* **Предварительные шаги перед запуском**

## Контейнеры и Docker { #containers-and-docker }

В следующей главе о [FastAPI в контейнерах — Docker](docker.md) я объясню стратегии, которые можно использовать для решения остальных **концепций деплоя**.

Я покажу, как **собрать свой образ с нуля**, чтобы запускать один процесс Uvicorn. Это простой подход и, вероятно, именно то, что вам нужно при использовании распределённой системы управления контейнерами, такой как **Kubernetes**.

## Резюме { #recap }

Вы можете использовать несколько воркер-процессов с опцией командной строки `--workers` в командах `fastapi` или `uvicorn`, чтобы задействовать **многоядерные CPU**, запуская **несколько процессов параллельно**.

Вы можете использовать эти инструменты и идеи, если настраиваете **собственную систему деплоя** и самостоятельно закрываете остальные концепции деплоя.

Перейдите к следующей главе, чтобы узнать о **FastAPI** в контейнерах (например, Docker и Kubernetes). Вы увидите, что эти инструменты тоже предлагают простые способы решить другие **концепции деплоя**. ✨
