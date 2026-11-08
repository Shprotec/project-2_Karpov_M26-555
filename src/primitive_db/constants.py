"""Пути хранения и типы столбцов."""

META_FILE = "db_meta.json"
DATA_DIR = "data"
ID_COLUMN = "ID"
ID_TYPE = "int"
VALID_TYPES = {"int": int, "str": str, "bool": bool}

INVALID_FILENAME_CHARS = '/\\:<>"|?*'
WINDOWS_DEVICE_NAMES = {
    "AUX",
    "CON",
    "CONIN$",
    "CONOUT$",
    "NUL",
    "PRN",
    *(f"{prefix}{digit}" for prefix in ("COM", "LPT") for digit in "123456789¹²³"),
}
