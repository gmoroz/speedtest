"""Фикстуры домена items. Имя фикстуры = создаваемый объект."""

from typing import cast
from unittest.mock import MagicMock, create_autospec

import pytest

from speedtest.enums import ItemStatus
from speedtest.models import Item
from speedtest.repositories.items import ItemRepository
from speedtest.services.items import ItemService


@pytest.fixture
def item() -> Item:
    """Готовый элемент для юнит-тестов."""
    return Item(id=1, name="Купить молоко", status=ItemStatus.NEW, created_at="2026-09-28T00:00:00+00:00")


@pytest.fixture
def item_repository() -> MagicMock:
    """Мок репозитория с autospec."""
    return cast(MagicMock, create_autospec(ItemRepository, instance=True))


@pytest.fixture
def item_service(item_repository: MagicMock) -> ItemService:
    """Сервис на мок-репозитории."""
    return ItemService(cast(ItemRepository, item_repository))
