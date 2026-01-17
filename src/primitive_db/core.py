from __future__ import annotations

import os
from typing import Any

from prettytable import PrettyTable

from .decorators import confirm_action, handle_db_errors, log_time
from .utils import (
    cast_value,
    load_table_data,
    parse_column_def,
    save_table_data,
    schema_for_table,
    table_path,
)


# ID формируется как (max(ID) + 1) по текущим данным таблицы
def _next_id(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 1
    ids = [r.get("ID", 0) for r in rows if isinstance(r.get("ID", None), int)]
    return (max(ids) + 1) if ids else 1


def print_rows(schema: list[dict[str, str]], rows: list[dict[str, Any]]) -> None:
    headers = [c["name"] for c in schema]
    table = PrettyTable()
    table.field_names = headers
    for row in rows:
        table.add_row([row.get(h) for h in headers])
    print(table)

@handle_db_errors
def create_table(
    metadata: dict[str, list[dict[str, str]]],
    table_name: str,
    columns: list[str],
) -> dict[str, list[dict[str, str]]] | None:
    if table_name in metadata:
        raise ValueError(f'Ошибка: Таблица "{table_name}" уже существует.')

    schema: list[dict[str, str]] = [{"name": "ID", "type": "int"}]
    for col_def in columns:
        name, typ = parse_column_def(col_def)
        schema.append({"name": name, "type": typ})

    metadata[table_name] = schema
    print(
        f'Таблица "{table_name}" успешно создана со столбцами: '
        + ", ".join([f'{c["name"]}:{c["type"]}' for c in schema])
    )
    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(
    metadata: dict[str, list[dict[str, str]]],
    table_name: str,
) -> dict[str, list[dict[str, str]]] | None:
    if table_name not in metadata:
        raise KeyError(f'Ошибка: Таблица "{table_name}" не существует.')

    del metadata[table_name]
    path = table_path(table_name)
    if path.exists():
        os.remove(path)

    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


@handle_db_errors
def list_tables(metadata: dict[str, list[dict[str, str]]]) -> None:
    for name in sorted(metadata.keys()):
        print(f"- {name}")


@handle_db_errors
def info(metadata: dict[str, list[dict[str, str]]], table_name: str) -> None:
    schema = schema_for_table(metadata, table_name)
    rows = load_table_data(table_name)
    cols = ", ".join([f'{c["name"]}:{c["type"]}' for c in schema])

    print("Таблица:")
    print(table_name)
    print(f"Столбцы: {cols}")
    print(f"Количество записей: {len(rows)}")


@handle_db_errors
@log_time
def insert(
    metadata: dict[str, list[dict[str, str]]],
    table_name: str,
    values: list[str],
) -> int | None:
    schema = schema_for_table(metadata, table_name)
    expected = len(schema) - 1
    if len(values) != expected:
        raise ValueError(f"Некорректное значение: {values}. Попробуйте снова.")

    rows = load_table_data(table_name)
    row: dict[str, Any] = {"ID": _next_id(rows)}

    for i, col in enumerate(schema[1:], start=0):
        row[col["name"]] = cast_value(values[i], col["type"])

    rows.append(row)
    save_table_data(table_name, rows)

    new_id = int(row["ID"])
    print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".')
    return new_id


@handle_db_errors
@log_time
def select(
    metadata: dict[str, list[dict[str, str]]],
    table_name: str,
    where: dict[str, Any] | None = None,
) -> list[dict[str, Any]] | None:
    schema = schema_for_table(metadata, table_name)
    rows = load_table_data(table_name)

    if where is not None:
        (wcol, wval_raw), = where.items()
        col_types = {c["name"]: c["type"] for c in schema}
        if wcol not in col_types:
            raise ValueError(f"Некорректное значение: {wcol}. Попробуйте снова.")
        wval = cast_value(wval_raw, col_types[wcol])
        rows = [row for row in rows if row.get(wcol) == wval]

    print_rows(schema, rows)
    return rows


@handle_db_errors
def update(
    metadata: dict[str, list[dict[str, str]]],
    table_name: str,
    set_clause: dict[str, Any],
    where_clause: dict[str, Any],
) -> int | None:
    schema = schema_for_table(metadata, table_name)
    rows = load_table_data(table_name)
    col_types = {c["name"]: c["type"] for c in schema}

    (wcol, wval_raw), = where_clause.items()
    if wcol not in col_types:
        raise ValueError(f"Некорректное значение: {wcol}. Попробуйте снова.")
    wval = cast_value(wval_raw, col_types[wcol])

    casted_set: dict[str, Any] = {}
    for k, v in set_clause.items():
        if k not in col_types or k == "ID":
            raise ValueError(f"Некорректное значение: {k}. Попробуйте снова.")
        casted_set[k] = cast_value(v, col_types[k])

    updated_ids: list[int] = []
    for r in rows:
        if r.get(wcol) == wval:
            for k, v in casted_set.items():
                r[k] = v
            if isinstance(r.get("ID"), int):
                updated_ids.append(int(r["ID"]))

    if not updated_ids:
        print(f'Записи по условию не найдены в таблице "{table_name}".')
        return 0

    save_table_data(table_name, rows)

    if len(updated_ids) == 1:
        print(
            f'Запись с ID={updated_ids[0]} в таблице "{table_name}" '
            "успешно обновлена."
        )
    else:
        print(f'Обновлено {len(updated_ids)} записей в таблице "{table_name}".')
    return len(updated_ids)


@handle_db_errors
@confirm_action("удаление записи")
def delete(
    metadata: dict[str, list[dict[str, str]]],
    table_name: str,
    where_clause: dict[str, Any],
) -> int | None:
    schema = schema_for_table(metadata, table_name)
    rows = load_table_data(table_name)
    col_types = {c["name"]: c["type"] for c in schema}

    (wcol, wval_raw), = where_clause.items()
    if wcol not in col_types:
        raise ValueError(f"Некорректное значение: {wcol}. Попробуйте снова.")
    wval = cast_value(wval_raw, col_types[wcol])

    kept: list[dict[str, Any]] = []
    deleted_ids: list[int] = []
    for r in rows:
        if r.get(wcol) == wval:
            if isinstance(r.get("ID"), int):
                deleted_ids.append(int(r["ID"]))
        else:
            kept.append(r)

    if not deleted_ids:
        print(f'Записи по условию не найдены в таблице "{table_name}".')
        return 0

    save_table_data(table_name, kept)

    if len(deleted_ids) == 1:
        print(
            f'Запись с ID={deleted_ids[0]} успешно удалена из таблицы "{table_name}".'
        )
    else:
        print(f'Удалено {len(deleted_ids)} записей из таблицы "{table_name}".')
    return len(deleted_ids)