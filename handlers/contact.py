from aiogram import Router, F
from aiogram.types import CallbackQuery

from config import ADMIN_GROUP_ID
from database.db import (
    get_or_create_user, save_contact_request,
    get_contact_request, approve_contact_request,
    get_specialist_by_id, check_existing_request
)
from keyboards.keyboards import admin_contact_keyboard
from handlers.rating import rating_keyboard

router = Router()


@router.callback_query(F.data.startswith("contact_"))
async def request_contact(callback: CallbackQuery, bot):
    spec_id = int(callback.data.split("_")[1])

    spec = await get_specialist_by_id(spec_id)
    if not spec:
        await callback.answer("❌ Mutaxassis topilmadi!", show_alert=True)
        return

    user = await get_or_create_user(callback.from_user.id, callback.from_user.full_name)

    already = await check_existing_request(user['id'], spec_id)
    if already:
        await callback.answer(
            "⚠️ Siz bu mutaxassisga allaqachon so'rov yuborgansiz!\nAdmin tasdiqlashini kuting.",
            show_alert=True
        )
        return

    request_id = await save_contact_request(user['id'], spec_id)

    username = callback.from_user.username
    username_text = f"@{username}" if username else "username yo'q"

    admin_text = (
        f"📩 ALOQA SO'ROVI\n\n"
        f"👤 Kim: {callback.from_user.full_name} ({username_text})\n"
        f"🔍 Kim bilan: {spec['fullname']} ({spec['profession']})\n\n"
        f"Kontaktni yuborishga ruxsat berasizmi?"
    )
    try:
        await bot.send_message(
            ADMIN_GROUP_ID,
            admin_text,
            reply_markup=admin_contact_keyboard(request_id)
        )
    except Exception as e:
        import logging
        logging.error(f"Admin guruhga yuborishda xato: {e}")

    try:
        await bot.send_message(
            callback.from_user.id,
            "✅ So'rovingiz yuborildi! Admin tasdiqlashidan so'ng kontakt beriladi."
        )
    except Exception:
        await callback.answer(
            "✅ So'rov yuborildi! Natija uchun botga /start yuboring.",
            show_alert=True
        )
        return

    await callback.answer("✅ So'rov yuborildi!")


@router.callback_query(F.data.startswith("approve_contact_"))
async def approve_contact(callback: CallbackQuery, bot):
    request_id = int(callback.data.split("_")[2])
    req = await get_contact_request(request_id)

    if not req:
        await callback.answer("Topilmadi yoki allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    await approve_contact_request(request_id)

    try:
        # Kontaktni yuborish
        await bot.send_message(
            req['user_telegram_id'],
            f"✅ So'rovingiz tasdiqlandi!\n\n"
            f"👤 Mutaxassis: {req['spec_fullname']}\n"
            f"💼 Kasbi: {req['profession']}\n"
            f"📱 Telefon: {req['spec_phone']}"
        )
        # Reyting so'rovi — 1 kun o'tib emas, darhol (test uchun)
        # Ishlab chiqishda scheduler bilan 1 kun keyinga qo'yish mumkin
        await bot.send_message(
            req['user_telegram_id'],
            f"⭐ Mutaxassis bilan bog'langandan so'ng baho bering:\n\n"
            f"👤 {req['spec_fullname']} qanday yordam berdi?",
            reply_markup=rating_keyboard(req['specialist_id'])
        )
    except Exception:
        pass

    await callback.message.edit_text(
        callback.message.text + "\n\n✅ Tasdiqlandi"
    )
    await callback.answer("Tasdiqlandi!")


@router.callback_query(F.data.startswith("reject_contact_"))
async def reject_contact(callback: CallbackQuery, bot):
    request_id = int(callback.data.split("_")[2])
    req = await get_contact_request(request_id)

    if not req:
        await callback.answer("Topilmadi!", show_alert=True)
        try:
            await callback.message.edit_text(
                callback.message.text + "\n\n❌ Rad etildi (allaqachon)"
            )
        except Exception:
            pass
        return

    try:
        await bot.send_message(
            req['user_telegram_id'],
            "❌ So'rovingiz rad etildi."
        )
    except Exception:
        pass

    await callback.message.edit_text(
        callback.message.text + "\n\n❌ Rad etildi"
    )
    await callback.answer("Rad etildi!")
