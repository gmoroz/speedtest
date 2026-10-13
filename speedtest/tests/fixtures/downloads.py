"""Фейковый загрузчик для тестов сервисного слоя."""

from collections.abc import Mapping, Sequence

from speedtest.models import DownloadSample
from speedtest.services.speedtest import Downloader


class FakeDownloader(Downloader):
    """Возвращает заданные сэмплы и записывает URL запросов."""

    def __init__(
        self,
        samples: Sequence[DownloadSample],
        *,
        errors: Mapping[int, BaseException] | None = None,
    ) -> None:
        self._samples = tuple(samples)
        self._errors = {} if errors is None else errors
        self.urls: list[str] = []

    def download(self, url: str) -> DownloadSample:
        """Возвращает следующий сэмпл или поднимает заданную ошибку."""
        self.urls.append(url)
        call_number = len(self.urls)
        if call_number in self._errors:
            raise self._errors[call_number]
        return self._samples[call_number - 1]


class FakeHttpDownloader(FakeDownloader):
    """Возвращает заданные сэмплы через интерфейс контекстного HTTP-клиента."""

    def __enter__(self) -> FakeHttpDownloader:
        """Возвращает фейковый клиент для контекстного менеджера."""
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_value: BaseException | None,
        _traceback: object | None,
    ) -> None:
        """Завершает работу фейкового клиента."""
        return None
