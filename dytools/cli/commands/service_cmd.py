from __future__ import annotations

import shutil

import click

from dytools.cli.common import ensure_mutually_exclusive, fail
from dytools.cli.options import service_with_types_option, without_types_option
from dytools.service import ServiceManager


def register(cli: click.Group) -> None:
    @cli.group(name="service", short_help="Manage systemd user services")
    @click.pass_context
    def service(ctx: click.Context) -> None:
        if not shutil.which("systemctl"):
            click.echo(
                "systemd user services not available. Ensure systemd is installed and running.",
                err=True,
            )
            raise SystemExit(1)

    @service.command(name="create")
    @click.argument("spec")
    @click.option("--dsn", envvar="DYTOOLS_DSN", help="PostgreSQL DSN (or set DYTOOLS_DSN)")
    @service_with_types_option()
    @without_types_option()
    @click.option("-v", "--verbose", is_flag=True, help="Enable debug logging for the collector")
    @click.pass_context
    def _create_service(
        ctx: click.Context,
        spec: str,
        dsn: str | None,
        msg_types_include: str | None,
        msg_types_exclude: str | None,
        verbose: bool,
    ) -> None:
        ensure_mutually_exclusive(
            msg_types_include,
            msg_types_exclude,
            "Cannot use both --with and --without together",
        )

        resolved_dsn = dsn or (ctx.obj.get("dsn") if ctx.obj else None)
        sm = ServiceManager()
        try:
            sm.create(
                spec,
                resolved_dsn,
                with_types=msg_types_include,
                without_types=msg_types_exclude,
                verbose=verbose,
            )
        except ValueError as e:
            fail(str(e))
        except RuntimeError as e:
            fail(str(e))

    @service.command(name="list")
    def _list_services() -> None:
        sm = ServiceManager()
        services = sm.list()

        if not services:
            click.echo("No dytools services found.")
            return

        click.echo(f"{'NAME':<30} {'STATUS':<12} {'ROOM_ID':<10}")
        click.echo("-" * 54)
        for svc in services:
            click.echo(f"{svc['name']:<30} {svc['status']:<12} {svc['room_id']:<10}")

    @service.command(name="start")
    @click.argument("service_name")
    def _start_service(service_name: str) -> None:
        sm = ServiceManager()
        try:
            sm.start(service_name)
        except RuntimeError as e:
            fail(str(e))

    @service.command(name="stop")
    @click.argument("service_name")
    def _stop_service(service_name: str) -> None:
        sm = ServiceManager()
        try:
            sm.stop(service_name)
        except RuntimeError as e:
            fail(str(e))

    @service.command(name="restart")
    @click.argument("service_name")
    def _restart_service(service_name: str) -> None:
        sm = ServiceManager()
        try:
            sm.restart(service_name)
        except RuntimeError as e:
            fail(str(e))

    @service.command(name="status")
    @click.argument("service_name")
    def _status_service(service_name: str) -> None:
        sm = ServiceManager()
        try:
            output = sm.status(service_name)
            click.echo(output, nl=False)
        except RuntimeError as e:
            fail(str(e))

    @service.command(name="logs")
    @click.argument("service_name")
    @click.option(
        "-n", "--lines", type=int, default=50, help="Number of log lines to show (default: 50)"
    )
    def _logs_service(service_name: str, lines: int) -> None:
        sm = ServiceManager()
        try:
            output = sm.logs(service_name, lines)
            click.echo(output, nl=False)
        except RuntimeError as e:
            fail(str(e))

    @service.command(name="where")
    @click.argument("service_name")
    def _where_service(service_name: str) -> None:
        sm = ServiceManager()
        try:
            path = sm.where(service_name)
            click.echo(path)
        except FileNotFoundError as e:
            fail(str(e))

    @service.command(name="edit")
    @click.argument("service_name")
    def _edit_service(service_name: str) -> None:
        sm = ServiceManager()
        try:
            sm.edit(service_name)
        except FileNotFoundError as e:
            fail(str(e))
        except RuntimeError as e:
            fail(str(e))

    @service.command(name="remove")
    @click.argument("service_name")
    def _remove_service(service_name: str) -> None:
        sm = ServiceManager()
        try:
            sm.remove(service_name)
        except FileNotFoundError as e:
            fail(str(e))
        except RuntimeError as e:
            fail(str(e))

    _registered = (
        _create_service,
        _list_services,
        _start_service,
        _stop_service,
        _restart_service,
        _status_service,
        _logs_service,
        _where_service,
        _edit_service,
        _remove_service,
    )
