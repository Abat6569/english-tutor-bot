from unittest.mock import AsyncMock

import pytest

from src.bot.middlewares.access_control import AccessControlMiddleware
from src.config.settings import settings


class _FakeUser:
    def __init__(self, user_id: int) -> None:
        self.id = user_id


@pytest.mark.asyncio
async def test_owner_is_allowed_through() -> None:
    middleware = AccessControlMiddleware()
    handler = AsyncMock(return_value="ok")
    data = {"event_from_user": _FakeUser(settings.admin_telegram_id)}

    result = await middleware(handler, event=object(), data=data)

    handler.assert_awaited_once()
    assert result == "ok"


@pytest.mark.asyncio
async def test_stranger_is_blocked() -> None:
    middleware = AccessControlMiddleware()
    handler = AsyncMock(return_value="ok")
    data = {"event_from_user": _FakeUser(settings.admin_telegram_id + 1)}

    result = await middleware(handler, event=object(), data=data)

    handler.assert_not_awaited()
    assert result is None
