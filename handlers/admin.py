from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command

from config import ADMIN_GROUP_ID, CHANNEL_ID
from database.db import (
    approve_specialist, delete_specialist, get_specialist_by_id,
    complete_problem, is_specialist_approved
)

router = Router()


def _channel_text(spec):
    return (
        f"👤 {spec['fullname']}\n"
        f"🏷 {spec.get('category', '')}\n"
        f"💼 {spec['profession']}\n"
        f"⭐ Tavsiyalar: {spec['recommendation_count']}\n"
        f"📝 {spec['description']}"
    )


@router.callback_query(F.data.startswith("approve_spec_"))
async def admin_approve_specialist(callback: CallbackQuery, bot):
    if callback.message.chat.id != ADMIN_GROUP_ID:
        return

    spec_id = int(callback.data.split("_")[2])

    # FIX 5: Ikki marta bosilsa tekshiruv
    already = await is_specialist_approved(spec_id)
    if already:
        await callback.answer("⚠️ Allaqachon tasdiqlangan!", show_alert=True)
        return

    await approve_specialist(spec_id)
    spec = await get_specialist_by_id(spec_id)

    if spec:
        from keyboards.keyboards import contact_keyboard
        try:
            await bot.send_message(
                CHANNEL_ID,
                _channel_text(spec),
                reply_markup=contact_keyboard(spec_id)
            )
        except Exception as e:
            await callback.message.answer(f"❌ Kanalga yuborishda xato: {e}")
            return

    await callback.message.edit_text(
        callback.message.text + "\n\n✅ Tasdiqlandi va kanalga joylashtirildi"
    )
    await callback.answer("✅ Tasdiqlandi!")


@router.callback_query(F.data.startswith("add_media_"))
async def admin_add_media(callback: CallbackQuery, bot):
    if callback.message.chat.id != ADMIN_GROUP_ID:
        return

    spec_id = int(callback.data.split("_")[2])

    # FIX 5: Allaqachon tasdiqlangan bo'lsa
    already = await is_specialist_approved(spec_id)
    if already:
        await callback.answer("⚠️ Allaqachon tasdiqlangan!", show_alert=True)
        return

    spec = await get_specialist_by_id(spec_id)
    if not spec:
        await callback.answer("Topilmadi!", show_alert=True)
        return

    await callback.message.reply(
        f"📎 <b>{spec['fullname']}</b> uchun rasm/video yuborish:\n\n"
        f"1. Guruhga rasm/video yuboring\n"
        f"2. Shu rasmga <b>reply</b> qilib yozing:\n"
        f"<code>/media {spec_id}</code>",
        parse_mode="HTML"
    )
    await callback.answer()


# FIX 6: Command import qo'shildi
@router.message(Command("media"))
async def admin_media_command(message: Message, bot):
    if message.chat.id != ADMIN_GROUP_ID and message.chat.type != "private":
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Format: rasmga reply qilib /media [spec_id] yozing")
        return

    try:
        spec_id = int(args[1])
    except ValueError:
        await message.answer("❌ spec_id raqam bo'lishi kerak. Masalan: /media 5")
        return

    spec = await get_specialist_by_id(spec_id)
    if not spec:
        await message.answer("❌ Mutaxassis topilmadi!")
        return

    # FIX 5: Ikki marta tasdiq
    already = await is_specialist_approved(spec_id)
    if already:
        await message.answer("⚠️ Bu mutaxassis allaqachon tasdiqlangan!")
        return

    media_message = message.reply_to_message
    from keyboards.keyboards import contact_keyboard
    kb = contact_keyboard(spec_id)
    text = _channel_text(spec)

    try:
        await approve_specialist(spec_id)

        if media_message and media_message.photo:
            await bot.send_photo(CHANNEL_ID, photo=media_message.photo[-1].file_id, caption=text, reply_markup=kb)
        elif media_message and media_message.video:
            await bot.send_video(CHANNEL_ID, video=media_message.video.file_id, caption=text, reply_markup=kb)
        elif message.photo:
            await bot.send_photo(CHANNEL_ID, photo=message.photo[-1].file_id, caption=text, reply_markup=kb)
        elif message.video:
            await bot.send_video(CHANNEL_ID, video=message.video.file_id, caption=text, reply_markup=kb)
        else:
            await message.answer(
                "❌ Rasm topilmadi!\n\n"
                "Rasmni yuboring va shu rasmga reply qilib /media [id] yozing."
            )
            return

        await message.answer("✅ Tasdiqlandi va media bilan kanalga yuborildi!")

    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")


@router.callback_query(F.data.startswith("reject_spec_"))
async def admin_reject_specialist(callback: CallbackQuery):
    if callback.message.chat.id != ADMIN_GROUP_ID:
        return

    spec_id = int(callback.data.split("_")[2])

    already = await is_specialist_approved(spec_id)
    if already:
        await callback.answer("⚠️ Allaqachon tasdiqlangan, o'chirib bo'lmaydi!", show_alert=True)
        return

    await delete_specialist(spec_id)
    await callback.message.edit_text(
        callback.message.text + "\n\n❌ Rad etildi va o'chirildi"
    )
    await callback.answer("❌ Rad etildi!")


@router.callback_query(F.data.startswith("done_problem_"))
async def admin_done_problem(callback: CallbackQuery):
    if callback.message.chat.id != ADMIN_GROUP_ID:
        return

    problem_id = int(callback.data.split("_")[2])
    await complete_problem(problem_id)
    await callback.message.edit_text(
        callback.message.text + "\n\n✅ Yakunlandi"
    )
    await callback.answer("✅ Yakunlandi!")
