VALID_TYPES = {"int", "str", "bool"}


def create_table(metadata, table_name, columns):
    """Добавляет схему новой таблицы в метаданные."""
    if table_name in metadata:
        raise ValueError(f"Таблица {table_name} уже существует.")

    schema = ["ID:int"]
    column_names = set()

    for column in columns:
        name, separator, column_type = column.partition(":")

        if not name or not separator or column_type not in VALID_TYPES:
            raise ValueError(f"Некорректный столбец: {column}")
        if name in column_names:
            raise ValueError(f"Столбец {name} указан дважды.")

        column_names.add(name)

        if name == "ID" and column_type != "int":
            raise ValueError("Столбец ID должен иметь тип int.")
        if name != "ID":
            schema.append(column)

    metadata[table_name] = schema
    return metadata


def drop_table(metadata, table_name):
    """Удаляет таблицу из метаданных."""
    if table_name not in metadata:
        raise ValueError(f"Таблица {table_name} не существует.")

    del metadata[table_name]
    return metadata