"""Юнит-тесты аргументов CLI без сетевых запросов."""

import builtins
import sys

import pytest

import speedtest.cli as cli
from speedtest import __version__
from speedtest.cli import build_parser, main
from speedtest.enums import ExitCode
from speedtest.models import DownloadSample
from tests.fixtures.downloads import FakeHttpDownloader


def test_parser_without_url_raises_system_exit() -> None:
    """Парсер завершает работу без обязательного URL."""
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_parser_requests_option_parses_integer() -> None:
    """Опция -n сохраняется как целое число запросов."""
    parsed = build_parser().parse_args(["-n", "3", "https://example.com/image.bin"])

    assert parsed.requests == 3


def test_parser_without_requests_leaves_value_unset() -> None:
    """Без опции -n парсер оставляет значение для settings."""
    parsed = build_parser().parse_args(["https://example.com/image.bin"])

    assert parsed.requests is None


def test_parser_version_prints_package_version(capsys: pytest.CaptureFixture[str]) -> None:
    """Опция --version печатает версию пакета."""
    with pytest.raises(SystemExit) as raised:
        build_parser().parse_args(["--version"])

    assert raised.value.code == 0
    assert capsys.readouterr().out == f"speedtest {__version__}\n"


def test_help_with_invalid_configuration_exits_successfully(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Опция --help работает при невалидном значении таймаута."""
    monkeypatch.setenv("SPEEDTEST_TIMEOUT_SECONDS", "0")

    with pytest.raises(SystemExit) as raised:
        main(["--help"])

    captured = capsys.readouterr()

    assert raised.value.code == 0
    assert "usage:" in captured.out


def test_main_invalid_configuration_returns_error_without_traceback(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Все ошибки конфигурации возвращаются без исключения."""
    monkeypatch.setenv("SPEEDTEST_REQUEST_COUNT", "not-an-integer")
    monkeypatch.setenv("SPEEDTEST_TIMEOUT_SECONDS", "0")

    exit_code = main(["http://127.0.0.1:1/image.bin"])
    captured = capsys.readouterr()

    assert exit_code == ExitCode.ERROR
    assert "Ошибка конфигурации: SPEEDTEST_REQUEST_COUNT:" in captured.err
    assert "Ошибка конфигурации: SPEEDTEST_TIMEOUT_SECONDS:" in captured.err
    assert captured.err.count("Ошибка конфигурации:") == 2
    assert captured.out == ""


@pytest.mark.parametrize(
    ("variable", "value"),
    (("SPEEDTEST_TIMEOUT_SECONDS", "inf"), ("SPEEDTEST_REQUEST_COUNT", "0")),
)
def test_main_invalid_environment_value_returns_configuration_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    variable: str,
    value: str,
) -> None:
    """Невалидное значение окружения возвращает ошибку конфигурации."""
    monkeypatch.setenv(variable, value)

    exit_code = main(["http://127.0.0.1:1/image.bin"])
    captured = capsys.readouterr()

    assert exit_code == ExitCode.ERROR
    assert f"Ошибка конфигурации: {variable}:" in captured.err
    assert captured.out == ""


def test_main_with_deterministic_samples_prints_exact_measurement_report(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Детерминированные сэмплы дают точные строки прогресса и итогового отчёта."""
    samples = (
        DownloadSample(size_bytes=1_250_000, elapsed_seconds=0.5),
        DownloadSample(size_bytes=2_500_000, elapsed_seconds=1.0),
    )
    downloaders: list[FakeHttpDownloader] = []

    def make_downloader(_timeout_seconds: float) -> FakeHttpDownloader:
        downloader = FakeHttpDownloader(samples)
        downloaders.append(downloader)
        return downloader

    monkeypatch.setattr(cli, "HttpDownloader", make_downloader)
    url = "https://user:secret@example.test/image.bin"

    exit_code = main(["-n", "2", url])
    captured = capsys.readouterr()

    assert exit_code == ExitCode.OK
    assert captured.out.splitlines() == [
        "Замер скорости: https://user:***@example.test/image.bin",
        "Запросов: 2, последовательно",
        "",
        "1/2  1.25 МБ за 0.500 с",
        "2/2  2.50 МБ за 1.000 с",
        "",
        "Среднее время запроса: 0.750 с",
        "Скачано: 3.75 МБ (в среднем 1.88 МБ за запрос)",
        "Скорость: 2.50 МБ/с (1 МБ = 1 000 000 байт)",
    ]
    assert downloaders[0].urls == [url, url]


def test_main_when_final_output_is_interrupted_returns_interrupt_code(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Прерывание во время итогового вывода возвращает код 130 без исключения."""
    samples = (DownloadSample(size_bytes=1_000_000, elapsed_seconds=1.0),)
    monkeypatch.setattr(cli, "HttpDownloader", lambda _timeout: FakeHttpDownloader(samples))
    original_print = builtins.print

    def interrupting_print(*values: object, file: object | None = None, flush: bool = False) -> None:
        if values and str(values[0]).startswith("Среднее время запроса:"):
            raise KeyboardInterrupt
        if file is not None:
            sys.stderr.write(" ".join(str(value) for value in values) + chr(10))
            return
        original_print(*values, flush=flush)

    monkeypatch.setattr(cli, "print", interrupting_print, raising=False)

    exit_code = main(["-n", "1", "https://example.test/image.bin"])
    captured = capsys.readouterr()

    assert exit_code == ExitCode.INTERRUPTED
    assert "Прервано." in captured.err
