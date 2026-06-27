from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from config import ADMIN_IDS
from database.db import (
    get_all_problem_categories, get_all_specialist_categories,
    add_problem_category, add_specialist_category,
    toggle_problem_category, toggle_specialist_category,
    delete_problem_category, delete_specialist_category,
    get_problem_category_by_id, get_specialist_category_by_id,
    get_all_specialists_full, get_specialist_by_id,
    delete_specialist, revoke_specialist, approve_specialist,
    update_specialist_field, get_stats,
    set_category_mapping, get_all_user_telegram_ids,
    set_auto_approve, disable_auto_approve,
    get_auto_approve_end_date, is_auto_approve_active,
    set_auto_contact, disable_auto_contact,
    get_auto_contact_end_date, is_auto_contact_active,
)
from utils.excel_export import export_specialists_to_excel

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


class AdminEditStates(StatesGroup):
    new_problem_cat = State()
    new_specialist_cat = State()
    edit_specialist_field = State()
    set_mapping_problem = State()
    set_mapping_specialist = State()
    broadcast_message = State()
    broadcast_confirm = State()


# ── ASOSIY ADMIN MENYU ────────────────────────────────────────

def admin_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏷 Muammo kategoriyalari", callback_data="adm_probcat")],
        [InlineKeyboardButton(text="📂 Mutaxassis kategoriyalari", callback_data="adm_speccat")],
        [InlineKeyboardButton(text="🔗 Kategoriya moslash", callback_data="adm_mapping")],
        [InlineKeyboardButton(text="👨‍💼 Mutaxassislar", callback_data="adm_specialists_0")],
        [InlineKeyboardButton(text="⚡ Auto-tasdiqlash", callback_data="adm_autoapprove")],
        [InlineKeyboardButton(text="📱 Auto-aloqa", callback_data="adm_autocontact")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="adm_stats")],
        [InlineKeyboardButton(text="📢 Xabar tarqatish (Broadcast)", callback_data="adm_broadcast")],
        [InlineKeyboardButton(text="📤 Excel export", callback_data="adm_export")],
    ])


@router.message(Command("admin"))
async def admin_start(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizda admin huquqi yo'q.")
        return

    await message.answer(
        "🛠 <b>ADMIN PANEL</b>\n\nKerakli bo'limni tanlang:",
        parse_mode="HTML",
        reply_markup=admin_main_menu()
    )


@router.callback_query(F.data == "adm_back")
async def admin_back(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return
    await callback.message.edit_text(
        "🛠 <b>ADMIN PANEL</b>\n\nKerakli bo'limni tanlang:",
        parse_mode="HTML",
        reply_markup=admin_main_menu()
    )
    await callback.answer()


# ── STATISTIKA ─────────────────────────────────────────────

@router.callback_query(F.data == "adm_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return

    s = await get_stats()
    text = (
        "📊 <b>STATISTIKA</b>\n\n"
        f"👥 Foydalanuvchilar: {s['users']}\n"
        f"📝 Jami muammolar: {s['problems']} (yangi: {s['problems_new']})\n"
        f"👨‍💼 Tasdiqlangan mutaxassislar: {s['specialists_approved']}\n"
        f"⏳ Kutilayotgan mutaxassislar: {s['specialists_pending']}\n"
        f"📩 Aloqa so'rovlari: {s['contact_requests']} (tasdiqlangan: {s['contact_approved']})\n"
        f"⭐ Baholar soni: {s['ratings']}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back")]
    ])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


# ── MUAMMO KATEGORIYALARI CRUD ────────────────────────────────

@router.callback_query(F.data == "adm_probcat")
async def admin_problem_categories(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return

    cats = await get_all_problem_categories()
    buttons = []
    for c in cats:
        status = "🟢" if c['active'] else "🔴"
        buttons.append([
            InlineKeyboardButton(text=f"{status} {c['name']}", callback_data=f"pc_toggle_{c['id']}"),
            InlineKeyboardButton(text="🗑", callback_data=f"pc_del_{c['id']}"),
        ])
    buttons.append([InlineKeyboardButton(text="➕ Yangi qo'shish", callback_data="pc_add")])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back")])

    await callback.message.edit_text(
        "🏷 <b>Muammo kategoriyalari</b>\n\n"
        "🟢 = faol, 🔴 = o'chirilgan\nBosing — holatini almashtiradi",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pc_toggle_"))
async def toggle_pc(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    cat_id = int(callback.data.split("_")[2])
    await toggle_problem_category(cat_id)
    await admin_problem_categories(callback)


@router.callback_query(F.data.startswith("pc_del_"))
async def delete_pc(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    cat_id = int(callback.data.split("_")[2])
    await delete_problem_category(cat_id)
    await callback.answer("🗑 O'chirildi!")
    await admin_problem_categories(callback)


@router.callback_query(F.data == "pc_add")
async def add_pc_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminEditStates.new_problem_cat)
    await callback.message.answer("➕ Yangi muammo kategoriyasi nomini yozing:\n(Misol: 🏥 Sog'liq)")
    await callback.answer()


@router.message(AdminEditStates.new_problem_cat)
async def add_pc_save(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("❌ Nomi juda qisqa.")
        return
    cat_id = await add_problem_category(name)
    await state.clear()
    if cat_id:
        await message.answer(f"✅ '{name}' qo'shildi!")
    else:
        await message.answer(f"❌ '{name}' allaqachon mavjud yoki xato yuz berdi.")


# ── MUTAXASSIS KATEGORIYALARI CRUD ────────────────────────────

@router.callback_query(F.data == "adm_speccat")
async def admin_specialist_categories(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return

    cats = await get_all_specialist_categories()
    buttons = []
    for c in cats:
        status = "🟢" if c['active'] else "🔴"
        buttons.append([
            InlineKeyboardButton(text=f"{status} {c['name']}", callback_data=f"sc_toggle_{c['id']}"),
            InlineKeyboardButton(text="🗑", callback_data=f"sc_del_{c['id']}"),
        ])
    buttons.append([InlineKeyboardButton(text="➕ Yangi qo'shish", callback_data="sc_add")])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back")])

    await callback.message.edit_text(
        "📂 <b>Mutaxassis kategoriyalari</b>\n\n"
        "🟢 = faol, 🔴 = o'chirilgan\nBosing — holatini almashtiradi",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sc_toggle_"))
async def toggle_sc(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    cat_id = int(callback.data.split("_")[2])
    await toggle_specialist_category(cat_id)
    await admin_specialist_categories(callback)


@router.callback_query(F.data.startswith("sc_del_"))
async def delete_sc(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    cat_id = int(callback.data.split("_")[2])
    await delete_specialist_category(cat_id)
    await callback.answer("🗑 O'chirildi!")
    await admin_specialist_categories(callback)


@router.callback_query(F.data == "sc_add")
async def add_sc_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminEditStates.new_specialist_cat)
    await callback.message.answer("➕ Yangi mutaxassis kategoriyasi nomini yozing:\n(Misol: 🏠 Ko'chmas mulk)")
    await callback.answer()


@router.message(AdminEditStates.new_specialist_cat)
async def add_sc_save(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("❌ Nomi juda qisqa.")
        return
    cat_id = await add_specialist_category(name)
    await state.clear()
    if cat_id:
        await message.answer(f"✅ '{name}' qo'shildi!")
    else:
        await message.answer(f"❌ '{name}' allaqachon mavjud yoki xato yuz berdi.")


# ── KATEGORIYA MOSLASH (MAPPING) ──────────────────────────────

@router.callback_query(F.data == "adm_mapping")
async def admin_mapping_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return

    cats = await get_all_problem_categories()
    buttons = []
    for c in cats:
        buttons.append([InlineKeyboardButton(text=c['name'], callback_data=f"map_p_{c['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back")])

    await callback.message.edit_text(
        "🔗 <b>Kategoriya moslash</b>\n\n"
        "Qaysi muammo kategoriyasini moslaymiz?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("map_p_"))
async def admin_mapping_choose_spec(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    prob_id = int(callback.data.split("_")[2])
    await state.update_data(mapping_problem_id=prob_id)

    cats = await get_all_specialist_categories()
    buttons = []
    for c in cats:
        buttons.append([InlineKeyboardButton(text=c['name'], callback_data=f"map_s_{c['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_mapping")])

    prob = await get_problem_category_by_id(prob_id)
    await callback.message.edit_text(
        f"🔗 '{prob['name']}' qaysi mutaxassis kategoriyasiga mos keladi?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("map_s_"))
async def admin_mapping_save(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    spec_id = int(callback.data.split("_")[2])
    data = await state.get_data()
    prob_id = data.get("mapping_problem_id")

    if not prob_id:
        await callback.answer("❌ Xatolik, qaytadan boshlang.", show_alert=True)
        return

    await set_category_mapping(prob_id, spec_id)
    await state.clear()

    prob = await get_problem_category_by_id(prob_id)
    spec = await get_specialist_category_by_id(spec_id)

    await callback.message.edit_text(
        f"✅ Moslandi:\n'{prob['name']}' → '{spec['name']}'",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 Admin panelga", callback_data="adm_back")
        ]])
    )
    await callback.answer("✅ Saqlandi!")


# ── MUTAXASSISLAR CRUD ─────────────────────────────────────────

@router.callback_query(F.data.startswith("adm_specialists_"))
async def admin_specialists_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return

    page = int(callback.data.split("_")[2])
    page_size = 5
    all_specs = await get_all_specialists_full()
    total_pages = (len(all_specs) - 1) // page_size + 1 if all_specs else 1
    start = page * page_size
    page_items = all_specs[start:start + page_size]

    buttons = []
    for s in page_items:
        status = "✅" if s['approved'] else "⏳"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {s['fullname']} ({s['profession']})",
            callback_data=f"adm_spec_view_{s['id']}"
        )])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"adm_specialists_{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
    if start + page_size < len(all_specs):
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"adm_specialists_{page+1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back")])

    await callback.message.edit_text(
        f"👨‍💼 <b>Barcha mutaxassislar</b> ({len(all_specs)} ta)\n\n"
        f"✅ = tasdiqlangan, ⏳ = kutilmoqda",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_spec_view_"))
async def admin_specialist_view(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    spec_id = int(callback.data.split("_")[3])
    spec = await get_specialist_by_id(spec_id)
    if not spec:
        await callback.answer("Topilmadi!", show_alert=True)
        return

    status = "✅ Tasdiqlangan" if spec['approved'] else "⏳ Kutilmoqda"
    text = (
        f"👤 {spec['fullname']}\n"
        f"🏷 {spec.get('category', '-')}\n"
        f"💼 {spec['profession']}\n"
        f"📱 {spec['phone']}\n"
        f"📝 {spec['description']}\n"
        f"⭐ Tavsiyalar: {spec['recommendation_count']}\n"
        f"Holat: {status}"
    )

    buttons = []
    if spec['approved']:
        buttons.append([InlineKeyboardButton(text="⛔ Bekor qilish (kanaldan yo'q qiladi)", callback_data=f"adm_revoke_{spec_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"adm_approve_{spec_id}")])
    buttons.append([InlineKeyboardButton(text="✏️ Ism", callback_data=f"adm_edit_fullname_{spec_id}"),
                     InlineKeyboardButton(text="✏️ Tel", callback_data=f"adm_edit_phone_{spec_id}")])
    buttons.append([InlineKeyboardButton(text="✏️ Kasb", callback_data=f"adm_edit_profession_{spec_id}"),
                     InlineKeyboardButton(text="✏️ Tavsif", callback_data=f"adm_edit_description_{spec_id}")])
    buttons.append([InlineKeyboardButton(text="🗑 Butunlay o'chirish", callback_data=f"adm_delete_{spec_id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Ro'yxatga", callback_data="adm_specialists_0")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("adm_revoke_"))
async def admin_revoke(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    spec_id = int(callback.data.split("_")[2])
    await revoke_specialist(spec_id)
    await callback.answer("⛔ Bekor qilindi! (Kanaldagi eski post qolishi mumkin, qo'lda o'chiring)", show_alert=True)
    await admin_specialist_view(callback)


@router.callback_query(F.data.startswith("adm_approve_"))
async def admin_approve_from_panel(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    spec_id = int(callback.data.split("_")[2])
    await approve_specialist(spec_id)
    await callback.answer("✅ Tasdiqlandi!")
    await admin_specialist_view(callback)


@router.callback_query(F.data.startswith("adm_delete_"))
async def admin_delete_confirm(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    spec_id = int(callback.data.split("_")[2])
    buttons = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Ha, o'chir", callback_data=f"adm_delete_confirm_{spec_id}"),
        InlineKeyboardButton(text="❌ Bekor", callback_data=f"adm_spec_view_{spec_id}"),
    ]])
    await callback.message.edit_text(
        "⚠️ Rostdan ham butunlay o'chirmoqchimisiz? Bu amalni qaytarib bo'lmaydi!",
        reply_markup=buttons
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_delete_confirm_"))
async def admin_delete_final(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    spec_id = int(callback.data.split("_")[3])
    await delete_specialist(spec_id)
    await callback.answer("🗑 O'chirildi!", show_alert=True)
    await callback.message.edit_text(
        "🗑 Mutaxassis butunlay o'chirildi.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 Ro'yxatga", callback_data="adm_specialists_0")
        ]])
    )


@router.callback_query(F.data.startswith("adm_edit_"))
async def admin_edit_field_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    parts = callback.data.split("_")
    field = parts[2]
    spec_id = int(parts[3])

    await state.update_data(edit_spec_id=spec_id, edit_field=field)
    await state.set_state(AdminEditStates.edit_specialist_field)

    field_names = {
        "fullname": "Ism",
        "phone": "Telefon",
        "profession": "Kasb",
        "description": "Tavsif",
    }
    await callback.message.answer(f"✏️ Yangi {field_names.get(field, field)} qiymatini yozing:")
    await callback.answer()


@router.message(AdminEditStates.edit_specialist_field)
async def admin_edit_field_save(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    spec_id = data.get("edit_spec_id")
    field = data.get("edit_field")

    if not spec_id or not field:
        await state.clear()
        await message.answer("❌ Xatolik. Qaytadan boshlang.")
        return

    await update_specialist_field(spec_id, field, message.text.strip())
    await state.clear()
    await message.answer(f"✅ Yangilandi!")


# ── BROADCAST (XABAR TARQATISH) ──────────────────────────────

@router.callback_query(F.data == "adm_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return

    await state.set_state(AdminEditStates.broadcast_message)
    await callback.message.answer(
        "📢 Barcha foydalanuvchilarga yuboriladigan xabarni yozing:\n\n"
        "(Matn, rasm yoki video yuborishingiz mumkin)"
    )
    await callback.answer()


@router.message(AdminEditStates.broadcast_message)
async def admin_broadcast_preview(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    # Xabarni saqlaymiz (keyin yuborish uchun)
    await state.update_data(
        broadcast_text=message.text or message.caption or "",
        broadcast_photo=message.photo[-1].file_id if message.photo else None,
        broadcast_video=message.video.file_id if message.video else None,
    )
    await state.set_state(AdminEditStates.broadcast_confirm)

    user_count = len(await get_all_user_telegram_ids())

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Yuborish", callback_data="bc_send"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="bc_cancel"),
    ]])

    await message.answer(
        f"📢 <b>Xabar tasdiqlash</b>\n\n"
        f"Quyidagi xabar <b>{user_count} foydalanuvchiga</b> yuboriladi:\n\n"
        f"━━━━━━━━━━━━━━\n{message.text or message.caption or '(media xabar)'}\n━━━━━━━━━━━━━━\n\n"
        f"Davom etamizmi?",
        parse_mode="HTML",
        reply_markup=kb
    )


@router.callback_query(F.data == "bc_cancel")
async def admin_broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.clear()
    await callback.message.edit_text("❌ Xabar tarqatish bekor qilindi.")
    await callback.answer()


@router.callback_query(F.data == "bc_send")
async def admin_broadcast_send(callback: CallbackQuery, state: FSMContext, bot):
    if not is_admin(callback.from_user.id):
        return

    data = await state.get_data()
    text = data.get("broadcast_text", "")
    photo = data.get("broadcast_photo")
    video = data.get("broadcast_video")
    await state.clear()

    user_ids = await get_all_user_telegram_ids()
    await callback.message.edit_text(f"📤 Yuborilmoqda... ({len(user_ids)} foydalanuvchi)")
    await callback.answer()

    success = 0
    failed = 0

    for uid in user_ids:
        try:
            if photo:
                await bot.send_photo(uid, photo=photo, caption=text)
            elif video:
                await bot.send_video(uid, video=video, caption=text)
            else:
                await bot.send_message(uid, text)
            success += 1
        except Exception:
            failed += 1

        # Telegram flood limit uchun kichik kutish
        import asyncio
        await asyncio.sleep(0.05)

    await callback.message.answer(
        f"✅ <b>Xabar tarqatish yakunlandi!</b>\n\n"
        f"✅ Yuborildi: {success}\n"
        f"❌ Yetib bormadi: {failed}",
        parse_mode="HTML"
    )


# ── AUTO-TASDIQLASH ────────────────────────────────────────────

@router.callback_query(F.data == "adm_autoapprove")
async def admin_autoapprove_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return

    active = await is_auto_approve_active()
    end_date = await get_auto_approve_end_date()

    if active:
        from datetime import datetime
        end = datetime.fromisoformat(end_date)
        status_text = (
            f"🟢 <b>Auto-tasdiqlash YOQILGAN</b>\n\n"
            f"📅 Tugash sanasi: {end.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Yangi mutaxassislar avtomatik tasdiqlanadi."
        )
        buttons = [
            [InlineKeyboardButton(text="⛔ O'chirish", callback_data="aa_disable")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back")],
        ]
    else:
        status_text = (
            "🔴 <b>Auto-tasdiqlash O'CHIRILGAN</b>\n\n"
            "Muddatni tanlang — shu muddatgacha barcha yangi\n"
            "mutaxassislar avtomatik tasdiqlanadi:"
        )
        buttons = [
            [InlineKeyboardButton(text="📅 3 oylik", callback_data="aa_set_3")],
            [InlineKeyboardButton(text="📅 6 oylik", callback_data="aa_set_6")],
            [InlineKeyboardButton(text="📅 1 yillik", callback_data="aa_set_12")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back")],
        ]

    await callback.message.edit_text(
        f"⚡ <b>AUTO-TASDIQLASH</b>\n\n{status_text}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("aa_set_"))
async def admin_autoapprove_set(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    months = int(callback.data.split("_")[2])
    from datetime import datetime, timedelta
    end_date = datetime.now() + timedelta(days=months * 30)
    await set_auto_approve(end_date.isoformat())

    labels = {3: "3 oy", 6: "6 oy", 12: "1 yil"}
    label = labels.get(months, f"{months} oy")

    await callback.answer(f"✅ Auto-tasdiqlash {label}ga yoqildi!", show_alert=True)
    await admin_autoapprove_menu(callback)


@router.callback_query(F.data == "aa_disable")
async def admin_autoapprove_disable(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    await disable_auto_approve()
    await callback.answer("⛔ Auto-tasdiqlash o'chirildi!", show_alert=True)
    await admin_autoapprove_menu(callback)


# ── AUTO-ALOQA ───────────────────────────────────────────────

@router.callback_query(F.data == "adm_autocontact")
async def admin_autocontact_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return

    active = await is_auto_contact_active()
    end_date = await get_auto_contact_end_date()

    if active:
        from datetime import datetime
        end = datetime.fromisoformat(end_date)
        status_text = (
            f"🟢 <b>Auto-aloqa YOQILGAN</b>\n\n"
            f"📅 Tugash sanasi: {end.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Foydalanuvchilar mutaxassis raqamini\n"
            f"admin tasdiqisiz oladi."
        )
        buttons = [
            [InlineKeyboardButton(text="⛔ O'chirish", callback_data="ac_disable")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back")],
        ]
    else:
        status_text = (
            "🔴 <b>Auto-aloqa O'CHIRILGAN</b>\n\n"
            "Muddatni tanlang — shu muddatgacha\n"
            "mutaxassis raqami admin tasdiqisiz\n"
            "avtomatik yuboriladi:"
        )
        buttons = [
            [InlineKeyboardButton(text="📅 1 oylik", callback_data="ac_set_1")],
            [InlineKeyboardButton(text="📅 3 oylik", callback_data="ac_set_3")],
            [InlineKeyboardButton(text="📅 6 oylik", callback_data="ac_set_6")],
            [InlineKeyboardButton(text="📅 1 yillik", callback_data="ac_set_12")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back")],
        ]

    await callback.message.edit_text(
        f"📱 <b>AUTO-ALOQA</b>\n\n{status_text}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ac_set_"))
async def admin_autocontact_set(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    months = int(callback.data.split("_")[2])
    from datetime import datetime, timedelta
    end_date = datetime.now() + timedelta(days=months * 30)
    await set_auto_contact(end_date.isoformat())

    labels = {1: "1 oy", 3: "3 oy", 6: "6 oy", 12: "1 yil"}
    label = labels.get(months, f"{months} oy")

    await callback.answer(f"✅ Auto-aloqa {label}ga yoqildi!", show_alert=True)
    await admin_autocontact_menu(callback)


@router.callback_query(F.data == "ac_disable")
async def admin_autocontact_disable(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    await disable_auto_contact()
    await callback.answer("⛔ Auto-aloqa o'chirildi!", show_alert=True)
    await admin_autocontact_menu(callback)


# ── EXCEL EXPORT ──────────────────────────────────────────────

@router.callback_query(F.data == "adm_export")
async def admin_export_excel(callback: CallbackQuery, bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return

    await callback.answer("⏳ Tayyorlanmoqda...")

    import os
    from datetime import datetime

    filename = f"mutaxassislar_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    filepath = os.path.join("/tmp", filename)

    try:
        await export_specialists_to_excel(filepath)

        from aiogram.types import FSInputFile
        doc = FSInputFile(filepath, filename=filename)
        await bot.send_document(
            callback.from_user.id,
            document=doc,
            caption="📤 Barcha mutaxassislar ro'yxati (Excel)"
        )
    except Exception as e:
        await callback.message.answer(f"❌ Xatolik: {e}")
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
