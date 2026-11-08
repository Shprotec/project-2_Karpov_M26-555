"""Чтение и запись JSON-файлов."""

import json
import os

from primitive_db.constants import (
    DATA_DIR,
    DATA_FILE_EXTENSION,
    FILE_ENCODING,
    JSON_INDENT,
)


def load_json(filepath, default):
    """Читает JSON-файл, если его нет — возвращает default."""
    try:
        with open(filepath, encoding=FILE_ENCODING) as file:
            return json.load(file)
    except FileNotFoundError:
        return default


def save_json(filepath, data):
    """Записывает данные в JSON-файл."""
    directory = os.path.dirname(filepath)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(filepath, "w", encoding=FILE_ENCODING) as file:
        json.dump(data, file, ensure_ascii=False, indent=JSON_INDENT)


def load_metadata(filepath):
    """Загружает схему таблиц из JSON-файла."""
    return load_json(filepath, {})


def save_metadata(filepath, data):
    """Сохраняет схему таблиц в JSON-файл."""
    save_json(filepath, data)


def get_table_path(table_name):
    """Возвращает путь к файлу с данными таблицы."""
    return os.path.join(DATA_DIR, f"{table_name}{DATA_FILE_EXTENSION}")


def load_table_data(table_name):
    """Загружает список строк таблицы."""
    return load_json(get_table_path(table_name), [])


def save_table_data(table_name, data):
    """Сохраняет список строк таблицы."""
    save_json(get_table_path(table_name), data)


def remove_table_data(table_name):
    """Удаляет файл строк, если он был создан."""
    filepath = get_table_path(table_name)
    if os.path.exists(filepath):
        os.remove(filepath)
