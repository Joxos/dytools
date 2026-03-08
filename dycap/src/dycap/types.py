"""Type definitions for dycap."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# Re-export MessageType from dyproto for convenience
from dyproto import MessageType


@dataclass(frozen=True)
class DanmuMessage:
    """Represents a parsed Douyu danmu message.

    This is the canonical message type used throughout dycap for storage
    and analysis. It contains all common fields from various message types.

    Attributes:
        timestamp: Time the message was received.
        room_id: The room ID this message belongs to.
        msg_type: Type of the message (chatmsg, gift, etc.).
        user_id: User's unique ID.
        username: User's display name.
        content: Message content (for chat messages).
        user_level: User's level in the streamer's room.
        gift_id: Gift ID (for gift messages).
        gift_count: Gift count (for gift messages).
        gift_name: Gift name (for gift messages).
        badge_level: Fan badge level.
        badge_name: Fan badge name.
        noble_level: Noble level (0 = not a noble).
        avatar_url: User's avatar URL.
        raw_data: Original raw message dictionary.
    """

    timestamp: datetime
    room_id: str
    msg_type: MessageType
    user_id: str | None = None
    username: str | None = None
    content: str | None = None
    user_level: int | None = None
    gift_id: str | None = None
    gift_count: int | None = None
    gift_name: str | None = None
    badge_level: int | None = None
    badge_name: str | None = None
    noble_level: int | None = None
    avatar_url: str | None = None
    raw_data: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "timestamp": self.timestamp,
            "room_id": self.room_id,
            "msg_type": self.msg_type.value,
            "user_id": self.user_id,
            "username": self.username,
            "content": self.content,
            "user_level": self.user_level,
            "gift_id": self.gift_id,
            "gift_count": self.gift_count,
            "gift_name": self.gift_name,
            "badge_level": self.badge_level,
            "badge_name": self.badge_name,
            "noble_level": self.noble_level,
            "avatar_url": self.avatar_url,
            "raw_data": self.raw_data,
        }
