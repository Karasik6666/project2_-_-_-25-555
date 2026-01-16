from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable


def handle_db_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """Единая обработка бизнес-ошибок и ошибок валидации."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except (KeyError, ValueError, FileNotFoundError) as e:
            msg = str(e)
            if msg.startswith("'") and msg.endswith("'"):
                msg = msg[1:-1]
            print(msg)
            return None
        except Exception as e:  # noqa: BLE001
            print(f"Произошла непредвиденная ошибка: {e}")
            return None
    return wrapper


def confirm_action(action_name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Подтверждение опасных операций (drop/delete)."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            answer = input(f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: ').strip().lower()
            if answer != "y":
                print("Операция отменена.")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_time(func: Callable[..., Any]) -> Callable[..., Any]:
    """Логирование времени выполнения (учебная механика)."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.monotonic()
        result = func(*args, **kwargs)
        end = time.monotonic()
        print(f"Функция {func.__name__} выполнилась за {end - start:.3f} секунд")
        return result
    return wrapper


def create_cacher():
    """Кэширование результатов через замыкание (используется для select)."""
    cache: dict[object, object] = {}

    def cache_result(key, value_func):
        if key in cache:
            return cache[key]
        value = value_func()
        cache[key] = value
        return value

    def clear() -> None:
        cache.clear()

    cache_result.clear = clear  # type: ignore[attr-defined]
    return cache_result