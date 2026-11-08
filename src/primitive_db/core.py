from primitive_db.constants import ID_COLUMN, ID_TYPE, VALID_TYPES
from primitive_db.decorators import confirm_action, handle_db_errors, log_time
from primitive_db.utils import load_table_data, validate_table_name


def has_table_name(metadata, table_name):
    """Проверяет, занято ли имя таблицы с учётом регистра файловой системы."""
    return any(name.casefold() == table_name.casefold() for name in metadata)


@handle_db_errors
def create_table(metadata, table_name, columns):
    """Добавляет схему новой таблицы в метаданные."""
    validate_table_name(table_name)
    if has_table_name(metadata, table_name):
        raise ValueError(f"Таблица {table_name} уже существует.")

    schema = [f"{ID_COLUMN}:{ID_TYPE}"]
    column_names = set()

    for column in columns:
        name, separator, column_type = column.partition(":")

        if not name or not separator or column_type not in VALID_TYPES:
            raise ValueError(f"Некорректный столбец: {column}")
        if name in column_names:
            raise ValueError(f"Столбец {name} указан дважды.")

        column_names.add(name)

        if name == ID_COLUMN and column_type != ID_TYPE:
            raise ValueError("Столбец ID должен иметь тип int.")
        if name != ID_COLUMN:
            schema.append(column)

    metadata[table_name] = schema
    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata, table_name):
    """Удаляет таблицу из метаданных."""
    if table_name not in metadata:
        raise ValueError(f"Таблица {table_name} не существует.")

    del metadata[table_name]
    return metadata


def get_table_columns(metadata, table_name):
    """Возвращает столбцы и их типы в порядке схемы."""
    if table_name not in metadata:
        raise KeyError(f"Таблица {table_name} не существует.")
    if any(
        name != table_name and name.casefold() == table_name.casefold()
        for name in metadata
    ):
        raise ValueError(
            f"Имя таблицы {table_name} совпадает с другим без учёта регистра."
        )
    validate_table_name(table_name)
    return dict(column.split(":", 1) for column in metadata[table_name])


def validate_values(columns, values):
    """Проверяет имена и типы столбцов в переданных значениях."""
    for name, value in values.items():
        if name not in columns:
            raise ValueError(f"Столбец {name} не существует.")
        column_type = columns[name]
        if type(value) is not VALID_TYPES[column_type]:
            raise ValueError(f"Столбец {name} ожидает значение типа {column_type}.")


@handle_db_errors
@log_time
def insert(metadata, table_name, values):
    """Добавляет строку в список записей таблицы."""
    columns = get_table_columns(metadata, table_name)
    columns.pop(ID_COLUMN)
    if len(values) != len(columns):
        raise ValueError(f"Ожидалось {len(columns)} значений, получено {len(values)}.")

    new_row = dict(zip(columns, values))
    validate_values(columns, new_row)

    table_data = load_table_data(table_name)
    next_id = max((row[ID_COLUMN] for row in table_data), default=0) + 1
    table_data.append({ID_COLUMN: next_id, **new_row})
    return table_data


def _matches(row, where_clause):
    return all(
        type(row.get(name)) is type(value) and row[name] == value
        for name, value in where_clause.items()
    )


@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    """Возвращает строки, подходящие под условия WHERE."""
    if where_clause is None:
        return table_data
    return [row for row in table_data if _matches(row, where_clause)]


@handle_db_errors
def update(table_data, set_clause, where_clause):
    """Обновляет поля строк, подходящих под условия WHERE."""
    if not set_clause or not where_clause:
        raise ValueError("Для update нужны условия SET и WHERE.")
    if ID_COLUMN in set_clause:
        raise ValueError("Столбец ID изменять нельзя.")
    return [
        {**row, **set_clause} if _matches(row, where_clause) else row
        for row in table_data
    ]


@handle_db_errors
@confirm_action("удаление записей")
def delete(table_data, where_clause):
    """Удаляет строки, подходящие под условия WHERE."""
    if not where_clause:
        raise ValueError("Для delete нужно условие WHERE.")
    return [row for row in table_data if not _matches(row, where_clause)]
