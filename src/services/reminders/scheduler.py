from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import structlog
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config.settings import settings
from src.infrastructure.db.repositories.achievement_repository import AchievementRepository
from src.infrastructure.db.repositories.mistake_repository import MistakeRepository
from src.infrastructure.db.repositories.reminder_repository import ReminderRepository
from src.infrastructure.db.repositories.user_repository import UserRepository
from src.infrastructure.db.repositories.vocabulary_repository import VocabularyRepository
from src.infrastructure.db.session import get_session
from src.services.reminders import content

log = structlog.get_logger()

_scheduler = AsyncIOScheduler()


async def _send_daily(bot: Bot) -> None:
    user_id = settings.admin_telegram_id
    async with get_session() as session:
        user = await UserRepository(session).get_or_create(user_id, None)
        reminder = await ReminderRepository(session).get(user_id, "daily")
        if reminder is None or not reminder.enabled:
            return
        if user.last_activity_date == date.today():
            return  # already practiced today, no need to nag

        await bot.send_message(user_id, content.build_daily_message(user))
        await ReminderRepository(session).mark_sent(user_id, "daily", datetime.now(UTC))


async def _send_weekly(bot: Bot) -> None:
    user_id = settings.admin_telegram_id
    since = datetime.now(UTC) - timedelta(days=7)
    async with get_session() as session:
        user = await UserRepository(session).get_or_create(user_id, None)
        reminder = await ReminderRepository(session).get(user_id, "weekly")
        if reminder is None or not reminder.enabled:
            return

        new_vocab = await VocabularyRepository(session).count_since(user_id, since)
        mistakes = await MistakeRepository(session).count_since(user_id, since)

        await bot.send_message(user_id, content.build_weekly_message(user, new_vocab, mistakes))
        await ReminderRepository(session).mark_sent(user_id, "weekly", datetime.now(UTC))


async def _send_monthly(bot: Bot) -> None:
    user_id = settings.admin_telegram_id
    async with get_session() as session:
        user = await UserRepository(session).get_or_create(user_id, None)
        reminder = await ReminderRepository(session).get(user_id, "monthly")
        if reminder is None or not reminder.enabled:
            return

        achievement_count = await AchievementRepository(session).count(user_id)

        await bot.send_message(user_id, content.build_monthly_message(user, achievement_count))
        await ReminderRepository(session).mark_sent(user_id, "monthly", datetime.now(UTC))


_JOBS: dict[str, Callable[[Bot], Awaitable[None]]] = {
    "daily": _send_daily,
    "weekly": _send_weekly,
    "monthly": _send_monthly,
}


def _cron_kwargs(reminder_type: str, hour: int, minute: int) -> dict[str, int | str]:
    if reminder_type == "daily":
        return {"hour": hour, "minute": minute}
    if reminder_type == "weekly":
        return {"day_of_week": "mon", "hour": hour, "minute": minute}
    if reminder_type == "monthly":
        return {"day": 1, "hour": hour, "minute": minute}
    raise ValueError(f"unknown reminder_type: {reminder_type}")


async def _schedule_job(bot: Bot, user_id: int, reminder_type: str) -> None:
    job_id = f"reminder_{reminder_type}"

    async with get_session() as session:
        reminder = await ReminderRepository(session).get(user_id, reminder_type)
        user = await UserRepository(session).get_or_create(user_id, None)

    if reminder is None or not reminder.enabled:
        if _scheduler.get_job(job_id):
            _scheduler.remove_job(job_id)
        return

    trigger = CronTrigger(
        timezone=ZoneInfo(user.timezone),
        **_cron_kwargs(reminder_type, reminder.hour, reminder.minute),
    )
    _scheduler.add_job(_JOBS[reminder_type], trigger, args=[bot], id=job_id, replace_existing=True)


async def start(bot: Bot) -> None:
    user_id = settings.admin_telegram_id
    async with get_session() as session:
        await UserRepository(session).get_or_create(user_id, None)
        await ReminderRepository(session).ensure_defaults(user_id)

    for reminder_type in _JOBS:
        await _schedule_job(bot, user_id, reminder_type)

    _scheduler.start()
    log.info("reminder_scheduler_started", jobs=[j.id for j in _scheduler.get_jobs()])


async def reschedule(bot: Bot, reminder_type: str) -> None:
    await _schedule_job(bot, settings.admin_telegram_id, reminder_type)
