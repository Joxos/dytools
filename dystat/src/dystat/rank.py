"""Ranking tool for danmu data."""

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
class RankResult:
    """Rank result item."""

    rank: int
    value: str  # username or content
    count: int


def rank(
    dsn: str,
    room: str,
    top: int = 10,
    mode: str = "user",
    msg_type: str | None = "chatmsg",
    days: int | None = None,
    username: str | None = None,
    user_id: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    window: str | None = None,
    last: int | None = None,
    first: int | None = None,
) -> list[RankResult]:
    """Rank users or content by frequency.

    Args:
        dsn: PostgreSQL connection string.
        room: Room ID to query.
        top: Number of top results.
        mode: "user" or "content".
        msg_type: Message type to filter.
        days: Optional limit to recent N days.

    Returns:
        List of RankResult sorted by count descending.
    """
    if last is not None and first is not None:
        raise ValueError("Cannot use --last and --first together. Use one window direction only.")
    if days is not None and (from_date is not None or to_date is not None):
        raise ValueError(
            "Cannot combine --days with --from/--to. Use either relative days or explicit date range."
        )
    if window is not None and (from_date is not None or to_date is not None):
        raise ValueError("Cannot combine --window with --from/--to")
    if window is not None and days is not None:
        raise ValueError("Cannot combine --window with --days")

    if window is not None:
        parsed_from, parsed_to = parse_relative_window(window)
    else:
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

    where_sql = sql.SQL(" AND ").join(where_clauses)
    order_limit_sql = sql.SQL("")
    if last is not None:
        order_limit_sql = sql.SQL("ORDER BY timestamp DESC LIMIT %s")
        params.append(last)
    elif first is not None:
        order_limit_sql = sql.SQL("ORDER BY timestamp ASC LIMIT %s")
        params.append(first)

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            group_field = "username" if mode == "user" else "content"
            query_sql = sql.SQL(
                """
                WITH filtered AS (
                    SELECT *
                    FROM danmaku
                    WHERE {where_sql}
                    {order_limit_sql}
                )
                SELECT {group_field}, COUNT(*) as cnt
                FROM filtered
                {content_guard}
                GROUP BY {group_field}
                ORDER BY cnt DESC
                LIMIT %s
                """
            ).format(
                where_sql=where_sql,
                order_limit_sql=order_limit_sql,
                group_field=sql.SQL(group_field),
                content_guard=sql.SQL("WHERE content IS NOT NULL AND content != ''")
                if mode == "content"
                else sql.SQL(""),
            )
            cur.execute(query_sql, (*params, top))
            results = cur.fetchall()

    return [RankResult(rank=i + 1, value=row[0], count=row[1]) for i, row in enumerate(results)]


def run_rank(
    room: str,
    top: int = 10,
    mode: str = "user",
    msg_type: str | None = "chatmsg",
    days: int | None = None,
    username: str | None = None,
    user_id: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    window: str | None = None,
    last: int | None = None,
    first: int | None = None,
    dsn: str | None = None,
) -> list[RankResult]:
    """Run rank command with CLI defaults."""
    dsn = dsn or get_dsn()
    if not dsn:
        raise ValueError("DSN required. Set DYKIT_DSN or pass --dsn")

    resolved_room = str(resolve_room_id(room))

    return rank(
        dsn,
        resolved_room,
        top,
        mode,
        msg_type,
        days,
        username,
        user_id,
        from_date,
        to_date,
        window,
        last,
        first,
    )
