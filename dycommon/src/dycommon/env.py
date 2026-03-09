from __future__ import annotations

import os


def get_dsn(*aliases: str) -> str | None:
    candidates = ["DYKIT_DSN", *aliases]
    for key in candidates:
        value = os.environ.get(key)
        if value:
            return value
    return None
