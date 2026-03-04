"""SQL-based frequency ranking for danmu messages.



This module provides SQL frequency ranking to analyze which users

send the most messages in a room, or which message content appears

most frequently.

"""



from __future__ import annotations



from typing import Literal



import psycopg



from dytools.log import logger

def rank(

    dsn: str,

    room_id: str,

    top: int = 10,

    msg_type: str = "chatmsg",

    days: int | None = None,

    mode: Literal["user", "content"] = "user",

) -> list[dict[str, int | str]]:

    """Get top N ranked items by frequency from database.



    Supports two modes:

    - mode='user': Rank users by message count (default)

    - mode='content': Rank repeated message content by occurrence



    Args:

        dsn: PostgreSQL connection string

        room_id: Room ID to query

        top: Number of top results to return

        msg_type: Message type to filter (default: 'chatmsg')

        days: Optional number of days to look back (None = all time)

        mode: 'user' (default) or 'content'



    Returns:

        List of dicts with keys: 'username', 'count' (user mode)

        or 'content', 'count', 'first_seen', 'last_seen' (content mode)

    """
    with psycopg.connect(dsn) as conn:

        with conn.cursor() as cur:

            if mode == "content":

                # Content mode: rank by repeated message content

                if days is not None:

                    query = """

                        SELECT content, COUNT(*) AS count, MIN(timestamp) AS first_seen, MAX(timestamp) AS last_seen

                        FROM danmaku

                        WHERE room_id = %s AND msg_type = %s AND content IS NOT NULL AND content != ''

                          AND timestamp >= NOW() - INTERVAL '%s days'

                        GROUP BY content

                        HAVING COUNT(*) > 1

                        ORDER BY count DESC

                        LIMIT %s

                    """

                    cur.execute(query, (room_id, msg_type, days, top))

                else:

                    query = """

                        SELECT content, COUNT(*) AS count, MIN(timestamp) AS first_seen, MAX(timestamp) AS last_seen

                        FROM danmaku

                        WHERE room_id = %s AND msg_type = %s AND content IS NOT NULL AND content != ''

                        GROUP BY content

                        HAVING COUNT(*) > 1

                        ORDER BY count DESC

                        LIMIT %s

                    """

                    cur.execute(query, (room_id, msg_type, top))



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



            else:

                # User mode (default): rank by username message count

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
