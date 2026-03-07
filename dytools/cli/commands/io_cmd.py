from __future__ import annotations

import sys

import click

from dytools.cli.common import get_dsn
from dytools.cli.services.dbio import export_room_to_csv, import_csv_to_db


def register(cli: click.Group) -> None:
    @cli.command("import")
    @click.argument("file", type=click.Path(exists=True))
    @click.option("-r", "--room", required=True, help="Target room ID for imported data")
    @click.pass_context
    def _import_csv(ctx: click.Context, file: str, room: str) -> None:
        from dytools import __main__ as main_module

        dsn = get_dsn(ctx)
        try:
            count = import_csv_to_db(main_module.psycopg.connect, dsn, file, room)
            click.echo(f"Imported {count} records from {file} to room {room}")
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
        except main_module.psycopg.Error as e:
            click.echo(f"Error: Database import failed: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

    @cli.command(name="export")
    @click.option("-r", "--room", required=True, help="Room ID")
    @click.option("-o", "--output", required=True, help="Output CSV file")
    @click.pass_context
    def _export(ctx: click.Context, room: str, output: str) -> None:
        from dytools import __main__ as main_module

        dsn = get_dsn(ctx)
        try:
            resolved_room = main_module.resolve_room_for_query(room)
            count = export_room_to_csv(main_module.psycopg.connect, dsn, resolved_room, output)
            if not count:
                click.echo(f"No data found for room {room}")
                return
            click.echo(f"Exported {count} records from room {room} to {output}")
        except main_module.psycopg.Error as e:
            click.echo(f"Error: Database export failed: {e}", err=True)
            sys.exit(1)

    _registered = (_import_csv, _export)
