"""Командная строка замера скорости."""

import argparse
import os
import sys
from collections.abc import Sequence

from pydantic import ValidationError

from speedtest import __version__
from speedtest.clients.http import HttpDownloader
from speedtest.config import Settings
from speedtest.const import BYTES_PER_MEGABYTE, DEFAULT_REQUEST_COUNT
from speedtest.enums import ExitCode
from speedtest.exceptions import SpeedTestError, mask_url_userinfo
from speedtest.models import DownloadSample
from speedtest.services import SpeedTestService


def build_parser() -> argparse.ArgumentParser:
    """Собирает парсер аргументов командной строки.

    :return: настроенный парсер аргументов.
    """
    parser = argparse.ArgumentParser(prog="speedtest", description="Замер скорости загрузки ресурса.")
    parser.add_argument(
        "-n",
        "--requests",
        type=int,
        default=None,
        metavar="N",
        help=f"число последовательных запросов (по умолчанию {DEFAULT_REQUEST_COUNT} или SPEEDTEST_REQUEST_COUNT)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("url", help="URL ресурса для загрузки")
    return parser


def main(argv: Sequence[str] | None = None) -> ExitCode:
    """Выполняет замер скорости и возвращает код завершения.

    :param argv: аргументы командной строки без имени программы.
    :return: код завершения команды.
    """
    args = build_parser().parse_args(argv)

    try:
        settings = Settings()
    except ValidationError as error:
        env_prefix = str(Settings.model_config["env_prefix"])
        for details in error.errors():
            field = "_".join(str(part) for part in details["loc"]).upper() or "SETTINGS"
            print(f"Ошибка конфигурации: {env_prefix}{field}: {details['msg']}", file=sys.stderr)
        return ExitCode.ERROR

    request_count = args.requests if args.requests is not None else settings.request_count

    try:
        width = len(str(request_count))

        with HttpDownloader(settings.timeout_seconds) as downloader:
            service = SpeedTestService(downloader)
            service.validate(args.url, request_count)
            print(f"Замер скорости: {mask_url_userinfo(args.url)}")
            print(f"Запросов: {request_count}, последовательно")
            print()

            def on_sample(index: int, sample: DownloadSample) -> None:
                """Печатает один полученный сэмпл."""
                megabytes = sample.size_bytes / BYTES_PER_MEGABYTE
                print(
                    f"{index:>{width}}/{request_count}  {megabytes:.2f} МБ за {sample.elapsed_seconds:.3f} с",
                    flush=True,
                )

            report = service.run(args.url, request_count, on_sample=on_sample)

            print()
            print(f"Среднее время запроса: {report.average_seconds:.3f} с")
            print(
                f"Скачано: {report.total_bytes / BYTES_PER_MEGABYTE:.2f} МБ "
                f"(в среднем {report.average_bytes / BYTES_PER_MEGABYTE:.2f} МБ за запрос)"
            )
            formatted_megabyte = f"{BYTES_PER_MEGABYTE:,}".replace(",", " ")
            print(f"Скорость: {report.megabytes_per_second:.2f} МБ/с (1 МБ = {formatted_megabyte} байт)")
    except SpeedTestError as error:
        print(f"Ошибка: {error.message}", file=sys.stderr)
        return ExitCode.ERROR
    except KeyboardInterrupt:
        print("Прервано.", file=sys.stderr)
        return ExitCode.INTERRUPTED
    except BrokenPipeError:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        os.close(devnull)
        return ExitCode.ERROR

    return ExitCode.OK
