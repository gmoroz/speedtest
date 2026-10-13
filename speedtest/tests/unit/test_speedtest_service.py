"""Тесты сервисного слоя замера скорости."""

import pytest

from speedtest.exceptions import InvalidRequestCountError, InvalidUrlError, NetworkError
from speedtest.models import DownloadSample
from speedtest.services import SpeedTestService
from tests.fixtures.downloads import FakeDownloader

SAMPLES = (
    DownloadSample(size_bytes=1_000_000, elapsed_seconds=0.5),
    DownloadSample(size_bytes=2_000_000, elapsed_seconds=1.0),
    DownloadSample(size_bytes=3_000_000, elapsed_seconds=1.5),
)
URL = "https://example.com/heavy.jpg"


def test_run_with_three_samples_returns_expected_report() -> None:
    """Проверяет расчёт итогового отчёта по трём сэмплам."""
    downloader = FakeDownloader(SAMPLES)
    service = SpeedTestService(downloader)

    report = service.run(URL, request_count=3, on_sample=lambda _index, _sample: None)

    assert report.total_bytes == 6_000_000
    assert report.average_bytes == pytest.approx(2_000_000)
    assert report.average_seconds == pytest.approx(1.0)
    assert report.megabytes_per_second == pytest.approx(2.0)


def test_run_with_samples_calls_downloader_and_callback_in_order() -> None:
    """Проверяет последовательность вызовов загрузчика и callback."""
    downloader = FakeDownloader(SAMPLES)
    service = SpeedTestService(downloader)
    received: list[tuple[int, DownloadSample]] = []

    service.run(URL, request_count=3, on_sample=lambda index, sample: received.append((index, sample)))

    assert downloader.urls == [URL, URL, URL]
    assert received == list(enumerate(SAMPLES, start=1))


@pytest.mark.parametrize(
    "url",
    ("ftp://example.com/a.jpg", "example.com/a.jpg", "http://", "", "http://[::1", "http://localhost:abc/x"),
)
def test_run_with_invalid_url_raises_error_without_download(url: str) -> None:
    """Проверяет отказ для каждого некорректного URL до загрузки."""
    downloader = FakeDownloader(SAMPLES)
    service = SpeedTestService(downloader)

    with pytest.raises(InvalidUrlError):
        service.run(url, request_count=3, on_sample=lambda _index, _sample: None)

    assert downloader.urls == []


def test_run_with_uppercase_https_url_accepts_request() -> None:
    """Проверяет принятие HTTPS-схемы в верхнем регистре."""
    downloader = FakeDownloader((SAMPLES[0],))
    service = SpeedTestService(downloader)
    uppercase_url = "HTTPS://Example.com/a.jpg"

    service.run(uppercase_url, request_count=1, on_sample=lambda _index, _sample: None)

    assert downloader.urls == [uppercase_url]


@pytest.mark.parametrize("request_count", (0, -1))
def test_run_with_invalid_request_count_raises_error_without_download(request_count: int) -> None:
    """Проверяет отказ для числа запросов меньше единицы."""
    downloader = FakeDownloader(SAMPLES)
    service = SpeedTestService(downloader)

    with pytest.raises(InvalidRequestCountError):
        service.run(URL, request_count=request_count, on_sample=lambda _index, _sample: None)

    assert downloader.urls == []


def test_run_with_network_error_on_second_call_propagates_same_error() -> None:
    """Проверяет остановку серии и проброс исходной сетевой ошибки."""
    network_error = NetworkError(URL, "соединение разорвано")
    downloader = FakeDownloader(SAMPLES, errors={2: network_error})
    service = SpeedTestService(downloader)
    received: list[tuple[int, DownloadSample]] = []

    with pytest.raises(NetworkError) as raised_error:
        service.run(URL, request_count=3, on_sample=lambda index, sample: received.append((index, sample)))

    assert raised_error.value is network_error
    assert downloader.urls == [URL, URL]
    assert received == [(1, SAMPLES[0])]
