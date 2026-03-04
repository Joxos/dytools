"""Find and aggregate duplicate danmaku messages by content.

This module provides SQL aggregation functionality to:
1. Query chatmsg records from PostgreSQL database
2. Identify duplicate message content
3. Count occurrences and track first/last seen timestamps
4. Return structured results sorted by frequency

Returns list of dicts with keys: content, count, first_seen, last_seen
"""

import psycopg
from typing import Any

from dytools.log import logger



def compact(dsn: str, room_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """Get most frequently repeated chatmsg content from database.
    
    Args:
        dsn: PostgreSQL connection string
        room_id: Room ID to query
        limit: Number of top results to return (default: 10)
    
    Returns:
        List of dicts with keys: content, count, first_seen, last_seen
    """
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            query = """
                SELECT content, COUNT(*) AS count, MIN(timestamp) AS first_seen, MAX(timestamp) AS last_seen
                FROM danmaku
                WHERE room_id = %s AND msg_type = 'chatmsg' AND content IS NOT NULL AND content != ''
                GROUP BY content
                HAVING COUNT(*) > 1
                ORDER BY count DESC
                LIMIT %s
            """
            cur.execute(query, (room_id, limit))
            results = cur.fetchall()
    
    return [
        {
            "content": row[0],
            "count": row[1],
            "first_seen": row[2],
            "last_seen": row[3]
        }
        for row in results
    ]


def run_compact(args) -> None:
    """CLI entry point for compact command.
    
    Args:
        args: Namespace from argparse with:
            - dsn: PostgreSQL connection string
            - room: Room ID to query
            - limit: Number of results (default: 10)
    """
    dsn = args.dsn
    room_id = args.room
    limit = getattr(args, 'limit', 10)
    
    results = compact(dsn, room_id, limit)
    
    if not results:
        logger.info(f"No repeated messages found for room {room_id}")
        return
    
    # Terminal output
    print(f"\n=== Repeated Messages (Top {len(results)}) ===")
    print(f"Room: {room_id}\n")
    print(f"{'Count':<8}{'Content':<50}{'First Seen':<20}{'Last Seen'}")
    print(f"{'─────':<8}{'───────':<50}{'──────────':<20}{'─────────'}")
    
    for item in results:
        content_preview = item['content'][:47] + "..." if len(item['content']) > 50 else item['content']
        first = item['first_seen'].strftime('%Y-%m-%d %H:%M:%S')
        last = item['last_seen'].strftime('%Y-%m-%d %H:%M:%S')
        print(f"{item['count']:<8}{content_preview:<50}{first:<20}{last}")
