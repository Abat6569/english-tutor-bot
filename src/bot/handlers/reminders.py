import structlog
from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from src.infrastructure.db.repositories.reminder_repository import ReminderRepository
from src.infrastructure.db.session import get_session
from src.services.reminders import scheduler

router = Router(name="reminders")
log = structlog.get_logger()

VALID_TYPES = ("daily", "weekly", "monthly")

STATUS_FOOTER = (
    "\nUse /reminders TYPE on|off to toggle, or /remind_time TYPE HH:MM to set the time "
    "(TYPE is daily, weekly, or monthly)."
)


async def _status_text(user_id: int) -> str:
    async with get_session() as session:
        rows = await ReminderRepository(session).ensure_defaults(user_id)

    by_type = {r.reminder_type: r for r in rows}
    lines = ["<b>Reminders</b>"]
    for reminder_type in VALID_TYPES:
        row = by_type[reminder_type]
        status = "on" if row.enabled else "off"
        lines.append(f"{reminder_type}: {status}, {row.hour:02d}:{row.minute:02d}")
    return "\n".join(lines) + STATUS_FOOTER


@router.message(Command("reminders"))
async def cmd_reminders(message: Message, command: CommandObject) -> None:
    assert message.from_user is not None
    assert message.bot is not None
    user_id = message.from_user.id

    args = (command.args or "").split()
    if len(args) != 2 or args[0] not in VALID_TYPES or args[1] not in ("on", "off"):
        await message.answer(await _status_text(user_id))
        return

    reminder_type, action = args[0], args[1] == "on"
    async with get_session() as session:
        await ReminderRepository(session).ensure_defaults(user_id)
        await ReminderRepository(session).set_enabled(user_id, reminder_type, action)

    await scheduler.reschedule(message.bot, reminder_type)
    await message.answer(await _status_text(user_id))


@router.message(Command("remind_time"))
async def cmd_remind_time(message: Message, command: CommandObject) -> None:
    assert message.from_user is not None
    assert message.bot is not None
    user_id = message.from_user.id

    args = (command.args or "").split()
    if len(args) != 2 or args[0] not in VALID_TYPES:
        await message.answer("Usage: /remind_time TYPE HH:MM (TYPE is daily, weekly, or monthly)")
        return

    reminder_type, time_str = args
    try:
        hour_str, minute_str = time_str.split(":")
        hour, minute = int(hour_str), int(minute_str)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except ValueError:
        await message.answer("Time must be in HH:MM 24-hour format, e.g. 19:30")
        return

    async with get_session() as session:
        await ReminderRepository(session).ensure_defaults(user_id)
        await ReminderRepository(session).set_time(user_id, reminder_type, hour, minute)

    await scheduler.reschedule(message.bot, reminder_type)
    await message.answer(await _status_text(user_id))
