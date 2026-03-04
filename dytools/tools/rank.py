"""SQL-based frequency ranking for danmu messages.

This module provides SQL frequency ranking to analyze which users
send the most messages in a room.
"""

from __future__ import annotations

from datetime import timedelta

import psycopg

from dytools.log import logger


def rank(
    dsn: str,
    room_id: str,
    top: int = 10,
    msg_type: str = "chatmsg",
    days: int | None = None,
) -> list[dict[str, int | str]]:
    """Get top N users by message count from database.

    Args:
        dsn: PostgreSQL connection string
        room_id: Room ID to query
        top: Number of top results to return
        msg_type: Message type to filter (default: 'chatmsg')
        days: Optional number of days to look back (None = all time)

    Returns:
        List of dicts with keys: 'username', 'count'
    """
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            # Build query with optional time filter
            if days is not None:
                query = """
                    SELECT username, COUNT(*) as count
                    FROM danmaku
                    WHERE room_id = %s AND msg_type = %s
                      AND timestamp >= NOW() - INTERVAL '%s days'
                    GROUP BY username
                    ORDER BY count DESC
                    LIMIT %s
                """
                cur.execute(query, (room_id, msg_type, days, top))
            else:
                query = """
                    SELECT username, COUNT(*) as count
                    FROM danmaku
                    WHERE room_id = %s AND msg_type = %s
                    GROUP BY username
                    ORDER BY count DESC
                    LIMIT %s
                """
                cur.execute(query, (room_id, msg_type, top))

            results = cur.fetchall()

    # Convert to list of dicts
    return [{"username": row[0], "count": row[1]} for row in results]


def run_rank(args) -> None:
    """CLI entry point for rank command.

    Args:
        args: Argparse namespace with dsn, room, top, msg_type, days
    """
    dsn = args.dsn
    room_id = args.room
    top = args.top
    msg_type = getattr(args, "msg_type", "chatmsg")
    days = getattr(args, "days", None)

    results = rank(dsn, room_id, top, msg_type, days)

    if not results:
        logger.info(f"No messages found for room {room_id}")
        return

    # Terminal output
    print(f"\n=== User Ranking (Top {len(results)}) ===")
    print(f"Room: {room_id}, Type: {msg_type}\n")
    print(f"{'Rank':<6}{'Count':<8}{'Username'}")
    print(f"{'────':<6}{'─────':<8}{'────────────────────'}")

    for rank_num, item in enumerate(results, start=1):
        print(f"{rank_num:<6}{item['count']:<8}{item['username']}")
