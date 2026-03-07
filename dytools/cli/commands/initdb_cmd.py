from __future__ import annotations

import sys

import click

from dytools.cli.common import get_dsn
from dytools.cli.services.dbio import init_database_schema


def register(cli: click.Group) -> None:
    @cli.command(name="init-db")
    @click.pass_context
    def _init_db(ctx: click.Context) -> None:
        from dytools import __main__ as main_module

        dsn = get_dsn(ctx)
        try:
            init_database_schema(main_module.psycopg.connect, dsn)
            click.echo("Database schema initialized successfully")
            click.echo("Table: danmaku")
            click.echo("Indexes: idx_danmaku_room_time, idx_danmaku_user_id, idx_danmaku_msg_type")
        except main_module.psycopg.Error as e:
            click.echo(f"Error: Database initialization failed: {e}", err=True)
            sys.exit(1)

    _registered = _init_db
