"""Юнит-тесты argparse CLI без записи на диск."""

import pytest

from speedtest.cli import build_parser


def test_parser_without_command_exits() -> None:
    """Без subcommand argparse завершает процесс."""
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_parser_add_command_keeps_name() -> None:
    """Команда add сохраняет имя аргумента."""
    args = build_parser().parse_args(["add", "задача"])

    assert args.command == "add"
    assert args.name == "задача"


def test_parser_get_command_parses_item_id() -> None:
    """Команда get парсит целочисленный id."""
    args = build_parser().parse_args(["get", "7"])

    assert args.command == "get"
    assert args.item_id == 7
