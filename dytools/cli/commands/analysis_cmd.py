from __future__ import annotations

import sys

import click

from dytools.cli.common import get_dsn
from dytools.cli.formatters import (
    show_cluster_results,
    show_content_rank,
    show_search_results,
    show_user_rank,
)
from dytools.cli.options import (
    output_option,
    room_option,
    search_first_option,
    search_from_option,
    search_last_option,
    search_to_option,
    validate_last_first,
    validate_user_content,
)
from dytools.cli.services.dbio import export_clusters_to_csv, export_search_results_to_csv


def register(cli: click.Group) -> None:
    @cli.command(name="rank", short_help="Show ranking statistics")
    @room_option()
    @click.option("--top", default=10, help="Top N results (default: 10)")
    @click.option(
        "--type",
        "msg_type",
        default="chatmsg",
        help="Message type (chatmsg, dgb, uenter, loginres, loginreq, joingroup, mrkl, anbc, rnewbc, blab, upgrade, unknown; default: chatmsg)",
    )
    @click.option("--days", type=int, help="Days to look back (default: all time)")
    @click.option("-u", "--user", is_flag=True, help="Rank by username (default)")
    @click.option("-c", "--content", "content_mode", is_flag=True, help="Rank by message content")
    @click.pass_context
    def _rank_cmd(
        ctx: click.Context,
        room: str,
        top: int,
        msg_type: str,
        days: int | None,
        user: bool,
        content_mode: bool,
    ) -> None:
        from dytools import __main__ as main_module

        dsn = get_dsn(ctx)
        validate_user_content(user, content_mode)

        mode = "content" if content_mode else "user"
        try:
            resolved_room = main_module.resolve_room_for_query(room)
            results = main_module.rank.rank(dsn, resolved_room, top, msg_type, days, mode=mode)
            if not results:
                click.echo(f"No {msg_type} messages found for room {room}")
                return
            if mode == "user":
                show_user_rank(results, room, msg_type, days)
            else:
                show_content_rank(results, room, days)
        except main_module.psycopg.Error as e:
            click.echo(f"Error: Database query failed: {e}", err=True)
            sys.exit(1)

    @cli.command(name="prune", short_help="Remove duplicate records")
    @room_option()
    @click.pass_context
    def _prune_cmd(ctx: click.Context, room: str) -> None:
        from dytools import __main__ as main_module

        dsn = get_dsn(ctx)
        try:
            resolved_room = main_module.resolve_room_for_query(room)
            removed_count = main_module.prune.prune(dsn, resolved_room)
            click.echo(f"Removed {removed_count} duplicate records from room {room}")
        except main_module.psycopg.Error as e:
            click.echo(f"Error: Database operation failed: {e}", err=True)
            sys.exit(1)

    @cli.command(name="cluster", short_help="Cluster similar chat messages")
    @room_option()
    @click.option(
        "--threshold", default=0.6, type=float, help="Similarity threshold (default: 0.6)"
    )
    @click.option("--limit", default=1000, type=int, help="Max messages to analyze (default: 1000)")
    @output_option()
    @click.pass_context
    def _cluster_cmd(
        ctx: click.Context,
        room: str,
        threshold: float,
        limit: int,
        output: str | None,
    ) -> None:
        from dytools import __main__ as main_module

        dsn = get_dsn(ctx)
        try:
            resolved_room = main_module.resolve_room_for_query(room)
            all_clusters = main_module.cluster.cluster(
                dsn, resolved_room, threshold, "chatmsg", limit
            )
            if not all_clusters:
                click.echo(f"No messages found in room {room}")
                return

            total_unique = sum(len(c) for c in all_clusters)
            multi_clusters = [c for c in all_clusters if len(c) >= 2]
            multi_clusters.sort(key=lambda c: sum(cnt for _, cnt in c), reverse=True)

            if not multi_clusters:
                click.echo(f"No clusters found with threshold {threshold}")
                return

            show_cluster_results(multi_clusters, threshold, total_unique)
            if output:
                export_clusters_to_csv(multi_clusters, output)
                click.echo(f"Cluster data saved to {output}")
        except main_module.psycopg.Error as e:
            click.echo(f"Error: Database query failed: {e}", err=True)
            sys.exit(1)

    @cli.command(name="search", short_help="Search messages with filters")
    @room_option()
    @click.option("-q", "--query", help="Keyword to search (case-insensitive)")
    @click.option("-u", "--user", help="Filter by username")
    @click.option("--user-id", help="Filter by user_id")
    @click.option(
        "--type",
        "msg_type",
        help="Filter by message type (chatmsg, loginres, loginreq, joingroup, mrkl, dgb, uenter, anbc, rnewbc, blab, upgrade, unknown)",
    )
    @search_from_option()
    @search_to_option()
    @search_last_option()
    @search_first_option()
    @output_option(help_text="Export to CSV file (optional)")
    @click.pass_context
    def _search_cmd(
        ctx: click.Context,
        room: str,
        query: str | None,
        user: str | None,
        user_id: str | None,
        msg_type: str | None,
        from_date: str | None,
        to_date: str | None,
        last: int | None,
        first: int | None,
        output: str | None,
    ) -> None:
        from dytools import __main__ as main_module

        dsn = get_dsn(ctx)
        validate_last_first(last, first)

        try:
            resolved_room = main_module.resolve_room_for_query(room)
            results = main_module.search.search(
                dsn,
                resolved_room,
                query=query,
                username=user,
                user_id=user_id,
                msg_type=msg_type,
                from_date=from_date,
                to_date=to_date,
                last=last,
                first=first,
            )
            if not results:
                click.echo(f"No messages found for room {room}")
                return

            search_desc: list[str] = []
            if query:
                search_desc.append(f'query="{query}"')
            if user:
                search_desc.append(f'user="{user}"')
            if user_id:
                search_desc.append(f'user_id="{user_id}"')
            if msg_type:
                search_desc.append(f'type="{msg_type}"')
            search_str = ", ".join(search_desc) if search_desc else "all"

            if last:
                sort_mode = f"Last {last}"
            elif first:
                sort_mode = f"First {first}"
            else:
                sort_mode = "Last 100 (default)"

            show_search_results(results, room, search_str, sort_mode)

            if output:
                export_search_results_to_csv(results, output)
                click.echo(f"\nResults exported to {output}")
        except main_module.psycopg.Error as e:
            click.echo(f"Error: Database query failed: {e}", err=True)
            sys.exit(1)

    _registered = (_rank_cmd, _prune_cmd, _cluster_cmd, _search_cmd)
