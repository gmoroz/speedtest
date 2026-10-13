"""Изоляция тестов от окружения разработчика."""

import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolate_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Удаляет настройки speedtest и меняет текущий каталог теста."""
    for variable_name in tuple(os.environ):
        if variable_name.startswith("SPEEDTEST_"):
            monkeypatch.delenv(variable_name, raising=False)
    monkeypatch.chdir(tmp_path)
