from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PartialDate:
    raw: str
    year: int | None
    month: int | None = None
    day: int | None = None


def parse_partial_date(value: str | None) -> PartialDate | None:
    if not value:
        return None
    parts = value.split("-")
    try:
        if len(parts) == 1:
            return PartialDate(raw=value, year=int(parts[0]))
        if len(parts) == 2:
            return PartialDate(raw=value, year=int(parts[0]), month=int(parts[1]))
        if len(parts) == 3:
            return PartialDate(
                raw=value,
                year=int(parts[0]),
                month=int(parts[1]),
                day=int(parts[2]),
            )
    except ValueError:
        return PartialDate(raw=value, year=None)
    return PartialDate(raw=value, year=None)


def duration_months(start: PartialDate | None, end: PartialDate | None) -> int | None:
    if start is None or end is None or start.year is None or end.year is None:
        return None
    start_month = start.month or 1
    end_month = end.month or 1
    months = (end.year - start.year) * 12 + (end_month - start_month)
    if start.day is not None and end.day is not None and end.day < start.day:
        months -= 1
    if months < 0:
        return None
    return months
