# Yechimchi Bot

Telegram bot: muammolarni yig'ish va mutaxassislarni ulash.

## O'rnatish

```bash
pip install -r requirements.txt
```

## Sozlash

`.env.example` faylini `.env` ga nusxalash va to'ldirish:

```bash
cp .env.example .env
```

Keyin quyidagilarni to'ldiring:
- `BOT_TOKEN` — @BotFather dan oling
- `ADMIN_GROUP_ID` — Admin guruh ID (manfiy son, masalan: -100123456789)
- `CHANNEL_ID` — Kanal username (@yechimchi_channel)

## Ishga tushirish

```bash
python bot.py
```

## Struktura

```
yechimchi_bot/
├── bot.py              # Asosiy fayl
├── config.py           # Sozlamalar
├── requirements.txt
├── handlers/
│   ├── user.py         # Muammo yuborish
│   ├── specialist.py   # Tavsiya + Ko'rish
│   ├── contact.py      # Aloqa so'rovlari
│   └── admin.py        # Admin amallar
├── keyboards/
│   └── keyboards.py    # Barcha tugmalar
└── database/
    └── db.py           # SQLite so'rovlar
```

## Qanday ishlaydi

1. **Muammom bor** → Kategoriya → Matn → Telefon → Admin guruhiga yuboriladi
2. **Mutaxassis tavsiya qilaman** → Ma'lumotlar → Admin tasdiqlaydi → Kanalga chiqadi
3. **Mutaxassislar ro'yxati** → Kasb → TOP ro'yxat → Aloqa so'rovi → Admin tasdiqlaydi → Telefon yuboriladi
