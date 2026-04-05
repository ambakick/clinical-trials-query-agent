from __future__ import annotations


def build_excerpt(field_path: str, value: str | int | float | bool | None) -> str:
    return f"{field_path} = {value}"

