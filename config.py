import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8864147886:AAFd0tKiiyCTtNxYTzn2l17kGyH_cqhyj78")
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID", "-1003919614880"))
CHANNEL_ID = os.getenv("CHANNEL_ID", "@yechimchi")
DATABASE_URL = os.getenv("DATABASE_URL", "yechimchi.db")

# /admin komandasini ishlatish huquqiga ega shaxsiy Telegram ID lar
# Telegram ID ni bilish uchun @userinfobot ga yozing
ADMIN_IDS = [
    934180087,  # <-- o'zingizning Telegram ID ingizni qo'ying
]

# Muammo kategoriyalari
CATEGORIES = [
    "🏥 Sog'liq",
    "⚖️ Huquq",
    "🚢 Bojxona",
    "🏗️ Qurilish",
    "📚 Ta'lim",
    "💻 IT",
    "💼 Biznes",
    "📌 Boshqa",
]

# Mutaxassis kategoriyalari (keng)
SPECIALIST_CATEGORIES = [
    "🏥 Tibbiyot",
    "⚖️ Huquq va Advokatlik",
    "🚢 Bojxona va Tashqi savdo",
    "🏗️ Qurilish va Dizayn",
    "💻 IT va Dasturlash",
    "📚 Ta'lim va Repetitorlik",
    "💼 Biznes va Marketing",
    "🏦 Moliya va Buxgalteriya",
    "🔧 Texnik xizmat va Ta'mirlash",
    "🌱 Qishloq xo'jaligi",
    "🚗 Avtomobil va Transport",
    "🍽️ Oshpazlik va Catering",
    "💇 Go'zallik va Sog'lomlashtirish",
    "🏠 Ko'chmas mulk",
    "📌 Boshqa",
]

# Muammo kategoriyasi → Mutaxassis kategoriyasi moslash
CATEGORY_MAP = {
    "🏥 Sog'liq":    "🏥 Tibbiyot",
    "⚖️ Huquq":      "⚖️ Huquq va Advokatlik",
    "🚢 Bojxona":    "🚢 Bojxona va Tashqi savdo",
    "🏗️ Qurilish":   "🏗️ Qurilish va Dizayn",
    "📚 Ta'lim":     "📚 Ta'lim va Repetitorlik",
    "💻 IT":         "💻 IT va Dasturlash",
    "💼 Biznes":     "💼 Biznes va Marketing",
    "📌 Boshqa":     None,  # Boshqa uchun ko'rsatilmaydi
}
