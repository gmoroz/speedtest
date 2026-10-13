# Python CLI

Каталог слоя: `speedtest`.

## Слои

Поток только вниз: cli -> services -> repositories. Транзакцию открывает CLI через db.transaction.

| Куда | Что класть |
|---|---|
| `speedtest/src/speedtest/cli.py` | argparse, print, сборка сервиса |
| `speedtest/src/speedtest/services` | бизнес-правила, без SQL |
| `speedtest/src/speedtest/repositories` | SQL и работа с sqlite |
| `speedtest/src/speedtest/db.py` | connect / init_db / transaction |
| `speedtest/src/speedtest/models` | immutable dataclass строк |
| `speedtest/src/speedtest/const.py` | только константы |
| `speedtest/src/speedtest/enums.py` | StrEnum |
| `speedtest/src/speedtest/config.py` | Settings-синглтон |

## Нельзя

- Импорт вверх по слоям (ловит import-linter).
- commit в services.
- Пакет requests (banned-api; нужен HTTP - бери httpx).
- Фикстуры в conftest.py (только pytest_plugins).
- print вне CLI (T201).
- except Exception (BLE001), TODO/FIXME/HACK (FIX).

## Make

- make install / make format / make lint / make test / make full-check
- Порог coverage branch - один: cov-fail-under=80 в `speedtest/pyproject.toml`.
- Ложные срабатывания vulture - в `speedtest/vulture_whitelist.py`.

## Тесты

- `speedtest/tests/unit` - без реальной БД.
- `speedtest/tests/integration` - sqlite на tmp_path.
- Фикстуры только в `speedtest/tests/fixtures/`.
- Имена: test_<что>_<условие>_<ожидание>.
