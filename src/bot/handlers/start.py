from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="start")

WELCOME_TEXT = (
    "Hi! I'm your personal English tutor.\n\n"
    "Send me a voice message any time and we'll talk. Use /help to see what I can do."
)

HELP_TEXT = (
    "/lesson — today's adaptive lesson\n"
    "/speaking — free conversation practice\n"
    "/interview — interview coaching\n"
    "/translator — translation mode\n"
    "/vocabulary — your saved words\n"
    "/grammar — your grammar stats\n"
    "/progress — XP, streak, dashboard\n"
    "/settings — preferences\n"
    "/export — export your data\n"
    "/import — import your data\n"
    "/reset — reset progress"
)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(WELCOME_TEXT)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)
