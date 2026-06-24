from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.db import get_or_create_user, save_rating, get_specialist_by_id, get_specialist_rating

router = Router()


def rating_keyboard(specialist_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⭐1", callback_data=f"rate_{specialist_id}_1"),
        InlineKeyboardButton(text="⭐2", callback_data=f"rate_{specialist_id}_2"),
        InlineKeyboardButton(text="⭐3", callback_data=f"rate_{specialist_id}_3"),
        InlineKeyboardButton(text="⭐4", callback_data=f"rate_{specialist_id}_4"),
        InlineKeyboardButton(text="⭐5", callback_data=f"rate_{specialist_id}_5"),
    ], [
        InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data=f"rate_{specialist_id}_0"),
    ]])


def stars_text(stars: int) -> str:
    return "⭐" * stars + "☆" * (5 - stars)


@router.callback_query(F.data.startswith("rate_"))
async def handle_rating(callback: CallbackQuery):
    parts = callback.data.split("_")
    specialist_id = int(parts[1])
    stars = int(parts[2])

    if stars == 0:
        await callback.message.edit_text("⏭ Baho o'tkazib yuborildi.")
        await callback.answer()
        return

    user = await get_or_create_user(callback.from_user.id, callback.from_user.full_name)
    spec = await get_specialist_by_id(specialist_id)

    if not spec:
        await callback.answer("Mutaxassis topilmadi!", show_alert=True)
        return

    saved = await save_rating(user['id'], specialist_id, stars)

    if not saved:
        await callback.answer("⚠️ Siz bu mutaxassisga allaqachon baho bergansiz!", show_alert=True)
        return

    avg = await get_specialist_rating(specialist_id)

    await callback.message.edit_text(
        f"✅ Bahoyingiz qabul qilindi!\n\n"
        f"👤 {spec['fullname']}\n"
        f"Sizning baho: {stars_text(stars)} ({stars}/5)\n"
        f"O'rtacha reyting: {avg} ⭐"
    )
    await callback.answer("✅ Rahmat!")
