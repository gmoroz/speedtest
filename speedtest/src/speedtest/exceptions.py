"""Иерархия доменных ошибок замера. Общая для clients и services, поэтому вне слоёв."""

import http


def mask_url_userinfo(url: str) -> str:
    """Скрывает пароль из userinfo URL для вывода пользователю.

    Разбор строковый, без urlsplit: маскировать нужно и URL, который urlsplit отвергает.

    :param url: URL в том виде, в котором его передал пользователь.
    :return: URL с `***` вместо пароля; URL без userinfo возвращается без изменений.
    """
    scheme, scheme_separator, remainder = url.partition("://")
    authority_end = min(
        (position for delimiter in "/?#" if (position := remainder.find(delimiter)) != -1),
        default=len(remainder),
    )
    userinfo, at_sign, host = remainder[:authority_end].rpartition("@")
    if not scheme_separator or not at_sign:
        return url
    username, password_separator, _ = userinfo.partition(":")
    masked_userinfo = f"{username}:***" if password_separator else "***"
    return f"{scheme}://{masked_userinfo}@{host}{remainder[authority_end:]}"


class SpeedTestError(Exception):
    """Базовая ошибка замера с сообщением для пользователя."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class InvalidUrlError(SpeedTestError):
    """Адрес не является абсолютным http(s)-URL с хостом."""

    def __init__(self, url: str) -> None:
        super().__init__(f"Некорректный адрес {mask_url_userinfo(url)!r}: нужен http(s)-URL с хостом.")


class InvalidRequestCountError(SpeedTestError):
    """Число запросов меньше одного."""

    def __init__(self, request_count: int) -> None:
        super().__init__(f"Число запросов должно быть не меньше 1, получено {request_count}.")


class RequestTimeoutError(SpeedTestError):
    """Таймаут при соединении, ожидании ответа или передаче данных."""

    def __init__(self, url: str, timeout_seconds: float) -> None:
        super().__init__(
            f"Таймаут {timeout_seconds:g} с при соединении, ожидании ответа или передаче данных "
            f"для загрузки {mask_url_userinfo(url)}."
        )


class NetworkError(SpeedTestError):
    """Сетевой сбой: DNS, соединение, обрыв передачи."""

    def __init__(self, url: str, reason: str) -> None:
        super().__init__(f"Сетевая ошибка при загрузке {mask_url_userinfo(url)}: {reason}.")


class UnexpectedStatusError(SpeedTestError):
    """Итоговый ответ (после редиректов) не 2xx."""

    def __init__(self, url: str, status_code: int) -> None:
        message = f"Сервер вернул HTTP {status_code} для {mask_url_userinfo(url)}."
        if status_code == http.HTTPStatus.TOO_MANY_REQUESTS:
            message += " Сервер ограничил частоту запросов: нужен повтор позже или другой URL."
        super().__init__(message)


class EmptyResponseError(SpeedTestError):
    """Тело ответа пустое: скорость по нему не вычислить."""

    def __init__(self, url: str) -> None:
        super().__init__(f"Сервер вернул пустое тело для {mask_url_userinfo(url)}.")
