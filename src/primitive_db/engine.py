import prompt

HELP_TEXT = (
    "<command> exit - выйти из программы\n<command> help - справочная информация"
)


def welcome() -> None:
    """Показывает справку и обрабатывает команды."""
    print("Первая попытка запустить проект!")
    print("\n***")
    print(HELP_TEXT)

    while True:
        command = prompt.string("Введите команду: ").strip().lower()

        if command == "exit":
            return
        if command == "help":
            print(f"\n{HELP_TEXT}")
        else:
            print(f"Неизвестная команда: {command}")
