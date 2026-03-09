from __future__ import annotations

from dyproto import MessageType

from .types import DanmuMessage


def render_message_text(message: DanmuMessage) -> str:
    username = message.username or "Unknown"
    match message.msg_type:
        case MessageType.CHATMSG:
            return f"{username}: {message.content or ''}"

        case MessageType.DGB:
            gift_count = message.gift_count if message.gift_count is not None else 1
            gift_name = message.gift_name or (message.gift_id or "未知礼物")
            return f"{username} 送出了 {gift_count}x {gift_name}"

        case MessageType.UENTER:
            return f"{username} 进入了直播间"

        case MessageType.ANBC:
            noble = message.noble_level or 0
            return f"{username} 开通了{noble}级贵族"

        case MessageType.RNEWBC:
            noble = message.noble_level or 0
            return f"{username} 续费了{noble}级贵族"

        case MessageType.BLAB:
            if message.badge_name and message.badge_level is not None:
                return f"{username} 粉丝牌《{message.badge_name}》升级至{message.badge_level}级"
            return f"{username} 粉丝牌升级"

        case MessageType.UPGRADE:
            if message.user_level is not None:
                return f"{username} 升级到{message.user_level}级"
            return f"{username} 升级"
