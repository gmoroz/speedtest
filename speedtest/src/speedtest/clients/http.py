"""HTTP-клиент для загрузки ресурсов."""

from __future__ import annotations

from time import perf_counter
from types import TracebackType

import httpx

from speedtest.const import USER_AGENT
from speedtest.exceptions import (
    EmptyResponseError,
    InvalidUrlError,
    NetworkError,
    RequestTimeoutError,
    UnexpectedStatusError,
)
from speedtest.models import DownloadSample


class HttpDownloader:
    """Загружает HTTP-ресурсы и измеряет объём и время передачи."""

    def __init__(self, timeout_seconds: float, transport: httpx.BaseTransport | None = None) -> None:
        """Создаёт HTTP-клиент с таймаутом простоя.

        :param timeout_seconds: максимальная пауза, когда сервер не отдаёт данных, в секундах.
        :param transport: транспорт HTTP-клиента, если нужен явный транспорт.
        """
        self._timeout_seconds = timeout_seconds
        self._client = httpx.Client(
            timeout=timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
            transport=transport,
        )

    def __enter__(self) -> HttpDownloader:
        """Возвращает клиент для работы внутри контекстного менеджера."""
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_value: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        """Закрывает HTTP-клиент при выходе из контекстного менеджера."""
        self.close()

    def close(self) -> None:
        """Закрывает HTTP-клиент и его соединения."""
        self._client.close()

    def download(self, url: str) -> DownloadSample:
        """Скачивает ресурс с таймаутом простоя.

        :param url: URL ресурса для загрузки.
        :return: размер тела и время от отправки запроса до последнего байта.
        """
        started_at = perf_counter()
        try:
            with self._client.stream("GET", url) as response:
                if not response.is_success:
                    raise UnexpectedStatusError(url, response.status_code)

                size_bytes = 0
                for chunk in response.iter_raw():
                    size_bytes += len(chunk)
                elapsed_seconds = perf_counter() - started_at
        except httpx.InvalidURL as error:
            raise InvalidUrlError(url) from error
        except httpx.TimeoutException as error:
            raise RequestTimeoutError(url, self._timeout_seconds) from error
        except httpx.RequestError as error:
            reason = str(error) or type(error).__name__
            raise NetworkError(url, reason) from error

        if size_bytes == 0:
            raise EmptyResponseError(url)
        return DownloadSample(size_bytes=size_bytes, elapsed_seconds=elapsed_seconds)
