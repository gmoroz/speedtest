"""Корневой conftest: только регистрация fixture-модулей."""

pytest_plugins = [
    "tests.fixtures.items",
]
