from __future__ import annotations

from typing import Any

import click

from dytools.cli.common import TYPES_HELP


def room_option(help_text: str = "Room ID") -> Any:
    return click.option("-r", "--room", required=True, help=help_text)


def with_types_option() -> Any:
    return click.option(
        "--with",
        "msg_types_include",
        default=None,
        help=(
            "Include only these message types (comma-separated). "
            f"Available: {TYPES_HELP}. "
            "Example: --with chatmsg,dgb,uenter"
        ),
    )


def without_types_option() -> Any:
    return click.option(
        "--without",
        "msg_types_exclude",
        default=None,
        help=(
            "Exclude these message types (comma-separated). "
            f"Available: {TYPES_HELP}. "
            "Example: --without uenter"
        ),
    )


def search_from_option() -> Any:
    return click.option("--from", "from_date", help="Start date (YYYY-MM-DD)")


def search_to_option() -> Any:
    return click.option("--to", "to_date", help="End date (YYYY-MM-DD)")


def search_last_option() -> Any:
    return click.option("--last", type=int, help="Show last (most recent) N messages")


def search_first_option() -> Any:
    return click.option("--first", type=int, help="Show first (earliest) N messages")


def service_with_types_option() -> Any:
    return click.option(
        "--with",
        "msg_types_include",
        default=None,
        help=(
            "Include only these message types (comma-separated). "
            f"Available: {TYPES_HELP}. "
            "Example: --with chatmsg,dgb"
        ),
    )
