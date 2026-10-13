"""Интеграционные тесты HTTP-загрузчика с локальным сервером."""

import socket

import pytest

from speedtest.clients.http import HttpDownloader
from speedtest.exceptions import EmptyResponseError, NetworkError, RequestTimeoutError, UnexpectedStatusError
from tests.fixtures.http_server import IMAGE_PAYLOAD, HttpServer

pytestmark = pytest.mark.integration


def test_download_image_from_local_server_returns_full_payload(http_server: HttpServer) -> None:
    """Загрузка image.bin возвращает полный размер тела локального сервера."""
    with HttpDownloader(timeout_seconds=2.0) as downloader:
        sample = downloader.download(f"{http_server.base_url}/image.bin")

    assert sample.size_bytes == len(IMAGE_PAYLOAD)


def test_download_missing_from_local_server_raises_status_error(http_server: HttpServer) -> None:
    """Загрузка missing преобразует ответ 404 в ошибку статуса."""
    with HttpDownloader(timeout_seconds=2.0) as downloader, pytest.raises(UnexpectedStatusError) as raised:
        downloader.download(f"{http_server.base_url}/missing")

    assert "404" in raised.value.message


def test_download_empty_from_local_server_raises_empty_response_error(http_server: HttpServer) -> None:
    """Загрузка empty преобразует пустое тело в ошибку ответа."""
    with HttpDownloader(timeout_seconds=2.0) as downloader, pytest.raises(EmptyResponseError):
        downloader.download(f"{http_server.base_url}/empty")


def test_download_redirect_from_local_server_returns_full_payload(http_server: HttpServer) -> None:
    """Загрузка redirect возвращает полный размер тела после перенаправления."""
    with HttpDownloader(timeout_seconds=2.0) as downloader:
        sample = downloader.download(f"{http_server.base_url}/redirect")

    assert sample.size_bytes == len(IMAGE_PAYLOAD)


def test_download_slow_from_local_server_raises_request_timeout(http_server: HttpServer) -> None:
    """Загрузка slow с коротким таймаутом вызывает ошибку таймаута."""
    with HttpDownloader(timeout_seconds=0.2) as downloader, pytest.raises(RequestTimeoutError):
        downloader.download(f"{http_server.base_url}/slow")


def test_download_closed_local_port_raises_network_error() -> None:
    """Подключение к закрытому loopback-порту вызывает сетевую ошибку."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        port = int(listener.getsockname()[1])

    with HttpDownloader(timeout_seconds=1.0) as downloader, pytest.raises(NetworkError):
        downloader.download(f"http://127.0.0.1:{port}/image.bin")
