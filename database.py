
import aiosqlite
from typing import Optional, List, Dict, Any
from datetime import datetime

CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    role TEXT CHECK(role IN ('MANAGER', 'EMPLOYEE')) NOT NULL DEFAULT 'EMPLOYEE',
    language TEXT DEFAULT 'uz',
    active INTEGER DEFAULT 1
);
"""

CREATE_TASKS = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    created_by INTEGER NOT NULL,
    assigned_to INTEGER NOT NULL,
    deadline TEXT,
    status TEXT CHECK(status IN ('open','done')) NOT NULL DEFAULT 'open',
    priority TEXT DEFAULT 'Medium',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

CREATE_REPORTS = """
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    content TEXT,
    tasks_completed INTEGER DEFAULT 0
);
"""

CREATE_INVITES = """
CREATE TABLE IF NOT EXISTS invites (
    code TEXT PRIMARY KEY,
    username TEXT,
    created_by INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    used_by INTEGER,
    used_at TEXT
);
"""

class Database:
    def __init__(self, path: str):
        self.path = path
        self._db: Optional[aiosqlite.Connection] = None

    async def connect(self):
        if not self._db:
            self._db = await aiosqlite.connect(self.path)
            await self._db.execute("PRAGMA journal_mode=WAL;")
            await self._db.execute("PRAGMA foreign_keys=ON;")
            await self._db.executescript(CREATE_USERS + CREATE_TASKS + CREATE_REPORTS + CREATE_INVITES)
            await self._db.commit()

    async def close(self):
        if self._db:
            await self._db.close()
            self._db = None

    async def upsert_user(self, telegram_id: int, username: Optional[str], full_name: str) -> None:
        await self.connect()
        await self._db.execute(
            """
            INSERT INTO users (telegram_id, username, full_name)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username=excluded.username,
                full_name=excluded.full_name
            """,
            (telegram_id, username, full_name),
        )
        await self._db.commit()

    async def set_user_language(self, telegram_id: int, language: str) -> None:
        await self.connect()
        await self._db.execute("UPDATE users SET language=? WHERE telegram_id=?", (language, telegram_id))
        await self._db.commit()

    async def set_user_role(self, telegram_id: int, role: str) -> None:
        await self.connect()
        await self._db.execute("UPDATE users SET role=? WHERE telegram_id=?", (role, telegram_id))
        await self._db.commit()

    async def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        await self.connect()
        cur = await self._db.execute("SELECT telegram_id, username, full_name, role, language, COALESCE(active,1) FROM users WHERE telegram_id=?", (telegram_id,))
        row = await cur.fetchone()
        if not row:
            return None
        return {
            "telegram_id": row[0],
            "username": row[1],
            "full_name": row[2],
            "role": row[3],
            "language": row[4],
            "active": row[5],
        }

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        await self.connect()
        cur = await self._db.execute("SELECT telegram_id, username, full_name, role, language, COALESCE(active,1) FROM users WHERE lower(username)=?", (username.lower(),))
        row = await cur.fetchone()
        if not row:
            return None
        return {
            "telegram_id": row[0],
            "username": row[1],
            "full_name": row[2],
            "role": row[3],
            "language": row[4],
            "active": row[5],
        }

    async def get_all_employees(self) -> List[Dict[str, Any]]:
        await self.connect()
        cur = await self._db.execute("SELECT telegram_id, username, full_name, role, language FROM users WHERE role='EMPLOYEE' AND (active IS NULL OR active=1) ORDER BY username")
        rows = await cur.fetchall()
        return [
            {"telegram_id": r[0], "username": r[1], "full_name": r[2], "role": r[3], "language": r[4]}
            for r in rows
        ]

    async def add_task(self, title: str, description: str, created_by: int, assigned_to: int, deadline: Optional[str], priority: str) -> int:
        await self.connect()
        now = datetime.utcnow().isoformat()
        cur = await self._db.execute(
            """
            INSERT INTO tasks (title, description, created_by, assigned_to, deadline, status, priority, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'open', ?, ?, ?)
            """,
            (title, description, created_by, assigned_to, deadline, priority, now, now),
        )
        await self._db.commit()
        return cur.lastrowid

    async def list_tasks_for_user(self, telegram_id: int) -> List[Dict[str, Any]]:
        await self.connect()
        cur = await self._db.execute(
            "SELECT id, title, description, created_by, assigned_to, deadline, status, priority, created_at, updated_at FROM tasks WHERE assigned_to=? ORDER BY status DESC, deadline ASC",
            (telegram_id,),
        )
        rows = await cur.fetchall()
        return [
            {
                "id": r[0], "title": r[1], "description": r[2], "created_by": r[3],
                "assigned_to": r[4], "deadline": r[5], "status": r[6], "priority": r[7],
                "created_at": r[8], "updated_at": r[9],
            }
            for r in rows
        ]

    async def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        await self.connect()
        cur = await self._db.execute(
            "SELECT id, title, description, created_by, assigned_to, deadline, status, priority, created_at, updated_at FROM tasks WHERE id=?",
            (task_id,),
        )
        r = await cur.fetchone()
        if not r:
            return None
        return {
            "id": r[0], "title": r[1], "description": r[2], "created_by": r[3],
            "assigned_to": r[4], "deadline": r[5], "status": r[6], "priority": r[7],
            "created_at": r[8], "updated_at": r[9],
        }

    async def mark_task_done(self, task_id: int) -> bool:
        await self.connect()
        now = datetime.utcnow().isoformat()
        cur = await self._db.execute("UPDATE tasks SET status='done', updated_at=? WHERE id=?", (now, task_id))
        await self._db.commit()
        return cur.rowcount > 0

    async def employee_status_counters(self) -> List[Dict[str, Any]]:
        await self.connect()
        cur = await self._db.execute("""
            SELECT u.username,
                   COUNT(t.id) as total,
                   SUM(CASE WHEN t.status='done' THEN 1 ELSE 0 END) as done,
                   SUM(CASE WHEN t.status='open' THEN 1 ELSE 0 END) as open
            FROM users u
            LEFT JOIN tasks t ON u.telegram_id = t.assigned_to
            WHERE u.role='EMPLOYEE' AND (u.active IS NULL OR u.active=1)
            GROUP BY u.username
            ORDER BY u.username
        """)
        rows = await cur.fetchall()
        return [{"username": r[0] or "-", "total": r[1] or 0, "done": r[2] or 0, "open": r[3] or 0} for r in rows]

    async def add_report(self, user_id: int, date_iso: str, content: str, tasks_completed: int) -> int:
        await self.connect()
        cur = await self._db.execute(
            "INSERT INTO reports (user_id, date, content, tasks_completed) VALUES (?, ?, ?, ?)",
            (user_id, date_iso, content, tasks_completed),
        )
        await self._db.commit()
        return cur.lastrowid

    async def aggregate_day(self, date_prefix: str) -> List[Dict[str, Any]]:
        await self.connect()
        cur = await self._db.execute("""
            SELECT u.username,
                   SUM(CASE WHEN substr(t.updated_at,1,10)=? AND t.status='done' THEN 1 ELSE 0 END) as done_today,
                   SUM(CASE WHEN t.status='open' THEN 1 ELSE 0 END) as open_now
            FROM users u
            LEFT JOIN tasks t ON u.telegram_id = t.assigned_to
            WHERE u.role='EMPLOYEE' AND (u.active IS NULL OR u.active=1)
            GROUP BY u.username
            ORDER BY u.username
        """, (date_prefix,))
        rows = await cur.fetchall()
        return [{"username": r[0] or "-", "done": r[1] or 0, "open": r[2] or 0} for r in rows]

    async def deactivate_user(self, telegram_id: int) -> bool:
        await self.connect()
        cur = await self._db.execute("UPDATE users SET active=0 WHERE telegram_id=?", (telegram_id,))
        await self._db.commit()
        return cur.rowcount > 0

    async def create_invite(self, code: str, username: str, created_by: int, created_at: str) -> None:
        await self.connect()
        await self._db.execute(
            "INSERT OR REPLACE INTO invites (code, username, created_by, created_at) VALUES (?,?,?,?)",
            (code, username.lower() if username else None, created_by, created_at),
        )
        await self._db.commit()

    async def get_invite(self, code: str) -> Optional[Dict[str, Any]]:
        await self.connect()
        cur = await self._db.execute("SELECT code, username, created_by, created_at, used_by, used_at FROM invites WHERE code=?", (code,))
        r = await cur.fetchone()
        if not r: return None
        return {"code": r[0], "username": r[1], "created_by": r[2], "created_at": r[3], "used_by": r[4], "used_at": r[5]}

    async def mark_invite_used(self, code: str, used_by: int, used_at: str) -> None:
        await self.connect()
        await self._db.execute("UPDATE invites SET used_by=?, used_at=? WHERE code=?", (used_by, used_at, code))
        await self._db.commit()
