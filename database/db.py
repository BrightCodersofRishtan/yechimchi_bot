import aiosqlite
from config import DATABASE_URL

async def init_db():
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                fullname TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS problems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                problem_text TEXT,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS specialists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fullname TEXT NOT NULL,
                category TEXT,
                profession TEXT NOT NULL,
                phone TEXT NOT NULL,
                description TEXT,
                recommendation_count INTEGER DEFAULT 0,
                approved INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                specialist_id INTEGER,
                user_id INTEGER,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (specialist_id) REFERENCES specialists(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS contact_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                specialist_id INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (specialist_id) REFERENCES specialists(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                specialist_id INTEGER,
                stars INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (specialist_id) REFERENCES specialists(id)
            )
        """)
        # Mavjud bazaga yangi ustunlar qo'shish
        for sql in [
            "ALTER TABLE specialists ADD COLUMN category TEXT",
            "ALTER TABLE specialists ADD COLUMN rating_sum INTEGER DEFAULT 0",
            "ALTER TABLE specialists ADD COLUMN rating_count INTEGER DEFAULT 0",
        ]:
            try:
                await db.execute(sql)
            except Exception:
                pass

        # Kategoriyalar jadvali (admin CRUD qila oladigan)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS problem_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS specialist_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS category_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem_category_id INTEGER,
                specialist_category_id INTEGER,
                FOREIGN KEY (problem_category_id) REFERENCES problem_categories(id),
                FOREIGN KEY (specialist_category_id) REFERENCES specialist_categories(id)
            )
        """)
        await db.commit()

        # Boshlang'ich kategoriyalarni bir marta yuklash (agar bo'sh bo'lsa)
        async with db.execute("SELECT COUNT(*) FROM problem_categories") as cursor:
            count = (await cursor.fetchone())[0]
        if count == 0:
            from config import CATEGORIES, SPECIALIST_CATEGORIES, CATEGORY_MAP
            for i, cat in enumerate(CATEGORIES):
                await db.execute(
                    "INSERT OR IGNORE INTO problem_categories (name, sort_order) VALUES (?, ?)",
                    (cat, i)
                )
            for i, cat in enumerate(SPECIALIST_CATEGORIES):
                await db.execute(
                    "INSERT OR IGNORE INTO specialist_categories (name, sort_order) VALUES (?, ?)",
                    (cat, i)
                )
            await db.commit()

            # Mapping yaratish
            for prob_cat, spec_cat in CATEGORY_MAP.items():
                if spec_cat is None:
                    continue
                async with db.execute(
                    "SELECT id FROM problem_categories WHERE name = ?", (prob_cat,)
                ) as cursor:
                    p_row = await cursor.fetchone()
                async with db.execute(
                    "SELECT id FROM specialist_categories WHERE name = ?", (spec_cat,)
                ) as cursor:
                    s_row = await cursor.fetchone()
                if p_row and s_row:
                    await db.execute(
                        "INSERT INTO category_mapping (problem_category_id, specialist_category_id) VALUES (?, ?)",
                        (p_row[0], s_row[0])
                    )
            await db.commit()

# Users
async def get_or_create_user(telegram_id: int, fullname: str = None):
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            user = await cursor.fetchone()
        if not user:
            await db.execute(
                "INSERT INTO users (telegram_id, fullname) VALUES (?, ?)",
                (telegram_id, fullname)
            )
            await db.commit()
            async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
                user = await cursor.fetchone()
        return dict(user)

async def update_user_phone(telegram_id: int, phone: str):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute("UPDATE users SET phone = ? WHERE telegram_id = ?", (phone, telegram_id))
        await db.commit()

# Problems
async def save_problem(user_id: int, category: str, problem_text: str):
    async with aiosqlite.connect(DATABASE_URL) as db:
        cursor = await db.execute(
            "INSERT INTO problems (user_id, category, problem_text) VALUES (?, ?, ?)",
            (user_id, category, problem_text)
        )
        await db.commit()
        return cursor.lastrowid

# FIX 1: get_last_problem_id qo'shildi
async def get_last_problem_id():
    async with aiosqlite.connect(DATABASE_URL) as db:
        async with db.execute("SELECT id FROM problems ORDER BY id DESC LIMIT 1") as cursor:
            row = await cursor.fetchone()
        return row[0] if row else 0

async def get_all_problems():
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT p.*, u.fullname, u.phone, u.telegram_id 
            FROM problems p JOIN users u ON p.user_id = u.id
            ORDER BY p.created_at DESC
        """) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def complete_problem(problem_id: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute("UPDATE problems SET status = 'done' WHERE id = ?", (problem_id,))
        await db.commit()

# Specialists
async def save_specialist(fullname: str, category: str, profession: str, phone: str, description: str):
    async with aiosqlite.connect(DATABASE_URL) as db:
        cursor = await db.execute(
            "INSERT INTO specialists (fullname, category, profession, phone, description) VALUES (?, ?, ?, ?, ?)",
            (fullname, category, profession, phone, description)
        )
        await db.commit()
        return cursor.lastrowid

async def get_pending_specialists():
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM specialists WHERE approved = 0 ORDER BY created_at DESC") as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def approve_specialist(specialist_id: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute("UPDATE specialists SET approved = 1 WHERE id = ?", (specialist_id,))
        await db.commit()

async def delete_specialist(specialist_id: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute("DELETE FROM specialists WHERE id = ?", (specialist_id,))
        await db.commit()

async def get_specialists_by_category(category: str):
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM specialists 
            WHERE category = ? AND approved = 1
            ORDER BY recommendation_count DESC LIMIT 20
        """, (category,)) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def get_specialist_by_id(specialist_id: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM specialists WHERE id = ?", (specialist_id,)) as cursor:
            row = await cursor.fetchone()
        return dict(row) if row else None

async def increment_recommendation(specialist_id: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            "UPDATE specialists SET recommendation_count = recommendation_count + 1 WHERE id = ?",
            (specialist_id,)
        )
        await db.commit()

# Contact requests
async def save_contact_request(user_id: int, specialist_id: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        cursor = await db.execute(
            "INSERT INTO contact_requests (user_id, specialist_id) VALUES (?, ?)",
            (user_id, specialist_id)
        )
        await db.commit()
        return cursor.lastrowid

# FIX 4: Duplicate so'rov tekshiruvi
async def check_existing_request(user_id: int, specialist_id: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        async with db.execute("""
            SELECT id FROM contact_requests 
            WHERE user_id = ? AND specialist_id = ? AND status = 'pending'
        """, (user_id, specialist_id)) as cursor:
            row = await cursor.fetchone()
        return row is not None

async def approve_contact_request(request_id: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute("UPDATE contact_requests SET status = 'approved' WHERE id = ?", (request_id,))
        await db.commit()

async def get_contact_request(request_id: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT cr.*, u.telegram_id as user_telegram_id, u.fullname as user_fullname,
                   s.fullname as spec_fullname, s.phone as spec_phone, s.profession, s.category
            FROM contact_requests cr
            JOIN users u ON cr.user_id = u.id
            JOIN specialists s ON cr.specialist_id = s.id
            WHERE cr.id = ?
        """, (request_id,)) as cursor:
            row = await cursor.fetchone()
        return dict(row) if row else None

# FIX 5: Tasdiqlangan mutaxassisni tekshirish
async def is_specialist_approved(specialist_id: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        async with db.execute(
            "SELECT approved FROM specialists WHERE id = ?", (specialist_id,)
        ) as cursor:
            row = await cursor.fetchone()
        return row and row[0] == 1

# ── REYTING ──────────────────────────────────────────────────

async def save_rating(user_id: int, specialist_id: int, stars: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        # Avvalgi bahoni tekshirish
        async with db.execute("""
            SELECT id FROM ratings 
            WHERE user_id = ? AND specialist_id = ?
        """, (user_id, specialist_id)) as cursor:
            existing = await cursor.fetchone()
        
        if existing:
            return False  # Allaqachon baho berilgan
        
        await db.execute(
            "INSERT INTO ratings (user_id, specialist_id, stars) VALUES (?, ?, ?)",
            (user_id, specialist_id, stars)
        )
        # Mutaxassis o'rtacha reytingini yangilash
        await db.execute("""
            UPDATE specialists SET 
                rating_sum = rating_sum + ?,
                rating_count = rating_count + 1,
                recommendation_count = recommendation_count + 1
            WHERE id = ?
        """, (stars, specialist_id))
        await db.commit()
        return True

async def get_specialist_rating(specialist_id: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        async with db.execute("""
            SELECT rating_sum, rating_count FROM specialists WHERE id = ?
        """, (specialist_id,)) as cursor:
            row = await cursor.fetchone()
        if row and row[1] > 0:
            return round(row[0] / row[1], 1)
        return 0.0

async def check_pending_ratings():
    """1 kun o'tgan tasdiqlangan so'rovlarni topadi"""
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT cr.id, cr.user_id, cr.specialist_id,
                   u.telegram_id as user_telegram_id,
                   s.fullname as spec_fullname
            FROM contact_requests cr
            JOIN users u ON cr.user_id = u.id
            JOIN specialists s ON cr.specialist_id = s.id
            LEFT JOIN ratings r ON r.user_id = cr.user_id AND r.specialist_id = cr.specialist_id
            WHERE cr.status = 'approved'
              AND r.id IS NULL
              AND datetime(cr.created_at, '+1 day') <= datetime('now')
        """) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]

# ── KATEGORIYALAR CRUD (Admin uchun) ──────────────────────────

async def get_active_problem_categories():
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM problem_categories WHERE active = 1 ORDER BY sort_order, id"
        ) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def get_active_specialist_categories():
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM specialist_categories WHERE active = 1 ORDER BY sort_order, id"
        ) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def get_all_problem_categories():
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM problem_categories ORDER BY sort_order, id"
        ) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def get_all_specialist_categories():
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM specialist_categories ORDER BY sort_order, id"
        ) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def add_problem_category(name: str):
    async with aiosqlite.connect(DATABASE_URL) as db:
        try:
            cursor = await db.execute(
                "INSERT INTO problem_categories (name) VALUES (?)", (name,)
            )
            await db.commit()
            return cursor.lastrowid
        except Exception:
            return None

async def add_specialist_category(name: str):
    async with aiosqlite.connect(DATABASE_URL) as db:
        try:
            cursor = await db.execute(
                "INSERT INTO specialist_categories (name) VALUES (?)", (name,)
            )
            await db.commit()
            return cursor.lastrowid
        except Exception:
            return None

async def toggle_problem_category(cat_id: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            "UPDATE problem_categories SET active = 1 - active WHERE id = ?", (cat_id,)
        )
        await db.commit()

async def toggle_specialist_category(cat_id: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            "UPDATE specialist_categories SET active = 1 - active WHERE id = ?", (cat_id,)
        )
        await db.commit()

async def delete_problem_category(cat_id: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute("DELETE FROM category_mapping WHERE problem_category_id = ?", (cat_id,))
        await db.execute("DELETE FROM problem_categories WHERE id = ?", (cat_id,))
        await db.commit()

async def delete_specialist_category(cat_id: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute("DELETE FROM category_mapping WHERE specialist_category_id = ?", (cat_id,))
        await db.execute("DELETE FROM specialist_categories WHERE id = ?", (cat_id,))
        await db.commit()

async def get_problem_category_by_id(cat_id: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM problem_categories WHERE id = ?", (cat_id,)
        ) as cursor:
            row = await cursor.fetchone()
        return dict(row) if row else None

async def get_specialist_category_by_id(cat_id: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM specialist_categories WHERE id = ?", (cat_id,)
        ) as cursor:
            row = await cursor.fetchone()
        return dict(row) if row else None

async def get_mapped_specialist_category(problem_category_id: int):
    """Muammo kategoriyasiga mos mutaxassis kategoriyasini topadi"""
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT sc.* FROM category_mapping cm
            JOIN specialist_categories sc ON cm.specialist_category_id = sc.id
            WHERE cm.problem_category_id = ?
            LIMIT 1
        """, (problem_category_id,)) as cursor:
            row = await cursor.fetchone()
        return dict(row) if row else None

async def set_category_mapping(problem_category_id: int, specialist_category_id: int):
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            "DELETE FROM category_mapping WHERE problem_category_id = ?",
            (problem_category_id,)
        )
        await db.execute(
            "INSERT INTO category_mapping (problem_category_id, specialist_category_id) VALUES (?, ?)",
            (problem_category_id, specialist_category_id)
        )
        await db.commit()


# ── MUTAXASSIS CRUD (Admin uchun to'liq boshqarish) ──────────

async def get_all_specialists_full():
    """Barcha mutaxassislar (tasdiqlangan + tasdiqlanmagan)"""
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM specialists ORDER BY created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def get_approved_specialists_paginated(offset: int = 0, limit: int = 10):
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM specialists WHERE approved = 1 
            ORDER BY created_at DESC LIMIT ? OFFSET ?
        """, (limit, offset)) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def count_approved_specialists():
    async with aiosqlite.connect(DATABASE_URL) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM specialists WHERE approved = 1"
        ) as cursor:
            row = await cursor.fetchone()
        return row[0] if row else 0

async def revoke_specialist(specialist_id: int):
    """Tasdiqlangan mutaxassisni bekor qilish (approved = 0)"""
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            "UPDATE specialists SET approved = 0 WHERE id = ?", (specialist_id,)
        )
        await db.commit()

async def update_specialist_field(specialist_id: int, field: str, value):
    allowed_fields = {"fullname", "profession", "phone", "description", "category"}
    if field not in allowed_fields:
        return False
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            f"UPDATE specialists SET {field} = ? WHERE id = ?", (value, specialist_id)
        )
        await db.commit()
        return True


# ── STATISTIKA ─────────────────────────────────────────────

async def get_stats():
    async with aiosqlite.connect(DATABASE_URL) as db:
        stats = {}
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            stats['users'] = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM problems") as c:
            stats['problems'] = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM problems WHERE status = 'new'") as c:
            stats['problems_new'] = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM specialists WHERE approved = 1") as c:
            stats['specialists_approved'] = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM specialists WHERE approved = 0") as c:
            stats['specialists_pending'] = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM contact_requests") as c:
            stats['contact_requests'] = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM contact_requests WHERE status = 'approved'") as c:
            stats['contact_approved'] = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM ratings") as c:
            stats['ratings'] = (await c.fetchone())[0]
        return stats

# ── BROADCAST ──────────────────────────────────────────────

async def get_all_user_telegram_ids():
    async with aiosqlite.connect(DATABASE_URL) as db:
        async with db.execute("SELECT telegram_id FROM users") as cursor:
            rows = await cursor.fetchall()
        return [r[0] for r in rows]
