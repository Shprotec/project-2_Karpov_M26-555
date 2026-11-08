"""Обработка ошибок, подтверждение команд, время и кэш."""

import time

from primitive_db.constants import CONFIRM_YES, TIME_PRECISION


def get_error_message(error):
    """Возвращает текст ошибки без лишних кавычек."""
    return error.args[0] if error.args else str(error)


def handle_db_errors(function):
    """Показывает ошибки базы и возвращает управление консоли."""

    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except FileNotFoundError:
            print(
                "Ошибка: Файл данных не найден. "
                "Возможно, база данных не инициализирована."
            )
        except KeyError as error:
            print(f"Ошибка: {get_error_message(error)}")
        except ValueError as error:
            print(f"Некорректное значение: {error}. Попробуйте снова.")
        except Exception as error:
            print(f"Произошла непредвиденная ошибка: {error}")
        return None

    return wrapper


def confirm_action(action_name):
    """Запрашивает подтверждение перед удалением."""

    def decorator(function):
        def wrapper(*args, **kwargs):
            question = f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
            if input(question).strip().lower() != CONFIRM_YES:
                print("Операция отменена.")
                return None
            return function(*args, **kwargs)

        return wrapper

    return decorator


def log_time(function):
    """Показывает время выполнения операции."""

    def wrapper(*args, **kwargs):
        start = time.monotonic()
        result = function(*args, **kwargs)
        elapsed = time.monotonic() - start
        print(
            f"Функция {function.__name__} выполнилась "
            f"за {elapsed:.{TIME_PRECISION}f} секунд"
        )
        return result

    return wrapper


def create_cacher():
    """Возвращает функцию, запоминающую результат по ключу.

    У функции есть метод clear(), который очищает кэш.
    """
    cache = {}

    def cache_result(key, value_func):
        if key not in cache:
            cache[key] = value_func()
        return cache[key]

    cache_result.clear = cache.clear
    return cache_result
