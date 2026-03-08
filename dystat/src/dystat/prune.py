"""Prune tool for removing duplicate danmu records."""

from __future__ import annotations

import os

from dyproto.discovery import resolve_room_id


def get_dsn() -> str | None:
    """Get DSN from environment."""
    return os.environ.get("DYKIT_DSN") or os.environ.get("DYSTAT_DSN")


def prune(dsn: str, room: str) -> int:
    """Remove duplicate records from danmaku table.

    Keeps the newest record for each unique (room_id, user_id, content, timestamp).

    Args:
        dsn: PostgreSQL connection string.
        room: Room ID to prune.

    Returns:
        Number of duplicate records removed.
    """
    import psycopg

    query = """
        WITH duplicates AS (
            SELECT id
            FROM danmaku
            WHERE room_id = %s
            AND (
                -- Same user repeating same content within 1 second
                (user_id, content) IN (
                    SELECT user_id, content
                    FROM danmaku
                    WHERE room_id = %s
                    AND content IS NOT NULL
                    GROUP BY user_id, content
                    HAVING COUNT(*) > 1
                )
            )
            AND id NOT IN (
                SELECT MIN(id)
                FROM danmaku
                WHERE room_id = %s
                GROUP BY user_id, content, DATE(timestamp)
            )
        )
        DELETE FROM danmaku
        WHERE id IN (SELECT id FROM duplicates)
    """

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (room, room, room))
            deleted = cur.rowcount
            conn.commit()

    return deleted


def run_prune(room: str, dsn: str | None = None) -> int:
    """Run prune command."""
    dsn = dsn or get_dsn()
    if not dsn:
        raise ValueError("DSN required. Set DYKIT_DSN or pass --dsn")

    resolved_room = str(resolve_room_id(room))
    return prune(dsn, resolved_room)
