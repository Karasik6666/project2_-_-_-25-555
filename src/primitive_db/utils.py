from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .constants import DATA_DIR, META_FILE, VALID_TYPES


def project_root() -> Path:
    return Path(os.getcwd())


def data_dir() -> Path:
    p = project_root() / DATA_DIR
    p.mkdir(parents=True, exist_ok=True)
    return p


def metadata_path() -> Path:
    return project_root() / META_FILE


def table_path(table_name: str) -> Path:
    return data_dir() / f"{table_name}.json"


def load_metadata() -> dict[str, list[dict[str, str]]]:
    try:
        raw = metadata_path().read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return {}

    if not raw:
        return {}

    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Некорректная структура metadata")
    return data


def save_metadata(metadata: dict[str, list[dict[str, str]]]) -> None:
    # Сериализация метаданных выполняется в читаемом формате (indent) 
    # для удобства контроля
    content = json.dumps(metadata, ensure_ascii=False, indent=2)
    metadata_path().write_text(content, encoding="utf-8")


def load_table_data(table_name: str) -> list[dict[str, Any]]:
    # Отсутствие файла таблицы интерпретируется как отсутствие записей.
    try:
        raw = table_path(table_name).read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return []

    if not raw:
        return []

    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("Некорректная структура данных таблицы")

    return data


def save_table_data(table_name: str, data: list[dict[str, Any]]) -> None:
    # Данные таблицы сохраняются в JSON с отключением ASCII-экранирования
    content = json.dumps(data, ensure_ascii=False, indent=2)
    table_path(table_name).write_text(content, encoding="utf-8")


def schema_for_table(
    metadata: dict[str, list[dict[str, str]]],
    table_name: str,
) -> list[dict[str, str]]:
    if table_name not in metadata:
        raise KeyError(f'Ошибка: Таблица "{table_name}" не существует.')
    schema = metadata[table_name]
    if not isinstance(schema, list):
        raise ValueError("Некорректная схема таблицы")
    return schema


def parse_column_def(col_def: str) -> tuple[str, str]:
    if ":" not in col_def:
        raise ValueError(f"Некорректное значение: {col_def}. Попробуйте снова.")
    name, typ = col_def.split(":", 1)
    name = name.strip()
    typ = typ.strip()
    if not name or not typ:
        raise ValueError(f"Некорректное значение: {col_def}. Попробуйте снова.")
    if typ not in VALID_TYPES:
        raise ValueError(f"Некорректное значение: {typ}. Попробуйте снова.")
    if name.upper() == "ID":
        raise ValueError("Некорректное значение: ID. Попробуйте снова.")
    return name, typ


def cast_value(value: object, target_type: str) -> Any:
    if target_type not in VALID_TYPES:
        raise ValueError(f"Некорректное значение: {target_type}. Попробуйте снова.")

    if target_type == "bool":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            v = value.strip().lower()
            if v in {"true", "1"}:
                return True
            if v in {"false", "0"}:
                return False
        raise ValueError(f"Некорректное значение: {value}. Попробуйте снова.")

    if target_type == "int":
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        if isinstance(value, str):
            try:
                return int(value.strip())
            except ValueError as e:
                raise ValueError(
                    f"Некорректное значение: {value}. Попробуйте снова."
                ) from e
        raise ValueError(f"Некорректное значение: {value}. Попробуйте снова.")

    if target_type == "str":
        if isinstance(value, str):
            v = value.strip()
            if len(v) >= 2 and ((v[0] == v[-1] == '"') or (v[0] == v[-1] == "'")):
                return v[1:-1]
            return v
        return str(value)

    if isinstance(value, str):
        return value
    return str(value)