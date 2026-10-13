"""Интеграционные тесты CLI с локальным HTTP-сервером."""

import subprocess
import sys
from pathlib import Path
from typing import NoReturn

import pytest

from speedtest.cli import main
from speedtest.clients.http import HttpDownloader
from speedtest.enums import ExitCode
from tests.fixtures.http_server import HttpServer

pytestmark = pytest.mark.integration


def test_main_image_download_returns_speed_and_sequential_requests(
    http_server: HttpServer, capsys: pytest.CaptureFixture[str]
) -> None:
    """Успешный CLI-замер печатает скорость и выполняет десять последовательных запросов."""
    exit_code = main([f"{http_server.base_url}/image.bin"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Скорость:" in output
    assert "МБ/с" in output
    assert http_server.served_paths.count("/image.bin") == 10
    assert http_server.max_concurrent_requests == 1


def test_main_requests_option_downloads_requested_number(
    http_server: HttpServer, capsys: pytest.CaptureFixture[str]
) -> None:
    """Опция -n ограничивает число последовательных запросов."""
    exit_code = main(["-n", "3", f"{http_server.base_url}/image.bin"])

    assert exit_code == 0
    assert http_server.served_paths.count("/image.bin") == 3
    assert capsys.readouterr().out.count("/3  ") == 3


def test_main_missing_resource_returns_error_after_one_request(
    http_server: HttpServer, capsys: pytest.CaptureFixture[str]
) -> None:
    """Ответ 404 печатает ошибку и прекращает замер после одного запроса."""
    exit_code = main([f"{http_server.base_url}/missing"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "HTTP 404" in captured.err
    assert http_server.served_paths.count("/missing") == 1


def test_main_ftp_url_returns_error_without_requests(
    http_server: HttpServer, capsys: pytest.CaptureFixture[str]
) -> None:
    """FTP-адрес отклоняется до обращения к HTTP-серверу."""
    exit_code = main(["ftp://example.com/image.bin"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Ошибка:" in captured.err
    assert captured.out == ""


def test_main_zero_requests_returns_error_without_request(
    http_server: HttpServer, capsys: pytest.CaptureFixture[str]
) -> None:
    """Нулевое число запросов отклоняется до обращения к HTTP-серверу."""
    exit_code = main(["-n", "0", f"{http_server.base_url}/image.bin"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Ошибка:" in captured.err
    assert captured.out == ""
    assert http_server.served_paths == []


def test_main_keyboard_interrupt_returns_interrupt_code(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Прерывание загрузки печатает сообщение и возвращает код 130."""

    def interrupted(_downloader: HttpDownloader, _url: str) -> NoReturn:
        raise KeyboardInterrupt

    monkeypatch.setattr(HttpDownloader, "download", interrupted)

    exit_code = main(["https://example.com/image.bin"])
    captured = capsys.readouterr()

    assert exit_code == 130
    assert "Прервано." in captured.err


def test_main_invalid_port_returns_error_without_output(capsys: pytest.CaptureFixture[str]) -> None:
    """URL с нечисловым портом отклоняется без вывода в stdout."""
    exit_code = main(["-n", "1", "http://localhost:abc/x"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""


def test_module_entrypoint_downloads_from_local_server(http_server: HttpServer, tmp_path: Path) -> None:
    """Запуск модуля через Python выполняет CLI-замер локального ресурса."""
    completed = subprocess.run(
        [sys.executable, "-m", "speedtest", f"{http_server.base_url}/image.bin", "-n", "2"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0
    assert "Скорость:" in completed.stdout


def test_main_when_stdout_pipe_closes_returns_error_code_without_traceback(
    http_server: HttpServer, tmp_path: Path
) -> None:
    """Закрытие stdout-пайпа возвращает код ошибки без BrokenPipeError и traceback."""
    process = subprocess.Popen(
        [sys.executable, "-m", "speedtest", "-n", "2", f"{http_server.base_url}/slow"],
        cwd=tmp_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert process.stdout is not None
    assert process.stderr is not None

    process.stdout.readline()
    process.stdout.close()
    return_code = process.wait(timeout=30)
    stderr = process.stderr.read()
    process.stderr.close()

    assert return_code == ExitCode.ERROR
    assert "BrokenPipeError" not in stderr
    assert "Traceback" not in stderr
