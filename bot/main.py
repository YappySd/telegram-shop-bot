from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .config import load_settings
from .db import Database
from .handlers import router
from .seed import seed_demo


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    settings = load_settings()

    db = Database(settings.db_path)
    await db.connect()
    await seed_demo(db)

    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # Keyword arguments become dependencies injected into handlers by name.
    dp = Dispatcher(db=db, settings=settings)
    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
