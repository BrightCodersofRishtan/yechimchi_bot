from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart, Command

from config import ADMIN_GROUP_ID
from database.db import (
    get_or_create_user, update_user_phone, save_problem, get_last_problem_id,
    get_specialists_by_category, get_active_problem_categories,
    get_problem_category_by_id, get_mapped_specialist_category,
)
from keyboards.keyboards import main_menu, categories_keyboard, phone_keyboard, specialists_list_keyboard

router = Router()


class ProblemStates(StatesGroup):
    category = State()
    problem_text = State()
    phone = State()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await get_or_create_user(
        telegram_id=message.from_user.id,
        fullname=message.from_user.full_name
    )
    await message.answer(
        "👋 Assalomu alaykum! Yechimchi botga xush kelibsiz!\n\n"
        "Bu bot orqali muammongizni yozib qoldirishingiz yoki "
        "ishonchli mutaxassislarni topishingiz mumkin.",
        reply_markup=main_menu()
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "ℹ️ Yordam:\n\n"
        "🔍 /problem — Muammongizni yozing\n"
        "⭐ /recommend — Mutaxassis tavsiya qiling\n"
        "📚 /specialists — Mutaxassislar ro'yxati\n"
        "🏠 /start — Bosh menyuga qaytish"
    )


@router.message(Command("problem"))
async def cmd_problem(message: Message, state: FSMContext):
    await problem_start(message, state)


@router.message(F.text == "🔍 Muammom bor")
async def problem_start(message: Message, state: FSMContext):
    await state.set_state(ProblemStates.category)
    cats = await get_active_problem_categories()
    await message.answer(
        "Muammongiz qaysi sohaga tegishli?",
        reply_markup=categories_keyboard(cats)
    )


@router.message(ProblemStates.category, F.text == "🔙 Orqaga")
async def problem_category_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu:", reply_markup=main_menu())


@router.message(ProblemStates.category)
async def problem_category(message: Message, state: FSMContext):
    cats = await get_active_problem_categories()
    cat_match = next((c for c in cats if c['name'] == message.text), None)

    if not cat_match:
        await message.answer(
            "❌ Iltimos, ro'yxatdan kategoriya tanlang.",
            reply_markup=categories_keyboard(cats)
        )
        return

    await state.update_data(category=message.text, category_id=cat_match['id'])
    await state.set_state(ProblemStates.problem_text)
    await message.answer(
        f"✅ Kategoriya: {message.text}\n\n"
        "Muammongizni batafsil yozing:",
        reply_markup=phone_keyboard()
    )


@router.message(ProblemStates.problem_text, F.text == "🔙 Orqaga")
async def problem_text_back(message: Message, state: FSMContext):
    await state.set_state(ProblemStates.category)
    cats = await get_active_problem_categories()
    await message.answer("Kategoriya tanlang:", reply_markup=categories_keyboard(cats))


@router.message(ProblemStates.problem_text)
async def problem_text_handler(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 5:
        await message.answer("❌ Muammoni biroz batafsil yozing (kamida 5 ta harf).")
        return
    await state.update_data(problem_text=message.text.strip())
    await state.set_state(ProblemStates.phone)
    await message.answer(
        "Telefon raqamingizni yuboring:",
        reply_markup=phone_keyboard()
    )


@router.message(ProblemStates.phone, F.text == "🔙 Orqaga")
async def problem_phone_back(message: Message, state: FSMContext):
    await state.set_state(ProblemStates.problem_text)
    await message.answer("Muammongizni yozing:", reply_markup=phone_keyboard())


@router.message(ProblemStates.phone, F.contact)
async def problem_phone_contact(message: Message, state: FSMContext, bot):
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    await _save_and_notify(message, state, bot, phone)


@router.message(ProblemStates.phone, F.text)
async def problem_phone_text(message: Message, state: FSMContext, bot):
    if message.text == "🔙 Orqaga":
        await state.set_state(ProblemStates.problem_text)
        await message.answer("Muammongizni yozing:", reply_markup=phone_keyboard())
        return
    phone = message.text.strip()
    if len(phone) < 9:
        await message.answer(
            "❌ Telefon raqam noto'g'ri!\nFormat: +998901234567",
            reply_markup=phone_keyboard()
        )
        return
    await _save_and_notify(message, state, bot, phone)


async def _save_and_notify(message, state, bot, phone):
    data = await state.get_data()
    user = await get_or_create_user(message.from_user.id, message.from_user.full_name)
    await update_user_phone(message.from_user.id, phone)
    await save_problem(user['id'], data['category'], data['problem_text'])
    problem_id = await get_last_problem_id()

    from keyboards.keyboards import admin_problem_keyboard
    admin_text = (
        f"🆕 YANGI MUAMMO\n\n"
        f"👤 Foydalanuvchi: {message.from_user.full_name}\n"
        f"📱 Telefon: {phone}\n"
        f"🏷️ Kategoriya: {data['category']}\n"
        f"📝 Muammo:\n{data['problem_text']}"
    )
    try:
        await bot.send_message(
            ADMIN_GROUP_ID,
            admin_text,
            reply_markup=admin_problem_keyboard(problem_id)
        )
    except Exception as e:
        import logging
        logging.error(f"Admin guruhga yuborishda xato: {e}")

    await state.clear()
    await message.answer(
        "✅ Muammongiz qabul qilindi!\n"
        "Tez orada mutaxassis siz bilan bog'lanadi.",
        reply_markup=main_menu()
    )

    # Shu kategoriyadan mutaxassislarni moslash (baza orqali)
    category_id = data.get('category_id')
    if category_id:
        mapped = await get_mapped_specialist_category(category_id)
        if mapped:
            specialists = await get_specialists_by_category(mapped['name'])
            if specialists:
                await message.answer(
                    f"💡 Shu sohadagi mutaxassislar:\n"
                    f"Quyidagilardan biri bilan hoziroq bog'lanishingiz mumkin:",
                    reply_markup=specialists_list_keyboard(specialists, page=0, category_idx=mapped['id'])
                )
            else:
                await message.answer(
                    f"ℹ️ Hozircha {mapped['name']} bo'yicha\n"
                    f"tasdiqlangan mutaxassis yo'q.\n"
                    f"Admin tez orada siz bilan bog'lanadi."
                )


@router.message(F.text == "🔙 Orqaga")
async def go_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu:", reply_markup=main_menu())
