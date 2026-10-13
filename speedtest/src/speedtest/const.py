"""Константы пакета. Только значения - без runtime-логики и настроек."""

from pathlib import Path

DEFAULT_DB_PATH = Path("data") / "speedtest.sqlite3"

SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
)
