from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from config import CHANNEL_ID, ADMIN_IDS


async def is_subscribed(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ("creator", "administrator", "member")
    except Exception:
        return False


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id

        if user_id in ADMIN_IDS:
            return await handler(event, data)

        bot = data["bot"]
        if await is_subscribed(bot, user_id):
            return await handler(event, data)

        from keyboards.keyboards import subscription_keyboard
        await event.answer(
            "❗ Botdan foydalanish uchun avval kanalimizga obuna bo'ling!\n\n"
            "👇 Quyidagi tugmani bosib kanalga obuna bo'ling, "
            "so'ng \"✅ Tekshirish\" tugmasini bosing.",
            reply_markup=subscription_keyboard()
        )
        return  # handler ni chaqirmaymiz


class SubscriptionCallbackMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id

        if user_id in ADMIN_IDS:
            return await handler(event, data)

        # "check_sub" callback ni doim o'tkazamiz
        if event.data == "check_sub":
            return await handler(event, data)

        bot = data["bot"]
        if await is_subscribed(bot, user_id):
            return await handler(event, data)

        from keyboards.keyboards import subscription_keyboard
        await event.answer(
            "❗ Avval kanalga obuna bo'ling!",
            show_alert=True
        )
        return
