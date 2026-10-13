"""Корневой conftest: только регистрация fixture-модулей."""

pytest_plugins = [
    "tests.fixtures.downloads",
    "tests.fixtures.environment",
    "tests.fixtures.http_server",
]
