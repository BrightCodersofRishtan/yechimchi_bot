# VPS ga joylashtirish (24/7 ishlatish)

## 1. Faylларни VPS ga yuklash

Mahalliy kompyuterdan (Windows):

```bash
scp -r yechimchi_bot root@SIZNING_VPS_IP:/root/
```

Yoki `git` orqali (agar GitHub repo bo'lsa):

```bash
git clone https://github.com/sizning-repo/yechimchi_bot.git
```

---

## 2. VPS ga ulanish (SSH)

```bash
ssh root@SIZNING_VPS_IP
```

---

## 3. Python va kutubxonalarni o'rnatish

```bash
cd /root/yechimchi_bot
apt update
apt install python3 python3-pip -y
pip3 install aiogram aiosqlite
```

---

## 4. `config.py` ni to'g'rilash

```bash
nano config.py
```

`BOT_TOKEN`, `ADMIN_GROUP_ID`, `CHANNEL_ID` ni to'g'ri qiymatlar bilan to'ldiring. `Ctrl+O` saqlash, `Ctrl+X` chiqish.

---

## 5. Systemd service o'rnatish (24/7 avtomatik ishlash)

```bash
cp yechimchi-bot.service /etc/systemd/system/
nano /etc/systemd/system/yechimchi-bot.service
```

`Environment=` qatorlardagi token va ID larni o'zingizning qiymatlaringiz bilan almashtiring (yoki shunchaki `config.py` dagi qiymatlardan foydalanadi, bu qatorlarni o'chirib tashlashingiz mumkin).

```bash
systemctl daemon-reload
systemctl enable yechimchi-bot
systemctl start yechimchi-bot
```

---

## 6. Holatni tekshirish

```bash
systemctl status yechimchi-bot
```

`active (running)` ko'rinishi kerak — yashil rangda.

---

## 7. Loglarni ko'rish

```bash
journalctl -u yechimchi-bot -f
```

`Ctrl+C` bilan chiqish (bot to'xtamaydi, faqat log ko'rish to'xtaydi).

---

## 8. Botni qayta ishga tushirish (kod o'zgartirgandan keyin)

```bash
systemctl restart yechimchi-bot
```

---

## 9. Botni to'xtatish

```bash
systemctl stop yechimchi-bot
```

---

## Foydali komandalar

| Buyruq | Vazifa |
|--------|--------|
| `systemctl status yechimchi-bot` | Holatni ko'rish |
| `systemctl restart yechimchi-bot` | Qayta ishga tushirish |
| `systemctl stop yechimchi-bot` | To'xtatish |
| `journalctl -u yechimchi-bot -f` | Jonli loglar |
| `journalctl -u yechimchi-bot -n 100` | Oxirgi 100 qator log |

---

## Muhim

- VPS o'chib-yonsa ham bot **avtomatik ishga tushadi** (`enable` tufayli)
- Bot xato bilan to'xtasa **5 soniyadan keyin avtomatik qayta tiklanadi** (`Restart=always`)
- Baza fayli (`yechimchi.db`) VPS ichida saqlanadi — uni vaqti-vaqti bilan zaxira (backup) qiling:

```bash
cp /root/yechimchi_bot/yechimchi.db /root/backup_$(date +%Y%m%d).db
```
