"""CSV storage handler."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import IO

from ..types import DanmuMessage
from .base import StorageHandler


class CSVStorage(StorageHandler):
    """CSV file storage handler.

    Writes danmu messages to a CSV file. Uses a background thread
    for non-blocking writes.

    Example:
        async with CSVStorage("output.csv") as storage:
            await storage.save(message)
    """

    def __init__(self, filename: str | Path) -> None:
        """Initialize CSV storage.

        Args:
            filename: Output CSV file path.
        """
        self._filename = Path(filename)
        self._closed = False
        self._file: IO[str] | None = None
        self._csv_writer: csv._writer | None = None

    async def __aenter__(self) -> CSVStorage:
        """Open CSV file and write header."""
        self._file = self._filename.open("w", newline="", encoding="utf-8")
        self._csv_writer = csv.writer(self._file)
        self._csv_writer.writerow(
            [
                "timestamp",
                "room_id",
                "msg_type",
                "user_id",
                "username",
                "content",
                "user_level",
                "gift_id",
                "gift_count",
                "gift_name",
                "badge_level",
                "badge_name",
                "noble_level",
                "avatar_url",
            ]
        )
        self._file.flush()
        return self

    async def save(self, message: DanmuMessage) -> None:
        """Write one message to CSV file."""
        if self._closed or self._file is None or self._csv_writer is None:
            return

        self._csv_writer.writerow(
            [
                message.timestamp.isoformat(),
                message.room_id,
                message.msg_type.value,
                message.user_id or "",
                message.username or "",
                message.content or "",
                message.user_level or "",
                message.gift_id or "",
                message.gift_count or "",
                message.gift_name or "",
                message.badge_level or "",
                message.badge_name or "",
                message.noble_level or "",
                message.avatar_url or "",
            ]
        )
        self._file.flush()

    async def close(self) -> None:
        """Close storage and output file."""
        if self._closed:
            return
        self._closed = True
        if self._file is not None:
            self._file.close()
            self._file = None
