import json
import os

from primitive_db.constants import (
    DATA_DIR,
    INVALID_FILENAME_CHARS,
    WINDOWS_DEVICE_NAMES,
)


def _load_json(filepath, default):
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return default


def _save_json(filepath, data):
    temporary_path = f"{filepath}.{os.urandom(8).hex()}.tmp"
    temporary_file = open(temporary_path, "x", encoding="utf-8")
    try:
        with temporary_file:
            json.dump(data, temporary_file, ensure_ascii=False, indent=4)
        os.replace(temporary_path, filepath)
    finally:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)


def load_metadata(filepath):
    """Загружает схему таблиц из JSON-файла."""
    return _load_json(filepath, {})


def save_metadata(filepath, data):
    """Сохраняет схему таблиц в JSON-файл."""
    _save_json(filepath, data)


def validate_table_name(table_name):
    """Проверяет, можно ли хранить строки таблицы в отдельном файле."""
    first_part = table_name.split(".", 1)[0].rstrip().upper()
    if (
        not table_name.strip()
        or table_name in {".", ".."}
        or first_part in WINDOWS_DEVICE_NAMES
        or any(char in INVALID_FILENAME_CHARS or ord(char) < 32 for char in table_name)
    ):
        raise ValueError("Недопустимое имя таблицы.")


def _table_data_path(table_name):
    validate_table_name(table_name)
    return os.path.join(DATA_DIR, f"{table_name}.json")


def load_table_data(table_name):
    """Загружает список строк таблицы."""
    return _load_json(_table_data_path(table_name), [])


def save_table_data(table_name, data):
    """Сохраняет список строк таблицы."""
    filepath = _table_data_path(table_name)
    os.makedirs(DATA_DIR, exist_ok=True)
    _save_json(filepath, data)


def remove_table_data(table_name):
    """Удаляет файл строк, если он был создан."""
    try:
        os.remove(_table_data_path(table_name))
    except FileNotFoundError:
        pass


def save_dropped_table(filepath, metadata, table_name):
    """Сохраняет схему без таблицы и удаляет её файл строк."""
    try:
        rows_path = _table_data_path(table_name)
    except ValueError:
        # У таблиц с устаревшими именами не могло быть записей в базе.
        save_metadata(filepath, metadata)
        return

    backup_path = f"{rows_path}.{os.urandom(8).hex()}.tmp"
    try:
        os.replace(rows_path, backup_path)
    except FileNotFoundError:
        save_metadata(filepath, metadata)
        return

    try:
        save_metadata(filepath, metadata)
    except OSError:
        os.replace(backup_path, rows_path)
        raise
    os.remove(backup_path)


def table_data_version(table_name):
    """Возвращает версию файла для проверки актуальности кэша."""
    try:
        status = os.stat(_table_data_path(table_name))
    except FileNotFoundError:
        return None
    return status.st_mtime_ns, status.st_size, status.st_ino
