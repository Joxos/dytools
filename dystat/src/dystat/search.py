"""Search tool for finding danmu messages."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import psycopg
from psycopg import sql
from dyproto.discovery import resolve_room_id

from .time_filters import (
    parse_from_inclusive,
    parse_relative_window,
    parse_to_exclusive,
    validate_time_window,
)


def get_dsn() -> str | None:
    """Get DSN from environment."""
    return os.environ.get("DYKIT_DSN") or os.environ.get("DYSTAT_DSN")


@dataclass
class SearchResult:
    """Search result item."""

    timestamp: datetime
    username: str | None
    content: str | None
    msg_type: str


def search(
    dsn: str,
    room: str,
    query: str | None = None,
    username: str | None = None,
    user_id: str | None = None,
    msg_type: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    window: str | None = None,
    last: int | None = None,
    first: int | None = None,
) -> list[SearchResult]:
    """Search danmu messages with filters.

    Args:
        dsn: PostgreSQL connection string.
        room: Room ID to search.
        query: Filter by content (ILIKE).
        username: Filter by username.
        user_id: Filter by user ID.
        msg_type: Filter by message type.
        from_date: Filter from timestamp.
        to_date: Filter to timestamp.
        window: Relative time window.
        last: Return the last (most recent) N messages.
        first: Return the first (earliest) N messages.

    Returns:
        List of matching messages.
    """
    if last is not None and first is not None:
        raise ValueError("Cannot use --last and --first together. Use one window direction only.")
    if window is not None and (from_date is not None or to_date is not None):
        raise ValueError("Cannot combine --window with --from/--to")
    if window is not None and (last is not None or first is not None):
        raise ValueError("Cannot combine --window with --last/--first")

    if last is None and first is None:
        last = 100

    where_clauses: list[sql.SQL] = [sql.SQL("room_id = %s")]
    params: list[str | int | datetime] = [room]

    if query is not None:
        where_clauses.append(sql.SQL("content ILIKE %s"))
        params.append(f"%{query}%")

    if username is not None:
        where_clauses.append(sql.SQL("username = %s"))
        params.append(username)

    if user_id is not None:
        where_clauses.append(sql.SQL("user_id = %s"))
        params.append(user_id)

    if msg_type is not None:
        where_clauses.append(sql.SQL("msg_type = %s"))
        params.append(msg_type)

    if window is not None:
        parsed_from, parsed_to = parse_relative_window(window)
    else:
        parsed_from = parse_from_inclusive(from_date) if from_date is not None else None
        parsed_to = parse_to_exclusive(to_date) if to_date is not None else None

    if parsed_from is not None and parsed_to is not None:
        validate_time_window(parsed_from, parsed_to)

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

    where_sql = sql.SQL(" AND ").join(where_clauses)
    if last is not None:
        query_sql = sql.SQL(
            """
            SELECT timestamp, username, content, msg_type
            FROM danmaku
            WHERE {where_sql}
            ORDER BY timestamp DESC
            LIMIT %s
            """
        ).format(where_sql=where_sql)
        params.append(last)
    else:
        query_sql = sql.SQL(
            """
            SELECT timestamp, username, content, msg_type
            FROM danmaku
            WHERE {where_sql}
            ORDER BY timestamp ASC
            LIMIT %s
            """
        ).format(where_sql=where_sql)
        if first is None:
            raise ValueError("Invalid --first value")
        params.append(first)

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(query_sql, params)
            rows = cur.fetchall()

    return [
        SearchResult(
            timestamp=row[0],
            username=row[1],
            content=row[2],
            msg_type=row[3],
        )
        for row in rows
    ]


def run_search(
    room: str,
    query: str | None = None,
    username: str | None = None,
    user_id: str | None = None,
    msg_type: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    window: str | None = None,
    last: int | None = None,
    first: int | None = None,
    dsn: str | None = None,
) -> list[SearchResult]:
    """Run search command."""
    dsn = dsn or get_dsn()
    if not dsn:
        raise ValueError("DSN required. Set DYKIT_DSN or pass --dsn")

    resolved_room = str(resolve_room_id(room))

    return search(
        dsn,
        resolved_room,
        query,
        username,
        user_id,
        msg_type,
        from_date,
        to_date,
        window,
        last,
        first,
    )
