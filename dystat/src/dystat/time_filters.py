from __future__ import annotations

from datetime import datetime, timedelta

_DATE_FORMAT = "%Y-%m-%d"
_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def parse_from_inclusive(from_value: str) -> datetime:
    parsed, _has_time = _parse_time_filter(from_value, "--from")
    return parsed


def parse_to_exclusive(to_value: str) -> datetime:
    parsed, has_time = _parse_time_filter(to_value, "--to")
    if has_time:
        return parsed + timedelta(seconds=1)
    return parsed + timedelta(days=1)


def validate_time_window(from_inclusive: datetime, to_exclusive: datetime) -> None:
    if from_inclusive >= to_exclusive:
        raise ValueError("Invalid time window: --from must be earlier than --to")


def _parse_time_filter(value: str, option_name: str) -> tuple[datetime, bool]:
    try:
        return datetime.strptime(value, _DATETIME_FORMAT), True
    except ValueError:
        pass

    try:
        return datetime.strptime(value, _DATE_FORMAT), False
    except ValueError as e:
        raise ValueError(
            f"Invalid {option_name} format: {value!r}. Use 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'."
        ) from e
