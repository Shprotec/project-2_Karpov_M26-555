"""Обработка ошибок, подтверждение команд, время и кэш."""

import time


def handle_db_errors(function):
    """Показывает ошибки базы и возвращает управление консоли."""
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except KeyError as error:
            print(f"Ошибка: {error.args[0]}")
        except (ValueError, OSError) as error:
            print(f"Ошибка: {error}")

    return wrapper


def confirm_action(action_name):
    """Запрашивает подтверждение перед удалением."""
    def decorator(function):
        def wrapper(*args, **kwargs):
            answer = input(f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: ')
            if answer.strip().lower() != "y":
                print("Операция отменена.")
                return None
            return function(*args, **kwargs)

        return wrapper

    return decorator


def log_time(function):
    """Показывает время выполнения операции."""
    def wrapper(*args, **kwargs):
        start = time.monotonic()
        try:
            return function(*args, **kwargs)
        finally:
            elapsed = time.monotonic() - start
            print(f"Функция {function.__name__} выполнилась за {elapsed:.3f} секунд.")

    return wrapper


def create_cacher():
    """Возвращает функцию, запоминающую результат по ключу."""
    cache = {}

    def cache_result(key, value_func):
        if key not in cache:
            cache[key] = value_func()
        return cache[key]

    return cache_result
