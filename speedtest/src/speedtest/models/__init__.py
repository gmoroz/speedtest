"""Доменные модели замера (immutable dataclass)."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DownloadSample:
    """Один запрос: байты, полученные из сети, и время от отправки запроса до последнего байта."""

    size_bytes: int
    elapsed_seconds: float

    def __post_init__(self) -> None:
        if self.elapsed_seconds <= 0:
            raise ValueError("elapsed_seconds должен быть больше нуля")


@dataclass(frozen=True, slots=True)
class SpeedReport:
    """Итог серии запросов."""

    total_bytes: int
    average_bytes: float
    average_seconds: float
    megabytes_per_second: float
