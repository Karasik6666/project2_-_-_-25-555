from __future__ import annotations

import shlex
from typing import Any

import prompt

from . import core
from .decorators import create_cacher
from .parser import parse_condition, parse_set_clause, parse_values_list
from .utils import load_metadata, save_metadata


def welcome() -> None:
    print("\n***")
    print("<command> exit - выйти из программы")
    print("<command> help - справочная информация")


def _print_help() -> None:
    print("***База данных***")
    print("Функции:")
    print(
        "<command> create_table <имя_таблицы> <столбец1:тип> <столбец2:тип> .. - "
        "создать таблицу"
    )
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print(
        "<command> insert into <имя_таблицы> values (<значение1>, <значение2>, ...) - "
        "создать запись."
    )
    print(
        "<command> select from <имя_таблицы> where <столбец> = <значение> - "
        "прочитать записи по условию."
    )
    print("<command> select from <имя_таблицы> - прочитать все записи.")
    print(
        "<command> update <имя_таблицы> set <столбец1> = <новое_значение1> where "
        "<столбец_условия> = <значение_условия> - обновить запись."
    )
    print(
        "<command> delete from <имя_таблицы> where <столбец> = <значение> - "
        "удалить запись."
    )
    print("<command> info <имя_таблицы> - вывести информацию о таблице.")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация")


def _read_command() -> str:
    return prompt.string(">>>Введите команду: ").strip()


def run() -> None:
    cache_result = create_cacher()

    while True:
        metadata = load_metadata()

        try:
            user_input = _read_command()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue

        if user_input == "exit":
            break
        if user_input == "help":
            _print_help()
            continue
        if user_input == "list_tables":
            core.list_tables(metadata)
            continue

        try:
            args = shlex.split(user_input)
        except ValueError as e:
            print(f"Некорректное значение: {e}. Попробуйте снова.")
            continue

        if not args:
            continue

        cmd0 = args[0]
        low = user_input.lower()

        # операции управления таблицами
        if cmd0 == "create_table":
            if len(args) < 3:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            table_name = args[1]
            columns = args[2:]
            updated = core.create_table(metadata, table_name, columns)
            if updated is not None:
                save_metadata(updated)
                cache_result.clear()
            continue

        if cmd0 == "drop_table":
            if len(args) != 2:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            table_name = args[1]
            updated = core.drop_table(metadata, table_name)
            if updated is not None:
                save_metadata(updated)
                cache_result.clear()
            continue

        if cmd0 == "info":
            if len(args) != 2:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            core.info(metadata, args[1])
            continue

        # вставка записи
        if low.startswith("insert into "):
            try:
                head, tail = user_input.split("values", 1)
                head_args = shlex.split(head.strip())
                table_name = head_args[2]
                values = parse_values_list(tail.strip())
            except Exception:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue

            res = core.insert(metadata, table_name, values)
            if res is not None:
                cache_result.clear()
            continue

        # чтение данных (с кэшированием)
        if low.startswith("select from "):
            try:
                after_from = user_input.split("from", 1)[1].strip()
                if " where " in after_from.lower():
                    left, where_raw = after_from.split("where", 1)
                    table_name = shlex.split(left.strip())[0]
                    where = parse_condition(where_raw.strip())
                else:
                    table_name = shlex.split(after_from.strip())[0]
                    where = None
            except Exception:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue

            key = (
                "select",
                table_name,
                tuple(sorted(where.items())) if where else None,
            )

            def _on_cache_hit(rows: list[dict[str, Any]] | None) -> None:
                if rows is None:
                    return
                schema = core.schema_for_table(metadata, table_name)
                core.print_rows(schema, rows)

            cache_result(
                key,
                lambda: core.select(metadata, table_name, where),
                on_hit=_on_cache_hit,
            )
            continue

        # обновление записей
        if low.startswith("update "):
            try:
                rest = user_input[len("update ") :].strip()
                table_part, rest2 = rest.split("set", 1)
                table_name = shlex.split(table_part.strip())[0]
                set_raw, where_raw = rest2.split("where", 1)
                set_clause = parse_set_clause(set_raw.strip())
                where_clause = parse_condition(where_raw.strip())
            except Exception:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue

            res = core.update(metadata, table_name, set_clause, where_clause)
            if res is not None:
                cache_result.clear()
            continue

        # удаление записей
        if low.startswith("delete from "):
            try:
                rest = user_input[len("delete from ") :].strip()
                table_part, where_raw = rest.split("where", 1)
                table_name = shlex.split(table_part.strip())[0]
                where_clause = parse_condition(where_raw.strip())
            except Exception:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue

            res = core.delete(metadata, table_name, where_clause)
            if res is not None:
                cache_result.clear()
            continue

        print(f"Функции {cmd0} нет. Попробуйте снова.")