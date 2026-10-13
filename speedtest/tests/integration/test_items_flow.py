"""Интеграционные тесты sqlite: db -> repository -> service -> cli."""

from pathlib import Path

import pytest

from speedtest.cli import main
from speedtest.db import connect, init_db, transaction
from speedtest.enums import ItemStatus
from speedtest.repositories.items import ItemRepository
from speedtest.services.exceptions import InvalidItemNameError, ItemNotFoundError
from speedtest.services.items import ItemService


@pytest.mark.integration
def test_service_add_list_get_roundtrip_persists(tmp_path: Path) -> None:
    """Сервис сохраняет элемент и читает его обратно через sqlite."""
    connection = connect(tmp_path / "app.sqlite3")
    try:
        init_db(connection)
        service = ItemService(ItemRepository(connection))

        with transaction(connection):
            created = service.add("Собрать отчёт")

        assert created.id > 0
        assert created.status == ItemStatus.NEW
        assert service.list_items() == [created]
        assert service.get(created.id) == created
    finally:
        connection.close()


@pytest.mark.integration
def test_service_add_blank_name_rolls_back(tmp_path: Path) -> None:
    """Ошибка валидации не оставляет строк в таблице."""
    connection = connect(tmp_path / "app.sqlite3")
    try:
        init_db(connection)
        service = ItemService(ItemRepository(connection))

        with pytest.raises(InvalidItemNameError), transaction(connection):
            service.add("  ")

        assert service.list_items() == []
    finally:
        connection.close()


@pytest.mark.integration
def test_cli_add_list_get_prints_item(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """CLI add/list/get работает на временном sqlite-файле."""
    db_path = tmp_path / "cli.sqlite3"

    add_code = main(["--db", str(db_path), "add", "Проверить гейты"])
    list_code = main(["--db", str(db_path), "list"])
    get_code = main(["--db", str(db_path), "get", "1"])
    captured = capsys.readouterr()

    assert add_code == 0
    assert list_code == 0
    assert get_code == 0
    assert "Проверить гейты" in captured.out


@pytest.mark.integration
def test_cli_get_missing_id_returns_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI get для отсутствующего id возвращает код 1."""
    db_path = tmp_path / "cli.sqlite3"
    main(["--db", str(db_path), "add", "есть"])

    code = main(["--db", str(db_path), "get", "999"])
    captured = capsys.readouterr()

    assert code == 1
    assert "item_not_found" in captured.err


@pytest.mark.integration
def test_transaction_rollback_on_error(tmp_path: Path) -> None:
    """Исключение внутри transaction откатывает INSERT."""
    connection = connect(tmp_path / "app.sqlite3")
    try:
        init_db(connection)
        repository = ItemRepository(connection)

        with pytest.raises(ItemNotFoundError), transaction(connection):
            repository.add("временный", ItemStatus.NEW, "2026-09-28T00:00:00+00:00")
            raise ItemNotFoundError

        assert ItemRepository(connection).list_all() == []
    finally:
        connection.close()
