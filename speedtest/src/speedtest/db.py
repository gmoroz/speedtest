"""Тонкий слой sqlite3. Транзакции коммитятся здесь, не в сервисах."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from speedtest.const import SCHEMA_STATEMENTS


def connect(db_path: Path) -> sqlite3.Connection:
    """Открыть соединение sqlite с Row-фабрикой и внешними ключами."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(connection: sqlite3.Connection) -> None:
    """Создать схему из констант DDL (идемпотентно)."""
    for statement in SCHEMA_STATEMENTS:
        connection.execute(statement)
    connection.commit()


@contextmanager
def transaction(connection: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Граница транзакции: commit при успехе, rollback при исключении."""
    committed = False
    try:
        yield connection
        connection.commit()
        committed = True
    finally:
        if not committed:
            connection.rollback()
