"""Юнит-тесты ItemService."""

from unittest.mock import MagicMock

import pytest

from speedtest.enums import ItemStatus
from speedtest.models import Item
from speedtest.services.exceptions import InvalidItemNameError, ItemNotFoundError, ServiceError
from speedtest.services.items import ItemService


def test_add_blank_name_raises_invalid_item_name(item_service: ItemService) -> None:
    """Пустое имя отклоняется до обращения к репозиторию."""
    with pytest.raises(InvalidItemNameError):
        item_service.add("   ")


def test_add_valid_name_persists_via_repository(
    item_service: ItemService,
    item_repository: MagicMock,
    item: Item,
) -> None:
    """Валидное имя уходит в репозиторий со статусом NEW."""
    item_repository.add.return_value = item

    result = item_service.add("Купить молоко")

    assert result == item
    item_repository.add.assert_called_once()
    call_args = item_repository.add.call_args.args
    assert call_args[0] == "Купить молоко"
    assert call_args[1] == ItemStatus.NEW


def test_get_missing_id_raises_item_not_found(
    item_service: ItemService,
    item_repository: MagicMock,
) -> None:
    """Отсутствие записи превращается в ItemNotFoundError."""
    item_repository.get.return_value = None

    with pytest.raises(ItemNotFoundError):
        item_service.get(99)


def test_item_not_found_is_service_error_with_404() -> None:
    """ItemNotFoundError несёт статус 404."""
    error = ItemNotFoundError()

    assert isinstance(error, ServiceError)
    assert error.status_code == 404
    assert error.error_code == "item_not_found"


def test_list_items_returns_repository_rows(
    item_service: ItemService,
    item_repository: MagicMock,
    item: Item,
) -> None:
    """list_items проксирует ответ репозитория."""
    item_repository.list_all.return_value = [item]

    assert item_service.list_items() == [item]
