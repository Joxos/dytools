"""Clustering tool for finding similar danmu messages."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import psycopg
from psycopg import sql
from rapidfuzz import fuzz
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
class ClusterResult:
    """Cluster result item."""

    representative: str
    count: int
    similar: list[tuple[str, int]]


def cluster(
    dsn: str,
    room: str,
    threshold: float = 0.5,
    msg_type: str | None = "chatmsg",
    limit: int = 50,
    username: str | None = None,
    user_id: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    window: str | None = None,
    last: int | None = None,
    first: int | None = None,
    days: int | None = None,
) -> list[ClusterResult]:
    """Cluster similar messages using text similarity.

    Args:
        dsn: PostgreSQL connection string.
        room: Room ID to analyze.
        limit: Number of source messages to consider.
        threshold: Similarity threshold (0-1).
        msg_type: Message type to filter.

    Returns:
        List of clusters with representative and similar messages.
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

    where_clauses: list[sql.SQL] = [
        sql.SQL("room_id = %s"),
        sql.SQL("content IS NOT NULL"),
        sql.SQL("content != ''"),
    ]
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

    order_limit_sql = sql.SQL("")
    if last is not None:
        order_limit_sql = sql.SQL("ORDER BY timestamp DESC LIMIT %s")
        params.append(last)
    elif first is not None:
        order_limit_sql = sql.SQL("ORDER BY timestamp ASC LIMIT %s")
        params.append(first)

    where_sql = sql.SQL(" AND ").join(where_clauses)
    query_sql = sql.SQL(
        """
        WITH filtered AS (
            SELECT *
            FROM danmaku
            WHERE {where_sql}
            {order_limit_sql}
        )
        SELECT content, COUNT(*) as cnt
        FROM filtered
        GROUP BY content
        ORDER BY cnt DESC
        LIMIT %s
        """
    ).format(where_sql=where_sql, order_limit_sql=order_limit_sql)

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(query_sql, (*params, limit))
            messages = [(row[0], row[1]) for row in cur.fetchall()]

    if not messages:
        return []

    # Greedy clustering
    clusters: list[ClusterResult] = []
    assigned = set()

    for i, (content, count) in enumerate(messages):
        if i in assigned:
            continue

        similar = [(content, count)]
        assigned.add(i)

        for j, (other_content, other_count) in enumerate(messages):
            if j in assigned:
                continue

            ratio = fuzz.ratio(content, other_content) / 100.0
            if ratio >= threshold:
                similar.append((other_content, other_count))
                assigned.add(j)

        clusters.append(
            ClusterResult(
                representative=content,
                count=sum(c for _, c in similar),
                similar=similar,
            )
        )

    return clusters


def run_cluster(
    room: str,
    threshold: float = 0.5,
    msg_type: str | None = "chatmsg",
    limit: int = 50,
    username: str | None = None,
    user_id: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    window: str | None = None,
    last: int | None = None,
    first: int | None = None,
    days: int | None = None,
    dsn: str | None = None,
) -> list[ClusterResult]:
    """Run cluster command."""
    dsn = dsn or get_dsn()
    if not dsn:
        raise ValueError("DSN required. Set DYKIT_DSN or pass --dsn")

    resolved_room = str(resolve_room_id(room))

    return cluster(
        dsn,
        resolved_room,
        threshold,
        msg_type,
        limit,
        username,
        user_id,
        from_date,
        to_date,
        window,
        last,
        first,
        days,
    )
