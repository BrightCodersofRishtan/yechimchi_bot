import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy
from aiogram.types import BotCommand

from config import BOT_TOKEN
from handlers import user, specialist, admin, contact
from handlers import rating, admin_panel
from database.db import init_db
from middlewares.subscription import SubscriptionMiddleware, SubscriptionCallbackMiddleware

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(
    storage=MemoryStorage(),
    fsm_strategy=FSMStrategy.USER_IN_CHAT
)

async def main():
    await init_db()

    await bot.set_my_commands([
        BotCommand(command="start", description="🏠 Bosh menyu"),
        BotCommand(command="problem", description="🔍 Muammom bor"),
        BotCommand(command="recommend", description="⭐ Mutaxassis tavsiya qilaman"),
        BotCommand(command="specialists", description="📚 Mutaxassislar ro'yxati"),
        BotCommand(command="help", description="❓ Yordam"),
    ])

    dp.include_router(rating.router)   # Reyting birinchi (callback conflict bo'lmasin)
    dp.include_router(admin_panel.router)  # Admin panel
    dp.include_router(user.router)
    dp.include_router(specialist.router)
    dp.include_router(admin.router)
    dp.include_router(contact.router)

    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionCallbackMiddleware())

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
