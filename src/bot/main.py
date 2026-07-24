import asyncio

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.bot.handlers import interview, lesson, modes, progress, reminders, start, translator, voice
from src.bot.middlewares.access_control import AccessControlMiddleware
from src.config.settings import settings
from src.services.reminders import scheduler as reminder_scheduler

log = structlog.get_logger()


async def main() -> None:
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.message.middleware(AccessControlMiddleware())
    # translator.router has a catch-all F.text handler that swallows any message
    # (including unrecognized commands) it sees first, so every command router
    # must be registered before it.
    dp.include_router(start.router)
    dp.include_router(lesson.router)
    dp.include_router(modes.router)
    dp.include_router(interview.router)
    dp.include_router(progress.router)
    dp.include_router(reminders.router)
    dp.include_router(voice.router)
    dp.include_router(translator.router)

    log.info("bot_starting")
    await bot.delete_webhook(drop_pending_updates=True)
    await reminder_scheduler.start(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
