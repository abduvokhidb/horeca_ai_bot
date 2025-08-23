# database.py
# SQLite uchun sodda wrapper. Python 3.11+, sqlite3.
# Jadval sxemasi:
# users(telegram_id PK, username, full_name, role, language)
# tasks(id PK, title, description, created_by, assigned_to, deadline, status, priority, created_at, completed_at)
# reports(id PK, user_id, date, content, tasks_completed)

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, Any, List, Optional

def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

class Database:
    def __init__(self, path: str):
        self.path = path
        self._init_db()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = dict_factory
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        with self._conn() as con:
            cur = con.cursor()
            # users
            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                role TEXT,
                language TEXT DEFAULT 'uz'
            )
            """)
            # tasks
            cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                created_by INTEGER,
                assigned_to INTEGER,
                deadline TEXT,
                status TEXT DEFAULT 'new',
                priority TEXT DEFAULT 'Medium',
                created_at TEXT DEFAULT (datetime('now')),
                completed_at TEXT
            )
            """)
            # reports
            cur.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT,
                content TEXT,
                tasks_completed INTEGER
            )
            """)

    # ---------------- Users ----------------
    def upsert_user(self, telegram_id: int, username: Optional[str], full_name: str) -> Dict[str, Any]:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            row = cur.fetchone()
            if row:
                cur.execute("UPDATE users SET username=?, full_name=? WHERE telegram_id=?",
                            (username, full_name, telegram_id))
            else:
                cur.execute("INSERT INTO users(telegram_id, username, full_name) VALUES(?,?,?)",
                            (telegram_id, username, full_name))
            cur.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            return cur.fetchone()

    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
            return cur.fetchone()

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        if not username:
            return None
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE lower(username)=lower(?)", (username,))
            return cur.fetchone()

    def set_user_role(self, telegram_id: int, role: str) -> None:
        with self._conn() as con:
            con.execute("UPDATE users SET role=? WHERE telegram_id=?", (role, telegram_id,))

    def get_user_role(self, telegram_id: int) -> Optional[str]:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT role FROM users WHERE telegram_id=?", (telegram_id,))
            r = cur.fetchone()
            return r["role"] if r else None

    def set_user_language(self, telegram_id: int, lang: str) -> None:
        with self._conn() as con:
            con.execute("UPDATE users SET language=? WHERE telegram_id=?", (lang, telegram_id,))

    def list_employees(self) -> List[Dict[str, Any]]:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE role='EMPLOYEE' ORDER BY username IS NULL, lower(username)")
            return cur.fetchall() or []

    def add_employee_by_username(self, username: str):
        """Foydalanuvchi username bo‘yicha allaqachon botga /start qilgan bo‘lsa → role=EMPLOYEE qiladi.
           Aks holda False qaytaradi va t.me linkini beradi."""
        link = f"https://t.me/{username}" if username else ""
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE lower(username)=lower(?)", (username,))
            row = cur.fetchone()
            if not row:
                # Hali botga yozmagan. Invitelink sifatida t.me/username qaytaramiz.
                return False, link
            # mavjud foydalanuvchini hodimga aylantiramiz
            cur.execute("UPDATE users SET role='EMPLOYEE' WHERE lower(username)=lower(?)", (username,))
            return True, link

    def remove_employee_by_username(self, username: str) -> bool:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT telegram_id FROM users WHERE lower(username)=lower(?) AND role='EMPLOYEE'", (username,))
            row = cur.fetchone()
            if not row:
                return False
            # roldan olib tashlaymiz (tarix saqlansin)
            cur.execute("UPDATE users SET role=NULL WHERE lower(username)=lower(?)", (username,))
            return True

    def list_managers(self) -> List[Dict[str, Any]]:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE role='MANAGER'")
            return cur.fetchall() or []

    # ---------------- Tasks ----------------
    def create_task(self, title: str, description: str, created_by: int,
                    assigned_to_username: Optional[str], deadline: Optional[str], priority: str) -> int:
        assigned_to_id = None
        with self._conn() as con:
            cur = con.cursor()
            if assigned_to_username:
                cur.execute("SELECT telegram_id FROM users WHERE lower(username)=lower(?)", (assigned_to_username,))
                row = cur.fetchone()
                if row:
                    assigned_to_id = row["telegram_id"]
            cur.execute("""
                INSERT INTO tasks(title, description, created_by, assigned_to, deadline, status, priority)
                VALUES(?,?,?,?,?,?,?)
            """, (title, description, created_by, assigned_to_id, deadline or None, "new", priority))
            return cur.lastrowid

    def list_tasks_for_user(self, telegram_id: int) -> List[Dict[str, Any]]:
        with self._conn() as con:
            cur = con.cursor()
            # Avval ochiq, keyin bajarilganlar
            cur.execute("""
                SELECT * FROM tasks
                WHERE assigned_to=?
                ORDER BY CASE WHEN status='done' THEN 1 ELSE 0 END, created_at DESC
            """, (telegram_id,))
            return cur.fetchall() or []

    def mark_task_done(self, task_id: int, telegram_id: int) -> bool:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("""
                UPDATE tasks
                SET status='done', completed_at=datetime('now')
                WHERE id=? AND assigned_to=?
            """, (task_id, telegram_id))
            return cur.rowcount > 0

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
            return cur.fetchone()

    # ---------------- Reports ----------------
    def count_completed_today(self, telegram_id: int) -> int:
        with self._conn() as con:
            cur = con.cursor()
            # localtime yetarli; agar TZ sezgir bo‘lsin desangiz, App layerda boshqariladi
            cur.execute("""
                SELECT COUNT(*) AS c FROM tasks
                WHERE assigned_to=? AND status='done' AND date(completed_at)=date('now','localtime')
            """, (telegram_id,))
            r = cur.fetchone()
            return int(r["c"]) if r else 0

    def save_report(self, user_id: int, content: str, tasks_completed: int) -> None:
        with self._conn() as con:
            con.execute("""
                INSERT INTO reports(user_id, date, content, tasks_completed)
                VALUES(?, date('now','localtime'), ?, ?)
            """, (user_id, content, tasks_completed))

    def build_daily_summary(self) -> List[Dict[str, Any]]:
        with self._conn() as con:
            cur = con.cursor()
            # har user uchun bugungi done/total
            cur.execute("""
                SELECT u.username,
                       SUM(CASE WHEN t.status='done' AND date(t.completed_at)=date('now','localtime') THEN 1 ELSE 0 END) AS completed,
                       COUNT(t.id) AS total
                FROM users u
                LEFT JOIN tasks t ON t.assigned_to = u.telegram_id
                WHERE u.role='EMPLOYEE'
                GROUP BY u.telegram_id
                ORDER BY lower(u.username)
            """)
            return cur.fetchall() or []

    def get_status_overview(self) -> List[Dict[str, Any]]:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE role='EMPLOYEE' ORDER BY lower(username)")
            emps = cur.fetchall() or []
            out = []
            for e in emps:
                cur.execute("""
                    SELECT * FROM tasks
                    WHERE assigned_to=? AND status!='archived'
                    ORDER BY CASE WHEN status='done' THEN 1 ELSE 0 END, created_at DESC
                """, (e["telegram_id"],))
                tasks = cur.fetchall() or []
                out.append({"employee": e, "tasks": tasks})
            return out
