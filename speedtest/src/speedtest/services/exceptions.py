"""Иерархия доменных ошибок."""


class ServiceError(Exception):
    """Базовая доменная ошибка с машинным кодом и ключом сообщения."""

    def __init__(self, status_code: int, error_code: str, message_key: str) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.message_key = message_key
        super().__init__(f"{error_code}: {message_key}")


class ItemNotFoundError(ServiceError):
    """Запрошенный элемент не найден."""

    def __init__(self, message_key: str = "item.not_found") -> None:
        super().__init__(status_code=404, error_code="item_not_found", message_key=message_key)


class InvalidItemNameError(ServiceError):
    """Имя элемента пустое или из одних пробелов."""

    def __init__(self, message_key: str = "item.invalid_name") -> None:
        super().__init__(status_code=400, error_code="invalid_item_name", message_key=message_key)
