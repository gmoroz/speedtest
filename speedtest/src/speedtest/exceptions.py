"""Иерархия доменных ошибок замера. Общая для clients и services, поэтому вне слоёв."""


class SpeedTestError(Exception):
    """Базовая ошибка замера с сообщением для пользователя."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class InvalidUrlError(SpeedTestError):
    """Адрес не является абсолютным http(s)-URL с хостом."""

    def __init__(self, url: str) -> None:
        super().__init__(f"Некорректный адрес {url!r}: нужен http(s)-URL с хостом.")


class InvalidRequestCountError(SpeedTestError):
    """Число запросов меньше одного."""

    def __init__(self, request_count: int) -> None:
        super().__init__(f"Число запросов должно быть не меньше 1, получено {request_count}.")


class RequestTimeoutError(SpeedTestError):
    """Сервер не отдавал данные дольше заданного таймаута."""

    def __init__(self, url: str, timeout_seconds: float) -> None:
        super().__init__(f"Сервер не отдавал данных дольше {timeout_seconds:g} с при загрузке {url}.")


class NetworkError(SpeedTestError):
    """Сетевой сбой: DNS, соединение, обрыв передачи."""

    def __init__(self, url: str, reason: str) -> None:
        super().__init__(f"Сетевая ошибка при загрузке {url}: {reason}.")


class UnexpectedStatusError(SpeedTestError):
    """Итоговый ответ (после редиректов) не 2xx."""

    def __init__(self, url: str, status_code: int) -> None:
        super().__init__(f"Сервер вернул HTTP {status_code} для {url}.")


class EmptyResponseError(SpeedTestError):
    """Тело ответа пустое: скорость по нему не вычислить."""

    def __init__(self, url: str) -> None:
        super().__init__(f"Сервер вернул пустое тело для {url}.")
