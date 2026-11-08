import shlex

import prompt

from primitive_db.core import create_table, drop_table
from primitive_db.utils import load_metadata, save_metadata

META_FILE = "db_meta.json"
HELP_TEXT = (
    "create_table <таблица> <столбец:тип> ... — создать таблицу\n"
    "list_tables — показать список таблиц\n"
    "drop_table <таблица> — удалить таблицу\n"
    "help — показать справку\n"
    "exit — выйти"
)


def run() -> None:
    """Читает и выполняет команды пользователя."""
    print(HELP_TEXT)

    while True:
        user_input = prompt.string("Введите команду: ")

        try:
            parts = shlex.split(user_input)
            if not parts:
                continue

            command, *args = parts
            command = command.lower()

            if command == "exit":
                return
            elif command == "help":
                print(HELP_TEXT)
            elif command == "create_table":
                if len(args) < 2:
                    print("Пример: create_table users name:str age:int")
                    continue

                table_name, *columns = args
                metadata = load_metadata(META_FILE)
                create_table(metadata, table_name, columns)
                save_metadata(META_FILE, metadata)
                print(f'Таблица "{table_name}" создана.')
            elif command == "list_tables":
                metadata = load_metadata(META_FILE)

                if metadata:
                    for table_name in metadata:
                        print(table_name)
                else:
                    print("Таблиц пока нет.")
            elif command == "drop_table":
                if len(args) != 1:
                    print("Пример: drop_table demo")
                    continue

                table_name = args[0]
                metadata = load_metadata(META_FILE)
                drop_table(metadata, table_name)
                save_metadata(META_FILE, metadata)
                print(f'Таблица "{table_name}" удалена.')
            else:
                print(f"Неизвестная команда: {command}")
        except ValueError as error:
            print(f"Ошибка: {error}")

