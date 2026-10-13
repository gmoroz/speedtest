"""Доменные модели строк (immutable dataclass)."""

from dataclasses import dataclass

from speedtest.enums import ItemStatus


@dataclass(frozen=True, slots=True)
class Item:
    """Элемент списка дел."""

    id: int
    name: str
    status: ItemStatus
    created_at: str
