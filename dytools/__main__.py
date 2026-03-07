from __future__ import annotations

import sys

import click
import psycopg

from dytools.cli import cli
from dytools.cli.common import resolve_room_for_query as _resolve_room_for_query
from dytools.collectors import AsyncCollector
from dytools.storage import PostgreSQLStorage
from dytools.tools import cluster, prune, rank, search

_LEGACY_PATCH_TARGETS = (
    _resolve_room_for_query,
    AsyncCollector,
    PostgreSQLStorage,
    rank,
    prune,
    cluster,
    search,
    psycopg,
)


def resolve_room_for_query(room: str) -> str:
    return _resolve_room_for_query(room)


def main() -> None:
    try:
        cli()
    except click.exceptions.MissingParameter as e:
        if "dsn" in str(e).lower():
            click.echo(
                "Error: Database DSN required. Use --dsn or set DYTOOLS_DSN environment variable.",
                err=True,
            )
            sys.exit(1)
        raise


if __name__ == "__main__":
    main()
