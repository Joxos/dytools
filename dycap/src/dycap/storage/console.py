"""Console storage handler (stdout logging)."""

from __future__ import annotations

from ..types import DanmuMessage
from .base import StorageHandler


class ConsoleStorage(StorageHandler):
    """Console/stdout storage handler.

    Prints danmu messages to stdout. Useful for debugging.

    Example:
        async with ConsoleStorage() as storage:
            await storage.save(message)
    """

    def __init__(self) -> None:
        """Initialize console storage."""
        pass

    async def save(self, message: DanmuMessage) -> None:
        """Print message to stdout."""
        username = message.username or "Unknown"
        content = message.content or ""

        if message.msg_type.value == "chatmsg":
            print(f"[{message.room_id}] {username}: {content}")
        elif message.msg_type.value == "dgb":
            print(
                f"[{message.room_id}] {username} 送出了 {message.gift_count}x {message.gift_name}"
            )
        elif message.msg_type.value == "uenter":
            print(f"[{message.room_id}] {username} 进入了直播间")
        else:
            print(f"[{message.room_id}] {message.msg_type.value}: {content}")

    async def close(self) -> None:
        """No-op for console storage."""
        pass
