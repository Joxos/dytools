from __future__ import annotations

import click

from dytools.cli.commands import analysis_cmd, collect_cmd, initdb_cmd, io_cmd, service_cmd


@click.group()
@click.option(
    "--dsn",
    envvar="DYTOOLS_DSN",
    required=False,
    help="PostgreSQL DSN (or set DYTOOLS_DSN env var)",
)
@click.pass_context
def cli(ctx: click.Context, dsn: str | None) -> None:
    ctx.ensure_object(dict)
    ctx.obj["dsn"] = dsn


collect_cmd.register(cli)
analysis_cmd.register(cli)
io_cmd.register(cli)
initdb_cmd.register(cli)
service_cmd.register(cli)
