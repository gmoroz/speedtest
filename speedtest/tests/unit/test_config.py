"""Юнит-тесты конфигурации."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from speedtest.config import Settings


def test_settings_defaults_without_env_file_return_expected_values() -> None:
    """Без env-файла настройки содержат значения по умолчанию."""
    loaded = Settings(_env_file=None)

    assert loaded.request_count == 10
    assert loaded.timeout_seconds == 30.0


def test_settings_ignore_env_example() -> None:
    """Файл `.env.example` не влияет на настройки приложения."""
    Path(".env.example").write_text("SPEEDTEST_REQUEST_COUNT=3\n", encoding="utf-8")

    loaded = Settings()

    assert loaded.request_count == 10


def test_settings_environment_variables_override_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Переменные SPEEDTEST_ переопределяют значения настроек."""
    monkeypatch.setenv("SPEEDTEST_REQUEST_COUNT", "3")
    monkeypatch.setenv("SPEEDTEST_TIMEOUT_SECONDS", "4.5")

    loaded = Settings(_env_file=None)

    assert loaded.request_count == 3
    assert loaded.timeout_seconds == 4.5


def test_settings_zero_timeout_raises_validation_error() -> None:
    """Нулевой таймаут не проходит валидацию."""
    with pytest.raises(ValidationError):
        Settings(_env_file=None, timeout_seconds=0)
