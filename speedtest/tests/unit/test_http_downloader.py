"""Модульные тесты HTTP-загрузчика."""

import gzip

import httpx
import pytest

from speedtest.clients.http import HttpDownloader
from speedtest.const import USER_AGENT
from speedtest.exceptions import (
    EmptyResponseError,
    InvalidUrlError,
    NetworkError,
    RequestTimeoutError,
    UnexpectedStatusError,
)


def test_download_success_with_user_agent_returns_size_and_elapsed() -> None:
    """Успешный ответ с User-Agent возвращает размер тела и положительное время."""
    payload = b"downloaded payload"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["User-Agent"] == USER_AGENT
        return httpx.Response(200, stream=httpx.ByteStream(payload), request=request)

    with HttpDownloader(timeout_seconds=1.0, transport=httpx.MockTransport(handler)) as downloader:
        sample = downloader.download("https://example.test/image.bin")

    assert sample.size_bytes == len(payload)
    assert sample.elapsed_seconds > 0


def test_download_redirect_to_success_returns_final_body_size() -> None:
    """Редирект 302 на успешный ответ возвращает размер финального тела."""
    payload = b"redirected payload"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/redirect":
            return httpx.Response(302, headers={"Location": "/image.bin"}, request=request)
        return httpx.Response(200, stream=httpx.ByteStream(payload), request=request)

    with HttpDownloader(timeout_seconds=1.0, transport=httpx.MockTransport(handler)) as downloader:
        sample = downloader.download("https://example.test/redirect")

    assert sample.size_bytes == len(payload)


def test_download_unexpected_status_raises_status_error() -> None:
    """Ответ 404 вызывает ошибку со статусом HTTP."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, content=b"missing", request=request)

    with (
        HttpDownloader(timeout_seconds=1.0, transport=httpx.MockTransport(handler)) as downloader,
        pytest.raises(UnexpectedStatusError) as raised,
    ):
        downloader.download("https://example.test/missing")

    error = raised.value
    assert "404" in error.message


def test_download_empty_body_raises_empty_response_error() -> None:
    """Успешный ответ с пустым телом вызывает ошибку пустого ответа."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, stream=httpx.ByteStream(b""), request=request)

    with (
        HttpDownloader(timeout_seconds=1.0, transport=httpx.MockTransport(handler)) as downloader,
        pytest.raises(EmptyResponseError),
    ):
        downloader.download("https://example.test/empty")


def test_download_read_timeout_raises_request_timeout_error() -> None:
    """ReadTimeout от транспорта преобразуется в ошибку таймаута запроса."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    with (
        HttpDownloader(timeout_seconds=0.2, transport=httpx.MockTransport(handler)) as downloader,
        pytest.raises(RequestTimeoutError),
    ):
        downloader.download("https://example.test/slow")


def test_download_connect_error_raises_network_error() -> None:
    """ConnectError от транспорта преобразуется в сетевую ошибку."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection failed", request=request)

    with (
        HttpDownloader(timeout_seconds=1.0, transport=httpx.MockTransport(handler)) as downloader,
        pytest.raises(NetworkError) as raised,
    ):
        downloader.download("https://example.test/image.bin")

    assert "connection failed" in raised.value.message


def test_download_network_error_without_reason_uses_exception_name() -> None:
    """Сетевая ошибка без текста использует имя исключения как причину."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("", request=request)

    with (
        HttpDownloader(timeout_seconds=1.0, transport=httpx.MockTransport(handler)) as downloader,
        pytest.raises(NetworkError) as raised,
    ):
        downloader.download("https://example.test/image.bin")

    assert "ConnectError" in raised.value.message


def test_download_invalid_url_raises_invalid_url_error() -> None:
    """Некорректный URL преобразуется в доменную ошибку адреса."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, stream=httpx.ByteStream(b"unused"), request=request)
    )

    with (
        HttpDownloader(timeout_seconds=1.0, transport=transport) as downloader,
        pytest.raises(InvalidUrlError),
    ):
        downloader.download("http://[::1")


def test_download_gzip_response_counts_compressed_bytes() -> None:
    """Ответ с gzip считает байты сжатого тела без распаковки."""
    payload = b"payload that is compressed before transmission"
    compressed_payload = gzip.compress(payload)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"Content-Encoding": "gzip"},
            stream=httpx.ByteStream(compressed_payload),
            request=request,
        )

    with HttpDownloader(timeout_seconds=1.0, transport=httpx.MockTransport(handler)) as downloader:
        sample = downloader.download("https://example.test/compressed")

    assert sample.size_bytes == len(compressed_payload)


def test_downloader_context_exit_closes_client() -> None:
    """Выход из контекстного менеджера закрывает внутренний HTTP-клиент."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, stream=httpx.ByteStream(b"ok"), request=request)
    )
    downloader = HttpDownloader(timeout_seconds=1.0, transport=transport)

    with downloader as active_downloader:
        assert active_downloader is downloader
        downloader.download("https://example.test/image.bin")

    assert downloader._client.is_closed
