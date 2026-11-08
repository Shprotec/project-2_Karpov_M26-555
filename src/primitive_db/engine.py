"""Консольный интерфейс базы данных."""

import shlex

import prompt
from prettytable import PrettyTable

from primitive_db import core
from primitive_db.constants import ID_COLUMN, META_FILE
from primitive_db.decorators import create_cacher, handle_db_errors
from primitive_db.parser import parse_delete, parse_insert, parse_select, parse_update
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    remove_table_data,
    save_dropped_table,
    save_metadata,
    save_table_data,
    table_data_version,
)

HELP_TEXT = (
    "create_table <таблица> <столбец:тип> ... — создать таблицу\n"
    "list_tables — показать список таблиц\n"
    "drop_table <таблица> — удалить таблицу\n"
    "insert into <таблица> values (<значение>, ...) — добавить запись\n"
    "select from <таблица> [where <столбец> = <значение>] — показать записи\n"
    "update <таблица> set <столбец> = <значение> where <условие> — обновить записи\n"
    "delete from <таблица> where <условие> — удалить записи\n"
    "help — показать справку\n"
    "exit — выйти"
)


def _create_table(args):
    if len(args) < 2:
        raise ValueError("Пример: create_table users name:str age:int")

    table_name, *columns = args
    metadata = load_metadata(META_FILE)
    if core.create_table(metadata, table_name, columns) is None:
        return False
    remove_table_data(table_name)
    save_metadata(META_FILE, metadata)
    print(f'Таблица "{table_name}" создана.')
    return True


def _drop_table(args):
    if len(args) != 1:
        raise ValueError("Пример: drop_table users")

    table_name = args[0]
    metadata = load_metadata(META_FILE)
    if core.drop_table(metadata, table_name) is None:
        return False

    if core.has_table_name(metadata, table_name):
        save_metadata(META_FILE, metadata)
    else:
        save_dropped_table(META_FILE, metadata, table_name)
    print(f'Таблица "{table_name}" удалена.')
    return True


def _list_tables():
    metadata = load_metadata(META_FILE)
    if metadata:
        for table_name in metadata:
            print(table_name)
    else:
        print("Таблиц пока нет.")


def _insert(user_input):
    table_name, values = parse_insert(user_input)
    metadata = load_metadata(META_FILE)
    rows = core.insert(metadata, table_name, values)
    if rows is None:
        return False

    save_table_data(table_name, rows)
    print(f"Запись с ID={rows[-1][ID_COLUMN]} добавлена.")
    return True


def _select(user_input, cache_result):
    table_name, conditions = parse_select(user_input)
    columns = core.get_table_columns(load_metadata(META_FILE), table_name)
    core.validate_values(columns, conditions or {})
    cache_key = (
        table_name,
        tuple(sorted((conditions or {}).items())),
        table_data_version(table_name),
    )
    rows = cache_result(
        cache_key, lambda: core.select(load_table_data(table_name), conditions)
    )
    if rows is None:
        return
    table = PrettyTable(list(columns))
    table.add_rows([[row.get(column) for column in columns] for row in rows])
    print(table)


def _update(user_input):
    table_name, changes, conditions = parse_update(user_input)
    columns = core.get_table_columns(load_metadata(META_FILE), table_name)
    core.validate_values(columns, changes)
    core.validate_values(columns, conditions)
    rows = load_table_data(table_name)
    updated_rows = core.update(rows, changes, conditions)
    if updated_rows is None:
        return False

    changed = sum(old != new for old, new in zip(rows, updated_rows))
    if changed:
        save_table_data(table_name, updated_rows)
    print(f"Обновлено записей: {changed}.")
    return bool(changed)


def _delete(user_input):
    table_name, conditions = parse_delete(user_input)
    columns = core.get_table_columns(load_metadata(META_FILE), table_name)
    core.validate_values(columns, conditions)
    rows = load_table_data(table_name)
    remaining_rows = core.delete(rows, conditions)
    if remaining_rows is None:
        return False

    removed = len(rows) - len(remaining_rows)
    if removed:
        save_table_data(table_name, remaining_rows)
    print(f"Удалено записей: {removed}.")
    return bool(removed)


@handle_db_errors
def _run_command(user_input, cache_result):
    words = user_input.split(maxsplit=1)
    if not words:
        return None

    command = words[0].lower()
    match command:
        case "exit":
            return "exit"
        case "help":
            print(HELP_TEXT)
        case "create_table":
            if _create_table(shlex.split(user_input)[1:]):
                return "changed"
        case "list_tables":
            _list_tables()
        case "drop_table":
            if _drop_table(shlex.split(user_input)[1:]):
                return "changed"
        case "insert":
            if _insert(user_input):
                return "changed"
        case "select":
            _select(user_input, cache_result)
        case "update":
            if _update(user_input):
                return "changed"
        case "delete":
            if _delete(user_input):
                return "changed"
        case _:
            print(f"Неизвестная команда: {command}")
    return None


def run() -> None:
    """Читает команды до выхода из программы."""
    cache_result = create_cacher()
    print(HELP_TEXT)
    try:
        while True:
            result = _run_command(prompt.string("Введите команду: "), cache_result)
            if result == "exit":
                return
            if result == "changed":
                cache_result = create_cacher()
    except (EOFError, KeyboardInterrupt):
        print()
