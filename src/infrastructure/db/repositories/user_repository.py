from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(self, telegram_id: int, username: str | None) -> User:
        user = await self._session.get(User, telegram_id)
        if user is None:
            user = User(telegram_id=telegram_id, username=username)
            self._session.add(user)
            await self._session.commit()
        return user

    async def update_settings(self, telegram_id: int, **updates: object) -> User:
        user = await self._session.get(User, telegram_id)
        assert user is not None
        user.settings_json = {**user.settings_json, **updates}
        await self._session.commit()
        return user
