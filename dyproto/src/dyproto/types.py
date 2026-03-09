"""Type definitions for Douyu protocol messages."""

from __future__ import annotations

from enum import Enum


class MessageType(str, Enum):
    """Douyu message type enumeration.

    These are the recognized message types in the Douyu protocol.
    """

    # User messages
    CHATMSG = "chatmsg"  # Regular chat message
    DGB = "dgb"  # Gift
    UENTER = "uenter"  # User entered
    ANBC = "anbc"  # Noble opened
    RNEWBC = "rnewbc"  # Noble renewed
    BLAB = "blab"  # Badge level up
    UPGRADE = "upgrade"  # User level up


# Mapping from string to MessageType
MSG_TYPE_TO_ENUM: dict[str, MessageType] = {
    "chatmsg": MessageType.CHATMSG,
    "dgb": MessageType.DGB,
    "uenter": MessageType.UENTER,
    "anbc": MessageType.ANBC,
    "rnewbc": MessageType.RNEWBC,
    "blab": MessageType.BLAB,
    "upgrade": MessageType.UPGRADE,
}
