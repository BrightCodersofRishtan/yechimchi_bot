from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from config import ADMIN_GROUP_ID
from database.db import (
    get_or_create_user, save_specialist, get_specialists_by_category,
    get_specialist_by_id, increment_recommendation,
    get_active_specialist_categories, get_specialist_category_by_id,
    get_specialist_rating,
)
from keyboards.keyboards import (
    main_menu, specialist_categories_keyboard, back_keyboard,
    specialists_list_keyboard, contact_keyboard, admin_specialist_with_media_keyboard
)

router = Router()


class RecommendStates(StatesGroup):
    fullname = State()
    category = State()
    profession = State()
    phone = State()
    reason = State()


class BrowseStates(StatesGroup):
    category = State()


# ── TAVSIYA QILISH ──────────────────────────────────────────

@router.message(Command("recommend"))
@router.message(F.text == "⭐ Mutaxassis tavsiya qilaman")
async def recommend_start(message: Message, state: FSMContext):
    await state.set_state(RecommendStates.fullname)
    await message.answer(
        "Mutaxassisning to'liq ismini kiriting:",
        reply_markup=back_keyboard()
    )


@router.message(RecommendStates.fullname, F.text == "🔙 Orqaga")
async def recommend_fullname_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu:", reply_markup=main_menu())


@router.message(RecommendStates.fullname)
async def recommend_name(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 3:
        await message.answer("❌ Ism kamida 3 ta harf bo'lishi kerak.")
        return
    await state.update_data(fullname=message.text.strip())
    await state.set_state(RecommendStates.category)

    cats = await get_active_specialist_categories()
    await message.answer(
        "Qaysi sohaga kiradi?",
        reply_markup=specialist_categories_keyboard(cats)
    )


@router.message(RecommendStates.category, F.text == "🔙 Orqaga")
async def recommend_category_back(message: Message, state: FSMContext):
    await state.set_state(RecommendStates.fullname)
    await message.answer("Mutaxassisning to'liq ismini kiriting:", reply_markup=back_keyboard())


@router.message(RecommendStates.category)
async def recommend_category(message: Message, state: FSMContext):
    cats = await get_active_specialist_categories()
    cat_names = [c['name'] for c in cats]

    if message.text not in cat_names:
        await message.answer(
            "❌ Iltimos, ro'yxatdan kategoriya tanlang.",
            reply_markup=specialist_categories_keyboard(cats)
        )
        return

    await state.update_data(category=message.text)
    await state.set_state(RecommendStates.profession)
    await message.answer(
        f"✅ Kategoriya: {message.text}\n\n"
        "Aniq kasbini yozing:\n"
        "Misol: Kardiolog, Soliq advokati, Android dasturchi...",
        reply_markup=back_keyboard()
    )


@router.message(RecommendStates.profession, F.text == "🔙 Orqaga")
async def recommend_profession_back(message: Message, state: FSMContext):
    await state.set_state(RecommendStates.category)
    cats = await get_active_specialist_categories()
    await message.answer("Kategoriya tanlang:", reply_markup=specialist_categories_keyboard(cats))


@router.message(RecommendStates.profession)
async def recommend_profession(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("❌ Kasbni to'liq yozing.")
        return
    await state.update_data(profession=message.text.strip())
    await state.set_state(RecommendStates.phone)
    await message.answer(
        "Telefon raqamini kiriting (masalan: +998901234567):",
        reply_markup=back_keyboard()
    )


@router.message(RecommendStates.phone, F.text == "🔙 Orqaga")
async def recommend_phone_back(message: Message, state: FSMContext):
    await state.set_state(RecommendStates.profession)
    data = await state.get_data()
    await message.answer(
        f"Aniq kasbini yozing (kategoriya: {data.get('category', '')}):",
        reply_markup=back_keyboard()
    )


@router.message(RecommendStates.phone)
async def recommend_phone(message: Message, state: FSMContext):
    if message.contact:
        phone = message.contact.phone_number
        if not phone.startswith("+"):
            phone = "+" + phone
        await state.update_data(phone=phone)
        await state.set_state(RecommendStates.reason)
        await message.answer(
            f"✅ Telefon: {phone}\n\nNima uchun tavsiya qilasiz?",
            reply_markup=back_keyboard()
        )
        return

    if message.text:
        phone = message.text.strip()
        if len(phone) < 9:
            await message.answer(
                "❌ Telefon raqam noto'g'ri!\nFormat: +998901234567",
                reply_markup=back_keyboard()
            )
            return
        await state.update_data(phone=phone)
        await state.set_state(RecommendStates.reason)
        await message.answer(
            "Nima uchun tavsiya qilasiz? (qisqacha sabab yozing):",
            reply_markup=back_keyboard()
        )
        return

    await message.answer("❌ Telefon raqam yuboring.", reply_markup=back_keyboard())


@router.message(RecommendStates.reason, F.text == "🔙 Orqaga")
async def recommend_reason_back(message: Message, state: FSMContext):
    await state.set_state(RecommendStates.phone)
    await message.answer("Telefon raqamini kiriting:", reply_markup=back_keyboard())


@router.message(RecommendStates.reason)
async def recommend_reason(message: Message, state: FSMContext, bot):
    if not message.text or len(message.text.strip()) < 3:
        await message.answer("❌ Sabab kamida 3 ta harf bo'lishi kerak.")
        return

    data = await state.get_data()

    if not all([data.get('fullname'), data.get('category'), data.get('profession'), data.get('phone')]):
        await state.clear()
        await message.answer(
            "❌ Xatolik yuz berdi. Qaytadan boshlang.",
            reply_markup=main_menu()
        )
        return

    spec_id = await save_specialist(
        fullname=data['fullname'],
        category=data['category'],
        profession=data['profession'],
        phone=data['phone'],
        description=message.text.strip()
    )

    await increment_recommendation(spec_id)

    admin_text = (
        f"⭐ YANGI MUTAXASSIS TAVSIYASI\n\n"
        f"👤 Ism: {data['fullname']}\n"
        f"🏷 Kategoriya: {data['category']}\n"
        f"💼 Kasbi: {data['profession']}\n"
        f"📱 Telefon: {data['phone']}\n"
        f"💬 Tavsiya sababi: {message.text.strip()}\n\n"
        f"Tavsiya qilgan: {message.from_user.full_name}"
    )
    try:
        await bot.send_message(
            ADMIN_GROUP_ID,
            admin_text,
            reply_markup=admin_specialist_with_media_keyboard(spec_id)
        )
    except Exception as e:
        import logging
        logging.error(f"Admin guruhga yuborishda xato: {e}")

    await state.clear()
    await message.answer(
        "✅ Tavsiyangiz yuborildi! Admin ko'rib chiqadi.",
        reply_markup=main_menu()
    )


# ── MUTAXASSISLARNI KO'RISH ──────────────────────────────────

@router.message(Command("specialists"))
@router.message(F.text == "📚 Tavsiya etilgan mutaxassislar")
async def browse_start(message: Message, state: FSMContext):
    await state.set_state(BrowseStates.category)
    cats = await get_active_specialist_categories()
    await message.answer(
        "Qaysi soha mutaxassisini qidiryapsiz?",
        reply_markup=specialist_categories_keyboard(cats)
    )


@router.message(BrowseStates.category, F.text == "🔙 Orqaga")
async def browse_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu:", reply_markup=main_menu())


@router.message(BrowseStates.category)
async def browse_category(message: Message, state: FSMContext):
    cats = await get_active_specialist_categories()
    cat_match = next((c for c in cats if c['name'] == message.text), None)

    if not cat_match:
        await message.answer(
            "❌ Iltimos, ro'yxatdan kategoriya tanlang.",
            reply_markup=specialist_categories_keyboard(cats)
        )
        return

    category = cat_match['name']
    category_id = cat_match['id']
    specialists = await get_specialists_by_category(category)
    await state.clear()

    if not specialists:
        await message.answer(
            f"😔 {category} bo'yicha hozircha tasdiqlangan mutaxassis yo'q.",
            reply_markup=main_menu()
        )
        return

    await message.answer(
        f"✅ {category} mutaxassislari ({len(specialists)} ta):",
        reply_markup=specialists_list_keyboard(specialists, page=0, category_idx=category_id)
    )
    await message.answer("Bosh menyuga qaytish:", reply_markup=main_menu())


@router.callback_query(F.data.startswith("page_"))
async def paginate_specialists(callback: CallbackQuery):
    parts = callback.data.split("_")
    category_id = int(parts[1])
    page = int(parts[2])

    cat = await get_specialist_category_by_id(category_id)
    if not cat:
        await callback.answer("Kategoriya topilmadi!", show_alert=True)
        return

    specialists = await get_specialists_by_category(cat['name'])

    if not specialists:
        await callback.answer("Mutaxassis topilmadi!", show_alert=True)
        return

    await callback.message.edit_text(
        f"✅ {cat['name']} mutaxassislari ({len(specialists)} ta):",
        reply_markup=specialists_list_keyboard(specialists, page=page, category_idx=category_id)
    )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("spec_"))
async def show_specialist(callback: CallbackQuery):
    spec_id = int(callback.data.split("_")[1])
    spec = await get_specialist_by_id(spec_id)

    if not spec:
        await callback.answer("Topilmadi!", show_alert=True)
        return

    avg = await get_specialist_rating(spec_id)
    stars_display = f"{avg}⭐" if avg > 0 else "hali baho yo'q"

    text = (
        f"👤 {spec['fullname']}\n"
        f"🏷 {spec.get('category', '')}\n"
        f"💼 {spec['profession']}\n"
        f"📊 Reyting: {stars_display} ({spec['recommendation_count']} tavsiya)\n"
        f"📝 {spec['description']}"
    )
    await callback.message.answer(text, reply_markup=contact_keyboard(spec_id))
    await callback.answer()
