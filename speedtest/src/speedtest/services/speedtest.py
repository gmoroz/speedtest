"""Сервис последовательного замера скорости загрузки."""

from collections.abc import Callable
from typing import Protocol
from urllib.parse import urlsplit

from speedtest.const import ALLOWED_URL_SCHEMES, BYTES_PER_MEGABYTE
from speedtest.exceptions import InvalidRequestCountError, InvalidUrlError
from speedtest.models import DownloadSample, SpeedReport


class Downloader(Protocol):
    """Порт загрузчика, который получает один сэмпл по URL."""

    def download(self, url: str) -> DownloadSample:
        """Загружает ресурс и возвращает сэмпл."""
        ...


class SpeedTestService:
    """Выполняет серию последовательных загрузок и собирает отчёт."""

    def __init__(self, downloader: Downloader) -> None:
        self._downloader = downloader

    def validate(self, url: str, request_count: int) -> None:
        """Проверяет URL и число запросов до начала замера.

        :param url: URL ресурса для загрузки.
        :param request_count: число последовательных запросов.
        """
        try:
            parsed_url = urlsplit(url)
            _ = parsed_url.port
        except ValueError:
            raise InvalidUrlError(url) from None
        if parsed_url.scheme not in ALLOWED_URL_SCHEMES or parsed_url.hostname is None:
            raise InvalidUrlError(url)
        if request_count < 1:
            raise InvalidRequestCountError(request_count)

    def run(
        self,
        url: str,
        request_count: int,
        on_sample: Callable[[int, DownloadSample], None],
    ) -> SpeedReport:
        """Выполняет замер и возвращает отчёт.

        Скорость равна суммарному объёму, делённому на суммарное время и
        `BYTES_PER_MEGABYTE`, что равно среднему объёму, делённому на среднее
        время и `BYTES_PER_MEGABYTE`.

        :param url: URL ресурса для загрузки.
        :param request_count: число последовательных запросов.
        :param on_sample: callback после каждого успешно полученного сэмпла.
        :return: итоговый отчёт по серии запросов.
        """
        self.validate(url, request_count)

        total_bytes = 0
        total_seconds = 0.0
        for index in range(1, request_count + 1):
            sample = self._downloader.download(url)
            on_sample(index, sample)
            total_bytes += sample.size_bytes
            total_seconds += sample.elapsed_seconds

        return SpeedReport(
            total_bytes=total_bytes,
            average_bytes=total_bytes / request_count,
            average_seconds=total_seconds / request_count,
            megabytes_per_second=total_bytes / total_seconds / BYTES_PER_MEGABYTE,
        )
