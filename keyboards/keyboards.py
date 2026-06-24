from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from config import CATEGORIES, SPECIALIST_CATEGORIES


def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Muammom bor")],
            [KeyboardButton(text="⭐ Mutaxassis tavsiya qilaman")],
            [KeyboardButton(text="📚 Tavsiya etilgan mutaxassislar")],
        ],
        resize_keyboard=True
    )


def categories_keyboard(categories=None):
    """categories - baza dan kelgan dict lar ro'yxati [{'name': '...'}] yoki None (eski statik ro'yxat)"""
    if categories is None:
        from config import CATEGORIES
        names = CATEGORIES
    else:
        names = [c['name'] for c in categories]
    buttons = [[KeyboardButton(text=name)] for name in names]
    buttons.append([KeyboardButton(text="🔙 Orqaga")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def specialist_categories_keyboard(categories=None):
    """categories - baza dan kelgan dict lar ro'yxati [{'name': '...'}] yoki None (eski statik ro'yxat)"""
    if categories is None:
        from config import SPECIALIST_CATEGORIES
        names = SPECIALIST_CATEGORIES
    else:
        names = [c['name'] for c in categories]
    buttons = [[KeyboardButton(text=name)] for name in names]
    buttons.append([KeyboardButton(text="🔙 Orqaga")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
        resize_keyboard=True
    )


def phone_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)],
            [KeyboardButton(text="🔙 Orqaga")],
        ],
        resize_keyboard=True
    )


def specialists_list_keyboard(specialists: list, page: int = 0, category_idx: int = 0, page_size: int = 5):
    start = page * page_size
    end = start + page_size
    page_items = specialists[start:end]
    total_pages = (len(specialists) - 1) // page_size + 1 if specialists else 1

    buttons = []
    for s in page_items:
        buttons.append([InlineKeyboardButton(
            text=f"👤 {s['fullname']} | ⭐{s['recommendation_count']}",
            callback_data=f"spec_{s['id']}"
        )])

    # Sahifalash tugmalari (category index ishlatamiz, callback 64 bayt limiti uchun)
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(
            text="⬅️ Oldingi", callback_data=f"page_{category_idx}_{page-1}"
        ))
    if total_pages > 1:
        nav_row.append(InlineKeyboardButton(
            text=f"{page+1}/{total_pages}", callback_data="noop"
        ))
    if end < len(specialists):
        nav_row.append(InlineKeyboardButton(
            text="Keyingi ➡️", callback_data=f"page_{category_idx}_{page+1}"
        ))
    if nav_row:
        buttons.append(nav_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def contact_keyboard(specialist_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔘 Aloqa olish", callback_data=f"contact_{specialist_id}")
    ]])


def admin_specialist_keyboard(specialist_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_spec_{specialist_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_spec_{specialist_id}"),
    ]])


def admin_specialist_with_media_keyboard(specialist_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_spec_{specialist_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_spec_{specialist_id}"),
        ],
        [
            InlineKeyboardButton(text="🖼 Rasm qo'shib tasdiqlash", callback_data=f"add_media_{specialist_id}"),
        ]
    ])


def admin_contact_keyboard(request_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_contact_{request_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_contact_{request_id}"),
    ]])


def admin_problem_keyboard(problem_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Yakunlash", callback_data=f"done_problem_{problem_id}"),
    ]])
