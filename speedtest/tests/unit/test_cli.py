"""Юнит-тесты аргументов CLI без сетевых запросов."""

import pytest

from speedtest import __version__
from speedtest.cli import build_parser, main
from speedtest.enums import ExitCode


def test_parser_without_url_exits() -> None:
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


def test_help_ignores_invalid_configuration(
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
