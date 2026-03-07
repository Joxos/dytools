from __future__ import annotations

import sys
from typing import NoReturn

import click

from dytools.constants import USER_FILTERABLE_TYPES_DESCRIBED
from dytools.log import logger

TYPES_HELP = ", ".join(f"{t}（{desc}）" for t, desc in USER_FILTERABLE_TYPES_DESCRIBED)


def fail(message: str) -> NoReturn:
    click.echo(f"Error: {message}", err=True)
    sys.exit(1)


def get_dsn(ctx: click.Context) -> str:
    dsn = ctx.obj.get("dsn") if ctx.obj else None
    if not isinstance(dsn, str) or not dsn:
        fail("Missing --dsn option or DYTOOLS_DSN environment variable")
    return dsn


def get_dsn_or(ctx: click.Context, supplied_dsn: str | None) -> str:
    if supplied_dsn:
        return supplied_dsn
    return get_dsn(ctx)


def resolve_room_for_query(room: str) -> str:
    from dytools.protocol import resolve_room_id

    try:
        real_id = resolve_room_id(int(room))
        return str(real_id)
    except Exception:
        logger.warning(f"Could not resolve room {room}, using as-is")
        return room


def ensure_mutually_exclusive(
    left_value: object,
    right_value: object,
    message: str,
) -> None:
    if left_value is not None and right_value is not None:
        fail(message)


def to_str(value: object, default: str) -> str:
    if isinstance(value, str):
        return value
    return default


def to_int(value: object, default: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default
