"""Фиксированные наборы значений - StrEnum."""

from enum import StrEnum


class ItemStatus(StrEnum):
    """Статус элемента списка."""

    NEW = "new"
    DONE = "done"
