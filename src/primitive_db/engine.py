"""Консольный интерфейс базы данных."""

import shlex

import prompt
from prettytable import PrettyTable

from primitive_db import core
from primitive_db.constants import (
    CMD_CREATE_TABLE,
    CMD_DELETE,
    CMD_DROP_TABLE,
    CMD_EXIT,
    CMD_HELP,
    CMD_INFO,
    CMD_INSERT,
    CMD_LIST_TABLES,
    CMD_SELECT,
    CMD_UPDATE,
    ID_COLUMN,
    META_FILE,
    PROMPT_MESSAGE,
)
from primitive_db.decorators import create_cacher, handle_db_errors
from primitive_db.parser import parse_delete, parse_insert, parse_select, parse_update
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    remove_table_data,
    save_metadata,
    save_table_data,
)

HELP_TEXT = """
***Процесс работы с таблицей***
Функции:
<command> create_table <имя_таблицы> <столбец1:тип> <столбец2:тип> .. - создать таблицу
<command> list_tables - показать список всех таблиц
<command> drop_table <имя_таблицы> - удалить таблицу

***Операции с данными***
Функции:
<command> insert into <имя_таблицы> values (<значение1>, <значение2>, ...) - создать запись.
<command> select from <имя_таблицы> where <столбец> = <значение> - прочитать записи по условию.
<command> select from <имя_таблицы> - прочитать все записи.
<command> update <имя_таблицы> set <столбец1> = <новое_значение1> where <столбец_условия> = <значение_условия> - обновить запись.
<command> delete from <имя_таблицы> where <столбец> = <значение> - удалить запись.
<command> info <имя_таблицы> - вывести информацию о таблице.

Общие команды:
<command> exit - выход из программы
<command> help - справочная информация
"""  # noqa: E501

select_cache = create_cacher()


def print_help():
    """Выводит справку."""
    print(HELP_TEXT)


def format_columns(columns):
    """Собирает строку со столбцами вида ID:int, name:str."""
    return ", ".join(f"{name}:{column_type}" for name, column_type in columns.items())


def require_arguments(args, count):
    """Проверяет количество слов в команде."""
    if len(args) != count:
        raise ValueError(" ".join(args))


def create_table_command(metadata, args):
    """Команда create_table."""
    if len(args) < 3:
        raise ValueError(
            f"{' '.join(args)} (пример: create_table users name:str age:int)"
        )
    table_name, columns = args[1], args[2:]
    if core.create_table(metadata, table_name, columns) is None:
        return
    save_metadata(META_FILE, metadata)
    schema = format_columns(core.get_table_columns(metadata, table_name))
    print(f'Таблица "{table_name}" успешно создана со столбцами: {schema}')


def list_tables_command(metadata, args):
    """Команда list_tables."""
    require_arguments(args, 1)
    if not metadata:
        print("Таблиц пока нет.")
    for table_name in metadata:
        print(f"- {table_name}")


def drop_table_command(metadata, args):
    """Команда drop_table. Наличие таблицы проверяется до подтверждения."""
    require_arguments(args, 2)
    table_name = args[1]
    core.check_table_exists(metadata, table_name)
    if core.drop_table(metadata, table_name) is None:
        return
    save_metadata(META_FILE, metadata)
    remove_table_data(table_name)
    select_cache.clear()
    print(f'Таблица "{table_name}" успешно удалена.')


def insert_command(metadata, user_input):
    """Команда insert."""
    table_name, values = parse_insert(user_input)
    rows = core.insert(metadata, table_name, values, load_table_data(table_name))
    if rows is None:
        return
    save_table_data(table_name, rows)
    select_cache.clear()
    new_id = rows[-1][ID_COLUMN]
    print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".')


def select_command(metadata, user_input):
    """Команда select, результат берётся из кэша."""
    table_name, conditions = parse_select(user_input)
    columns = core.get_table_columns(metadata, table_name)
    core.validate_values(columns, conditions or {})
    cache_key = (table_name, tuple(sorted((conditions or {}).items())))
    rows = select_cache(
        cache_key, lambda: core.select(load_table_data(table_name), conditions)
    )
    table = PrettyTable(list(columns))
    table.add_rows([[row.get(column) for column in columns] for row in rows])
    print(table)


def update_command(metadata, user_input):
    """Команда update."""
    table_name, changes, conditions = parse_update(user_input)
    columns = core.get_table_columns(metadata, table_name)
    core.validate_values(columns, changes)
    core.validate_values(columns, conditions)
    rows = load_table_data(table_name)
    row_ids = core.find_row_ids(rows, conditions)
    if not row_ids:
        print("Записи, удовлетворяющие условию, не найдены.")
        return

    updated_rows = core.update(rows, changes, conditions)
    if updated_rows is None:
        return
    save_table_data(table_name, updated_rows)
    select_cache.clear()
    for row_id in row_ids:
        print(f'Запись с ID={row_id} в таблице "{table_name}" успешно обновлена.')


def delete_command(metadata, user_input):
    """Команда delete."""
    table_name, conditions = parse_delete(user_input)
    columns = core.get_table_columns(metadata, table_name)
    core.validate_values(columns, conditions)
    rows = load_table_data(table_name)
    row_ids = core.find_row_ids(rows, conditions)
    if not row_ids:
        print("Записи, удовлетворяющие условию, не найдены.")
        return

    remaining_rows = core.delete(rows, conditions)
    if remaining_rows is None:
        return
    save_table_data(table_name, remaining_rows)
    select_cache.clear()
    for row_id in row_ids:
        print(f'Запись с ID={row_id} успешно удалена из таблицы "{table_name}".')


def info_command(metadata, args):
    """Команда info."""
    require_arguments(args, 2)
    table_name = args[1]
    columns = core.get_table_columns(metadata, table_name)
    print(f"Таблица: {table_name}")
    print(f"Столбцы: {format_columns(columns)}")
    print(f"Количество записей: {len(load_table_data(table_name))}")


@handle_db_errors
def run_command(user_input):
    """Разбирает введённую строку и выполняет команду."""
    words = user_input.split()
    if not words:
        return
    command = words[0].lower()
    metadata = load_metadata(META_FILE)

    if command == CMD_HELP:
        print_help()
    elif command == CMD_CREATE_TABLE:
        create_table_command(metadata, shlex.split(user_input))
    elif command == CMD_LIST_TABLES:
        list_tables_command(metadata, shlex.split(user_input))
    elif command == CMD_DROP_TABLE:
        drop_table_command(metadata, shlex.split(user_input))
    elif command == CMD_INFO:
        info_command(metadata, shlex.split(user_input))
    elif command == CMD_INSERT:
        insert_command(metadata, user_input)
    elif command == CMD_SELECT:
        select_command(metadata, user_input)
    elif command == CMD_UPDATE:
        update_command(metadata, user_input)
    elif command == CMD_DELETE:
        delete_command(metadata, user_input)
    else:
        print(f"Функции {words[0]} нет. Попробуйте снова.")


def run():
    """Читает команды до выхода из программы."""
    print("\n***База данных***")
    print_help()
    while True:
        try:
            user_input = prompt.string(PROMPT_MESSAGE)
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if user_input.strip().lower() == CMD_EXIT:
            return
        run_command(user_input)
        print()
