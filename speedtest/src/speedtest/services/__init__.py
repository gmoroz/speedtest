"""Слой бизнес-логики. Сервисы знают репозитории, но не транзакции."""

from speedtest.services.items import ItemService

__all__ = ["ItemService"]
