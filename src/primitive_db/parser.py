from __future__ import annotations

import re
from typing import Any


def _strip_outer_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and ((s[0] == s[-1] == '"') or (s[0] == s[-1] == "'")):
        return s[1:-1]
    return s


def parse_values_list(raw: str) -> list[str]:
    """values ( "Sergei", 28, true ) -> ['"Sergei"', '28', 'true'] (сохраняем токены, каст будет позже)."""
    s = raw.strip()
    if not (s.startswith("(") and s.endswith(")")):
        raise ValueError(f"Некорректное значение: {raw}. Попробуйте снова.")
    inner = s[1:-1].strip()
    if not inner:
        return []
    parts = re.split(r""",(?=(?:[^'"]|'[^']*'|"[^"]*")*$)""", inner)
    return [p.strip() for p in parts]


def parse_condition(expr: str) -> dict[str, Any]:
    """age = 28 -> {'age': '28'}, name = "Sergei" -> {'name': 'Sergei'}."""
    if "=" not in expr:
        raise ValueError(f"Некорректное значение: {expr}. Попробуйте снова.")
    left, right = expr.split("=", 1)
    col = left.strip()
    val = right.strip()
    if not col:
        raise ValueError(f"Некорректное значение: {expr}. Попробуйте снова.")
    return {col: _strip_outer_quotes(val)}


def parse_set_clause(raw: str) -> dict[str, Any]:
    """age = 29, is_active = false -> {'age':'29','is_active':'false'}."""
    s = raw.strip()
    if not s:
        raise ValueError(f"Некорректное значение: {raw}. Попробуйте снова.")
    parts = re.split(r""",(?=(?:[^'"]|'[^']*'|"[^"]*")*$)""", s)
    merged: dict[str, Any] = {}
    for part in parts:
        merged.update(parse_condition(part.strip()))
    return merged