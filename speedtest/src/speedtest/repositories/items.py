"""Репозиторий элементов списка на sqlite3."""

import sqlite3

from speedtest.enums import ItemStatus
from speedtest.models import Item


class ItemRepository:
    """SQL-доступ к таблице items."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, name: str, status: ItemStatus, created_at: str) -> Item:
        """Вставить элемент и вернуть доменную модель."""
        cursor = self._connection.execute(
            "INSERT INTO items (name, status, created_at) VALUES (?, ?, ?)",
            (name, status.value, created_at),
        )
        item_id = int(cursor.lastrowid) if cursor.lastrowid is not None else 0
        return Item(id=item_id, name=name, status=status, created_at=created_at)

    def list_all(self) -> list[Item]:
        """Вернуть все элементы по возрастанию id."""
        rows = self._connection.execute(
            "SELECT id, name, status, created_at FROM items ORDER BY id",
        ).fetchall()
        return [
            Item(
                id=int(row["id"]),
                name=str(row["name"]),
                status=ItemStatus(str(row["status"])),
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]

    def get(self, item_id: int) -> Item | None:
        """Найти элемент по id или вернуть None."""
        row = self._connection.execute(
            "SELECT id, name, status, created_at FROM items WHERE id = ?",
            (item_id,),
        ).fetchone()
        if row is None:
            return None
        return Item(
            id=int(row["id"]),
            name=str(row["name"]),
            status=ItemStatus(str(row["status"])),
            created_at=str(row["created_at"]),
        )
