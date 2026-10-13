"""Юнит-тесты доменных моделей."""

import pytest

from speedtest.models import DownloadSample


def test_download_sample_allows_zero_size() -> None:
    """Нулевой размер сэмпла допускается моделью."""
    sample = DownloadSample(size_bytes=0, elapsed_seconds=1.0)

    assert sample.size_bytes == 0


@pytest.mark.parametrize(
    ("size_bytes", "elapsed_seconds"),
    ((1, 0.0), (1, -1.0)),
)
def test_download_sample_non_positive_elapsed_raises_value_error(size_bytes: int, elapsed_seconds: float) -> None:
    """Неположительное время сэмпла вызывает ошибку."""
    with pytest.raises(ValueError, match="elapsed_seconds"):
        DownloadSample(size_bytes=size_bytes, elapsed_seconds=elapsed_seconds)
