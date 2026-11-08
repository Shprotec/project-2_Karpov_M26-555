"""Константы базы данных."""

# Хранение данных
META_FILE = "db_meta.json"
DATA_DIR = "data"
DATA_FILE_EXTENSION = ".json"
FILE_ENCODING = "utf-8"
JSON_INDENT = 4

# Схема таблиц
ID_COLUMN = "ID"
ID_TYPE = "int"
FIRST_ID = 1
VALID_TYPES = {"int": int, "str": str, "bool": bool}
COLUMN_TYPE_SEPARATOR = ":"

# Значения в командах
BOOL_TRUE = "true"
BOOL_FALSE = "false"
VALUES_SEPARATOR = ","

# Команды
CMD_CREATE_TABLE = "create_table"
CMD_LIST_TABLES = "list_tables"
CMD_DROP_TABLE = "drop_table"
CMD_INSERT = "insert"
CMD_SELECT = "select"
CMD_UPDATE = "update"
CMD_DELETE = "delete"
CMD_INFO = "info"
CMD_HELP = "help"
CMD_EXIT = "exit"

# Ключевые слова команд
KW_INTO = "into"
KW_FROM = "from"
KW_VALUES = "values"
KW_WHERE = "where"
KW_SET = "set"
KW_AND = "and"

# Взаимодействие с пользователем
PROMPT_MESSAGE = ">>>Введите команду: "
CONFIRM_YES = "y"
TIME_PRECISION = 3
