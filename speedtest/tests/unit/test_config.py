"""Юнит-тесты Settings."""

from pathlib import Path

import pytest

from speedtest.config import Settings
from speedtest.const import DEFAULT_DB_PATH


def test_settings_defaults_debug_true_uses_default_db_path() -> None:
    """По умолчанию debug=True и дефолтный путь БД."""
    loaded = Settings(_env_file=None)

    assert loaded.debug is True
    assert loaded.db_path == DEFAULT_DB_PATH


def test_settings_production_default_db_path_raises() -> None:
    """Prod-guard отклоняет дефолтный db_path."""
    with pytest.raises(ValueError, match="db_path"):
        Settings(_env_file=None, debug=False)


def test_settings_production_explicit_db_path_accepted() -> None:
    """В production явный db_path проходит."""
    loaded = Settings(_env_file=None, debug=False, db_path=Path("/srv/app.sqlite3"))

    assert loaded.db_path == Path("/srv/app.sqlite3")
