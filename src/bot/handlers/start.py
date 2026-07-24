from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.infrastructure.db.repositories.user_repository import UserRepository
from src.infrastructure.db.session import get_session

router = Router(name="start")

WELCOME_TEXT = (
    "Hi! I'm your personal English tutor.\n\n"
    "Send me a voice message any time and we'll talk. Use /help to see what I can do."
)

HELP_TEXT = (
    "/lesson — today's adaptive lesson\n"
    "/speaking — free conversation practice (default mode)\n"
    "/professional — QA/QC role-play (EPC contractor, inspector, client)\n"
    "/interview — interview coaching\n"
    "/translator — translation mode\n"
    "/vocabulary — your saved words\n"
    "/grammar — your grammar stats\n"
    "/progress — XP, streak, dashboard\n"
    "/reminders — configure daily/weekly/monthly practice reminders\n"
    "/settings — preferences\n"
    "/export — export your data\n"
    "/import — import your data\n"
    "/reset — reset progress"
)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    assert message.from_user is not None
    async with get_session() as session:
        await UserRepository(session).get_or_create(
            message.from_user.id, message.from_user.username
        )
    await message.answer(WELCOME_TEXT)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)
