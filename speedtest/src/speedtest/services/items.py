"""Сервис элементов списка."""

from datetime import UTC, datetime

from speedtest.enums import ItemStatus
from speedtest.models import Item
from speedtest.repositories.items import ItemRepository
from speedtest.services.exceptions import InvalidItemNameError, ItemNotFoundError


class ItemService:
    """Бизнес-операции над элементами без знания о транзакциях."""

    def __init__(self, repository: ItemRepository) -> None:
        self._repository = repository

    def add(self, name: str) -> Item:
        """Добавить элемент с валидацией имени."""
        cleaned = name.strip()
        if not cleaned:
            raise InvalidItemNameError
        created_at = datetime.now(UTC).isoformat()
        return self._repository.add(cleaned, ItemStatus.NEW, created_at)

    def list_items(self) -> list[Item]:
        """Вернуть все элементы."""
        return self._repository.list_all()

    def get(self, item_id: int) -> Item:
        """Вернуть элемент или поднять ItemNotFoundError."""
        item = self._repository.get(item_id)
        if item is None:
            raise ItemNotFoundError
        return item
