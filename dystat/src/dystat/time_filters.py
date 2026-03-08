from __future__ import annotations

from datetime import datetime, timedelta

_UNITS = ["seconds", "minutes", "hours", "days", "weeks", "months", "years"]

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


def parse_relative_window(
    range_value: str, now: datetime | None = None
) -> tuple[datetime | None, datetime | None]:
    current = now or datetime.now()
    if "-" not in range_value:
        raise ValueError("Invalid --window format. Use 'start-end', e.g. '10 30-' or '-5 0'.")

    left_text, right_text = range_value.split("-", maxsplit=1)
    left_delta = _parse_relative_side(left_text.strip(), "start")
    right_delta = _parse_relative_side(right_text.strip(), "end")

    from_inclusive = current - left_delta if left_delta is not None else None
    to_exclusive = current - right_delta if right_delta is not None else None

    if from_inclusive is not None and to_exclusive is not None:
        validate_time_window(from_inclusive, to_exclusive)

    return from_inclusive, to_exclusive


def _parse_relative_side(text: str, side: str) -> timedelta | None:
    if not text:
        return None

    parts = text.split()
    if len(parts) > len(_UNITS):
        raise ValueError(
            f"Invalid --window {side} segment: too many fields. "
            "Supported order: seconds minutes hours days weeks months years."
        )

    total_seconds = 0
    for idx, part in enumerate(reversed(parts)):
        if not part.isdigit():
            raise ValueError(
                f"Invalid --window {side} segment value: {part!r}. Only non-negative integers are allowed."
            )
        value = int(part)
        unit = _UNITS[idx]
        if unit == "seconds":
            total_seconds += value
        elif unit == "minutes":
            total_seconds += value * 60
        elif unit == "hours":
            total_seconds += value * 3600
        elif unit == "days":
            total_seconds += value * 86400
        elif unit == "weeks":
            total_seconds += value * 7 * 86400
        elif unit == "months":
            total_seconds += value * 30 * 86400
        else:
            total_seconds += value * 365 * 86400

    return timedelta(seconds=total_seconds)


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
