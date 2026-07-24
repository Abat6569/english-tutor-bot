from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.models.reminder import Reminder

DEFAULTS: dict[str, tuple[int, int]] = {
    "daily": (19, 0),
    "weekly": (9, 0),
    "monthly": (9, 0),
}


class ReminderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def ensure_defaults(self, user_id: int) -> list[Reminder]:
        stmt = select(Reminder).where(Reminder.user_id == user_id)
        existing = {r.reminder_type: r for r in (await self._session.execute(stmt)).scalars()}

        for reminder_type, (hour, minute) in DEFAULTS.items():
            if reminder_type not in existing:
                row = Reminder(
                    user_id=user_id, reminder_type=reminder_type, hour=hour, minute=minute
                )
                self._session.add(row)
                existing[reminder_type] = row

        await self._session.commit()
        return list(existing.values())

    async def get(self, user_id: int, reminder_type: str) -> Reminder | None:
        stmt = select(Reminder).where(
            Reminder.user_id == user_id, Reminder.reminder_type == reminder_type
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def set_enabled(self, user_id: int, reminder_type: str, enabled: bool) -> Reminder:
        row = await self.get(user_id, reminder_type)
        assert row is not None
        row.enabled = enabled
        await self._session.commit()
        return row

    async def set_time(self, user_id: int, reminder_type: str, hour: int, minute: int) -> Reminder:
        row = await self.get(user_id, reminder_type)
        assert row is not None
        row.hour = hour
        row.minute = minute
        await self._session.commit()
        return row

    async def mark_sent(self, user_id: int, reminder_type: str, when: datetime) -> None:
        row = await self.get(user_id, reminder_type)
        assert row is not None
        row.last_sent_at = when
        await self._session.commit()
