import asyncio

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.bot.handlers import interview, lesson, modes, start, voice
from src.bot.middlewares.access_control import AccessControlMiddleware
from src.config.settings import settings

log = structlog.get_logger()


async def main() -> None:
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.message.middleware(AccessControlMiddleware())
    dp.include_router(start.router)
    dp.include_router(lesson.router)
    dp.include_router(modes.router)
    dp.include_router(interview.router)
    dp.include_router(voice.router)

    log.info("bot_starting")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
