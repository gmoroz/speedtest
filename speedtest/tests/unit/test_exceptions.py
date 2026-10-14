"""Юнит-тесты пользовательских сообщений ошибок."""

from http import HTTPStatus

import pytest

from speedtest.exceptions import (
    EmptyResponseError,
    InvalidUrlError,
    NetworkError,
    RequestTimeoutError,
    SpeedTestError,
    UnexpectedStatusError,
    mask_url_userinfo,
)

URL_WITH_CREDENTIALS = "https://user:secret@example.test/image.bin"


@pytest.mark.parametrize(
    "error",
    (
        InvalidUrlError(URL_WITH_CREDENTIALS),
        RequestTimeoutError(URL_WITH_CREDENTIALS, 1.0),
        NetworkError(URL_WITH_CREDENTIALS, "connection failed"),
        UnexpectedStatusError(URL_WITH_CREDENTIALS, 404),
        EmptyResponseError(URL_WITH_CREDENTIALS),
    ),
)
def test_error_messages_with_password_mask_url_userinfo(error: SpeedTestError) -> None:
    """Сообщения ошибок не раскрывают пароль из URL."""
    assert "secret" not in error.message
    assert "https://user:***@example.test/image.bin" in error.message


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        ("https://user:secret@example.test/image.bin", "https://user:***@example.test/image.bin"),
        ("https://example.test/image.bin", "https://example.test/image.bin"),
        ("https://example.test/user@host/image.bin", "https://example.test/user@host/image.bin"),
        ("https://token@example.test/image.bin?x=1", "https://***@example.test/image.bin?x=1"),
        ("http://user:secret@[::1", "http://user:***@[::1"),
        ("http://[::1", "http://[::1"),
    ),
)
def test_mask_url_userinfo_returns_safe_url_or_original_for_invalid_url(url: str, expected: str) -> None:
    """Маскировка скрывает userinfo и не падает на некорректном URL."""
    assert mask_url_userinfo(url) == expected


def test_unexpected_status_429_suggests_retry_or_other_url() -> None:
    """Ответ 429 объясняет ограничение частоты запросов и предлагает варианты."""
    error = UnexpectedStatusError("https://example.test/image.bin", HTTPStatus.TOO_MANY_REQUESTS)

    assert error.message == (
        "Сервер вернул HTTP 429 для https://example.test/image.bin. "
        "Сервер ограничил частоту запросов: нужен повтор позже или другой URL."
    )


def test_unexpected_status_404_keeps_original_message() -> None:
    """Ответ 404 сохраняет исходное сообщение без подсказки для 429."""
    error = UnexpectedStatusError("https://example.test/image.bin", HTTPStatus.NOT_FOUND)

    assert error.message == "Сервер вернул HTTP 404 для https://example.test/image.bin."
