from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

K = TypeVar("K")
V = TypeVar("V")

# Централизованная обработка типовых пользовательских и файловых ошибок
def handle_db_errors(func: Callable[..., Any]) -> Callable[..., Any]:
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
        except Exception as e:
            print(f"Произошла непредвиденная ошибка: {e}")
            return None

    return wrapper

# Декоратор подтверждения применяется к операциям с необратимым эффектом (drop/delete)
def confirm_action(
    action_name: str,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            answer = input(
                f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
            ).strip().lower()
            if answer != "y":
                print("Операция отменена.")
                return None
            return func(*args, **kwargs)

        return wrapper

    return decorator

# Время измеряется по монотонным часам для исключения влияния системных корректировок
def log_time(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.monotonic()
        result = func(*args, **kwargs)
        end = time.monotonic()
        print(f"Функция {func.__name__} выполнилась за {end - start:.3f} секунд")
        return result

    return wrapper


def create_cacher() -> Callable[
    [K, Callable[[], V], Optional[Callable[[V], None]]],
    V,
]:
    # Кэширование реализовано через замыкание (in-memory) 
    # и используется для повторных select
    cache: dict[K, V] = {}

    def cache_result(
        key: K,
        value_func: Callable[[], V],
        on_hit: Optional[Callable[[V], None]] = None,
    ) -> V:
        if key in cache:
            value = cache[key]
            if on_hit is not None:
                on_hit(value)
            return value

        value = value_func()
        cache[key] = value
        return value

    def clear() -> None:
        cache.clear()

    setattr(cache_result, "clear", clear)
    return cache_result