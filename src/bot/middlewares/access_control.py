from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.config.settings import settings


class AccessControlMiddleware(BaseMiddleware):
    """Personal tutor bot: only the owner's Telegram account may use it.

    Every Claude/Groq call costs money, so an open bot is an open bill.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is None or user.id != settings.admin_telegram_id:
            return None
        return await handler(event, data)
