from __future__ import annotations

import re
from typing import Any


def _strip_outer_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and ((s[0] == s[-1] == '"') or (s[0] == s[-1] == "'")):
        return s[1:-1]
    return s

# Разбор части values (...) с корректной обработкой запятых внутри кавычек
def parse_values_list(raw: str) -> list[str]:
    s = raw.strip()
    if not (s.startswith("(") and s.endswith(")")):
        raise ValueError(f"Некорректное значение: {raw}. Попробуйте снова.")

    inner = s[1:-1].strip()
    if not inner:
        return []

    parts = re.split(r""",(?=(?:[^'"]|'[^']*'|"[^"]*")*$)""", inner)
    return [p.strip() for p in parts]

# Преобразование выражения вида "age = 28" в словарь { "age": "28" }
def parse_condition(expr: str) -> dict[str, Any]:
    if "=" not in expr:
        raise ValueError(f"Некорректное значение: {expr}. Попробуйте снова.")

    left, right = expr.split("=", 1)
    col = left.strip()
    val = right.strip()

    if not col:
        raise ValueError(f"Некорректное значение: {expr}. Попробуйте снова.")

    return {col: _strip_outer_quotes(val)}

# Разбор части set: "age = 29, is_active = false" -> {"age":"29", "is_active":"false"}
def parse_set_clause(raw: str) -> dict[str, Any]:
    s = raw.strip()
    if not s:
        raise ValueError(f"Некорректное значение: {raw}. Попробуйте снова.")

    parts = re.split(r""",(?=(?:[^'"]|'[^']*'|"[^"]*")*$)""", s)
    merged: dict[str, Any] = {}
    for part in parts:
        merged.update(parse_condition(part.strip()))
    return merged