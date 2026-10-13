"""CLI-точка входа (argparse). Слой I/O: print разрешён (per-file-ignore T201)."""

import argparse
import sqlite3
import sys
from collections.abc import Sequence
from pathlib import Path

from speedtest.config import settings
from speedtest.db import connect, init_db, transaction
from speedtest.repositories.items import ItemRepository
from speedtest.services.exceptions import ServiceError
from speedtest.services.items import ItemService


def build_parser() -> argparse.ArgumentParser:
    """Собрать парсер с subcommands."""
    parser = argparse.ArgumentParser(prog="speedtest", description="CLI-список элементов.")
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="Путь к sqlite-файлу (по умолчанию из Settings).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Добавить элемент")
    add_parser.add_argument("name", help="Имя элемента")

    subparsers.add_parser("list", help="Показать все элементы")

    get_parser = subparsers.add_parser("get", help="Показать элемент по id")
    get_parser.add_argument("item_id", type=int, help="Идентификатор элемента")

    return parser


def build_item_service(connection: sqlite3.Connection) -> ItemService:
    """Собрать сервис с репозиторием на открытом соединении."""
    return ItemService(ItemRepository(connection))


def main(argv: Sequence[str] | None = None) -> int:
    """Разобрать аргументы и выполнить subcommand. Возвращает код выхода."""
    parser = build_parser()
    args = parser.parse_args(argv)
    db_path = args.db if args.db is not None else settings.db_path
    connection = connect(db_path)
    try:
        init_db(connection)
        try:
            with transaction(connection):
                service = build_item_service(connection)
                if args.command == "add":
                    item = service.add(args.name)
                    print(f"{item.id}\t{item.name}\t{item.status}")
                    return 0
                if args.command == "list":
                    for item in service.list_items():
                        print(f"{item.id}\t{item.name}\t{item.status}")
                    return 0
                if args.command == "get":
                    item = service.get(args.item_id)
                    print(f"{item.id}\t{item.name}\t{item.status}")
                    return 0
        except ServiceError as error:
            print(f"error: {error.error_code}", file=sys.stderr)
            return 1
    finally:
        connection.close()

    parser.error(f"неизвестная команда: {args.command}")
    return 2
