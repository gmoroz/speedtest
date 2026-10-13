# Python CLI

Каталог слоя: `speedtest`.

## Слои

Поток зависимостей направлен вниз: cli -> services -> clients.

| Слой | Что кладут |
|---|---|
| `speedtest/src/speedtest/cli.py` | argparse, вывод в консоль, сборка сервиса |
| `speedtest/src/speedtest/services` | бизнес-правила последовательного замера |
| `speedtest/src/speedtest/clients` | HTTP-загрузка и измерение одного ответа |
| `speedtest/src/speedtest/models` | неизменяемые доменные модели |
| `speedtest/src/speedtest/exceptions.py` | общие ошибки для сервисов и клиентов |
| `speedtest/src/speedtest/const.py` | константы |
| `speedtest/src/speedtest/enums.py` | коды завершения CLI (`ExitCode`) |
| `speedtest/src/speedtest/config.py` | Settings из окружения и `.env` |

Сервис принимает загрузчик через Protocol и не импортирует httpx; это проверяет import-linter.
exceptions.py общий для слоёв и не относится к одному из них.

## Нельзя

- Импортировать вверх по слоям.
- Импортировать httpx в speedtest.services.
- Использовать пакет requests; для HTTP нужен httpx.
- Размещать фикстуры в `speedtest/tests/conftest.py`; они находятся в `speedtest/tests/fixtures`.
- Печатать вне `speedtest/src/speedtest/cli.py`.
- Ловить Exception или оставлять TODO/FIXME/HACK.

## Make

- `make install`
- `make format`
- `make lint`
- `make test`
- `make full-check`

Порог branch coverage задаётся в `speedtest/pyproject.toml`.
Ложные срабатывания vulture находятся в `speedtest/vulture_whitelist.py`.

## Тесты

- `speedtest/tests/unit` — без сети; HTTP-транспорт заменяется MockTransport, остальные загрузчики — фейками.
- `speedtest/tests/integration` — реальный локальный HTTP-сервер из `speedtest/tests/fixtures/http_server.py`.
- Фикстуры размещаются только в `speedtest/tests/fixtures`.
- Имена тестов имеют форму `test_<что>_<условие>_<ожидание>`.
