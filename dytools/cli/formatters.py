from __future__ import annotations

from typing import Any

import click


def show_user_rank(
    results: list[dict[str, Any]], room: str, msg_type: str, days: int | None
) -> None:
    click.echo(f"\n=== User Ranking (Top {len(results)}) ===")
    click.echo(f"Room: {room}, Type: {msg_type}")
    if days:
        click.echo(f"Time range: last {days} days")
    click.echo(f"\n{'Rank':<6}{'Count':<8}{'Username'}")
    click.echo(f"{'────':<6}{'─────':<8}{'────────────────────'}")
    for rank_num, item in enumerate(results, start=1):
        click.echo(f"{rank_num:<6}{item['count']:<8}{item['username']}")


def show_content_rank(results: list[dict[str, Any]], room: str, days: int | None) -> None:
    click.echo(f"\n=== Repeated Messages (Top {len(results)}) ===")
    click.echo(f"Room: {room}")
    if days:
        click.echo(f"Time range: last {days} days")
    click.echo(f"\n{'Count':<8}{'Content':<50}{'First Seen':<20}{'Last Seen'}")
    click.echo(f"{'─────':<8}{'───────':<50}{'──────────':<20}{'─────────'}")
    for item in results:
        content: Any = item["content"]
        content_str = str(content) if content is not None else ""
        content_preview = content_str[:47] + "..." if len(content_str) > 50 else content_str
        first_seen: Any = item["first_seen"]
        last_seen: Any = item["last_seen"]
        first = (
            first_seen.strftime("%Y-%m-%d %H:%M:%S")
            if hasattr(first_seen, "strftime")
            else str(first_seen)
        )
        last = (
            last_seen.strftime("%Y-%m-%d %H:%M:%S")
            if hasattr(last_seen, "strftime")
            else str(last_seen)
        )
        click.echo(f"{item['count']:<8}{content_preview:<50}{first:<20}{last}")


def show_search_results(
    results: list[dict[str, Any]], room: str, search_str: str, sort_mode: str
) -> None:
    click.echo(f"\n=== Search Results ({len(results)} found) ===")
    click.echo(f"Room: {room}, Filter: {search_str}, Sort: {sort_mode}")
    click.echo()
    click.echo(f"{'Timestamp':<20}{'Username':<16}{'Content'}")
    click.echo(f"{'─' * 20:<20}{'─' * 16:<16}{'─' * 50}")
    for item in results:
        ts = (
            item["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            if hasattr(item["timestamp"], "strftime")
            else str(item["timestamp"])[:19]
        )
        username_str = item["username"] or "[unknown]"
        content_str = item["content"] or ""
        content_preview = content_str[:47] + "..." if len(content_str) > 50 else content_str
        click.echo(f"{ts:<20}{username_str:<16}{content_preview}")


def show_cluster_results(
    multi_clusters: list[list[tuple[str, int]]], threshold: float, total_unique: int
) -> None:
    click.echo(f"\n=== Clusters (threshold={threshold:.2f}, {total_unique} unique msgs) ===")
    click.echo(f"Found {len(multi_clusters)} clusters with 2+ variants\n")
    for idx, clust in enumerate(multi_clusters, start=1):
        total = sum(cnt for _, cnt in clust)
        variants = len(clust)
        click.echo(f"─── Cluster {idx} ({variants} variants, {total} total) ───")
        max_cnt_width = len(str(clust[0][1]))
        for content, cnt in clust:
            display = content if len(content) <= 60 else content[:57] + "..."
            click.echo(f"  [{cnt:>{max_cnt_width}}x] {display}")
        click.echo()
