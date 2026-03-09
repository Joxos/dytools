from __future__ import annotations

from datetime import datetime

from dycommon.time_rules import WINDOW_CONFLICT_FIRST_LAST
from psycopg import sql

from .time_filters import parse_from_inclusive, parse_to_exclusive, validate_time_window


def parse_order_limit(last: int | None, first: int | None) -> tuple[sql.SQL, int | None]:
    if last is not None and first is not None:
        raise ValueError(WINDOW_CONFLICT_FIRST_LAST)

    if last is not None:
        return sql.SQL("ORDER BY timestamp DESC LIMIT %s"), last

    if first is not None:
        return sql.SQL("ORDER BY timestamp ASC LIMIT %s"), first

    return sql.SQL(""), None


def build_common_filters(
    *,
    room: str,
    msg_type: str | None,
    username: str | None,
    user_id: str | None,
    from_date: str | None,
    to_date: str | None,
    days: int | None = None,
) -> tuple[list[sql.SQL], list[str | int | datetime]]:
    parsed_from = parse_from_inclusive(from_date) if from_date is not None else None
    parsed_to = parse_to_exclusive(to_date) if to_date is not None else None

    if parsed_from is not None and parsed_to is not None:
        validate_time_window(parsed_from, parsed_to)

    where_clauses: list[sql.SQL] = [sql.SQL("room_id = %s")]
    params: list[str | int | datetime] = [room]

    if msg_type is not None:
        where_clauses.append(sql.SQL("msg_type = %s"))
        params.append(msg_type)
    if username is not None:
        where_clauses.append(sql.SQL("username = %s"))
        params.append(username)
    if user_id is not None:
        where_clauses.append(sql.SQL("user_id = %s"))
        params.append(user_id)
    if from_date is not None:
        where_clauses.append(sql.SQL("timestamp >= %s"))
        if parsed_from is None:
            raise ValueError("Invalid --from value")
        params.append(parsed_from)
    if to_date is not None:
        where_clauses.append(sql.SQL("timestamp < %s"))
        if parsed_to is None:
            raise ValueError("Invalid --to value")
        params.append(parsed_to)
    if days is not None:
        where_clauses.append(sql.SQL("timestamp >= NOW() - INTERVAL '%s days'"))
        params.append(days)

    return where_clauses, params
