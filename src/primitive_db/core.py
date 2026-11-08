"""Работа с таблицами и CRUD-операции."""

from primitive_db.constants import (
    COLUMN_TYPE_SEPARATOR,
    FIRST_ID,
    ID_COLUMN,
    ID_TYPE,
    VALID_TYPES,
)
from primitive_db.decorators import confirm_action, handle_db_errors, log_time


def find_table_name(metadata, table_name):
    """Ищет таблицу с таким же именем без учёта регистра."""
    for name in metadata:
        if name.casefold() == table_name.casefold():
            return name
    return None


def check_table_exists(metadata, table_name):
    """Выбрасывает KeyError, если таблицы нет."""
    if table_name not in metadata:
        raise KeyError(f'Таблица "{table_name}" не существует.')


def get_table_columns(metadata, table_name):
    """Возвращает столбцы таблицы и их типы."""
    check_table_exists(metadata, table_name)
    return dict(
        column.split(COLUMN_TYPE_SEPARATOR, 1) for column in metadata[table_name]
    )


def validate_name(name):
    """Проверяет имя таблицы или столбца."""
    if not name.isidentifier():
        raise ValueError(f"{name} (имя должно состоять из букв, цифр и _)")


def validate_values(columns, values):
    """Проверяет, что столбцы существуют и типы значений совпадают."""
    for name, value in values.items():
        if name not in columns:
            raise KeyError(f'Столбец "{name}" не существует.')
        column_type = columns[name]
        if type(value) is not VALID_TYPES[column_type]:
            raise ValueError(f"{value!r} (столбец {name} имеет тип {column_type})")


def matches(row, where_clause):
    """Проверяет, подходит ли строка под условие WHERE."""
    return all(
        type(row.get(name)) is type(value) and row[name] == value
        for name, value in where_clause.items()
    )


def find_row_ids(table_data, where_clause):
    """Возвращает ID строк, подходящих под условие WHERE."""
    return [row[ID_COLUMN] for row in table_data if matches(row, where_clause)]


@handle_db_errors
def create_table(metadata, table_name, columns):
    """Добавляет новую таблицу в метаданные, столбец ID:int ставится первым."""
    existing_name = find_table_name(metadata, table_name)
    if existing_name is not None:
        raise KeyError(f'Таблица "{existing_name}" уже существует.')
    validate_name(table_name)

    schema = [f"{ID_COLUMN}{COLUMN_TYPE_SEPARATOR}{ID_TYPE}"]
    column_names = set()
    for column in columns:
        name, separator, column_type = column.partition(COLUMN_TYPE_SEPARATOR)
        if not separator or column_type not in VALID_TYPES:
            raise ValueError(column)
        validate_name(name)
        if name in column_names:
            raise ValueError(f"{name} (столбец указан дважды)")
        column_names.add(name)

        if name == ID_COLUMN:
            if column_type != ID_TYPE:
                raise ValueError(f"{column} (столбец ID должен иметь тип int)")
            continue
        schema.append(column)

    metadata[table_name] = schema
    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata, table_name):
    """Удаляет таблицу из метаданных."""
    check_table_exists(metadata, table_name)
    del metadata[table_name]
    return metadata


@handle_db_errors
@log_time
def insert(metadata, table_name, values, table_data):
    """Проверяет значения и добавляет строку с новым ID."""
    columns = get_table_columns(metadata, table_name)
    columns.pop(ID_COLUMN)
    if len(values) != len(columns):
        raise ValueError(
            f"передано значений: {len(values)}, нужно: {len(columns)} "
            f"({', '.join(columns)})"
        )

    new_row = dict(zip(columns, values))
    validate_values(columns, new_row)

    last_id = max((row[ID_COLUMN] for row in table_data), default=FIRST_ID - 1)
    table_data.append({ID_COLUMN: last_id + 1, **new_row})
    return table_data


@log_time
def select(table_data, where_clause=None):
    """Возвращает все строки или строки, подходящие под условие WHERE."""
    if not where_clause:
        return list(table_data)
    return [row for row in table_data if matches(row, where_clause)]


@handle_db_errors
def update(table_data, set_clause, where_clause):
    """Обновляет поля строк, подходящих под условие WHERE."""
    if ID_COLUMN in set_clause:
        raise ValueError(f"{ID_COLUMN} (этот столбец нельзя изменять)")
    return [
        {**row, **set_clause} if matches(row, where_clause) else row
        for row in table_data
    ]


@handle_db_errors
@confirm_action("удаление записей")
def delete(table_data, where_clause):
    """Удаляет строки, подходящие под условие WHERE."""
    return [row for row in table_data if not matches(row, where_clause)]
