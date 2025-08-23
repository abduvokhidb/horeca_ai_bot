# database.py
# SQLite uchun kengaytirilgan wrapper.
# Python 3.11+, sqlite3
# Jadval sxemasi:
# users(telegram_id PK, username, full_name, role, language)
# invite_requests(id PK, username, full_name, status, requested_at, decided_at, decided_by)
# tasks(id PK, title, description, created_by, assigned_to, deadline, status, priority, reason, created_at, completed_at)
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
            # --- users ---
            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                full_name TEXT,
                role TEXT,
                language TEXT DEFAULT 'uz'
            )
            """)
            # --- invite requests ---
            cur.execute("""
            CREATE TABLE IF NOT EXISTS invite_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                full_name TEXT,
                status TEXT DEFAULT 'pending', -- pending/accepted/rejected
                requested_at TEXT DEFAULT (datetime('now')),
                decided_at TEXT,
                decided_by INTEGER
            )
            """)
            # --- tasks ---
            cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                created_by INTEGER,
                assigned_to INTEGER,
                deadline TEXT,
                status TEXT DEFAULT 'new',  -- new/accepted/rejected/done
                priority TEXT DEFAULT 'Medium',
                reason TEXT,  -- agar rejected bo‘lsa, sababi
                created_at TEXT DEFAULT (datetime('now')),
                completed_at TEXT
            )
            """)
            # --- reports ---
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
            cur.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
            row = cur.fetchone()
            if row:
                cur.execute("UPDATE users SET username=?, full_name=? WHERE telegram_id=?",
                            (username, full_name, telegram_id))
            else:
                cur.execute("INSERT INTO users(telegram_id, username, full_name) VALUES(?,?,?)",
                            (telegram_id, username, full_name))
            cur.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
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
            cur.execute("SELECT * FROM users WHERE role='EMPLOYEE' ORDER BY lower(username)")
            return cur.fetchall() or []

    def list_managers(self) -> List[Dict[str, Any]]:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE role='MANAGER'")
            return cur.fetchall() or []

    # ---------------- Invite Requests ----------------
    def add_invite_request(self, username: str, full_name: str) -> int:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("""
                INSERT INTO invite_requests(username, full_name, status)
                VALUES(?,?, 'pending')
            """, (username, full_name))
            return cur.lastrowid

    def list_pending_invites(self) -> List[Dict[str, Any]]:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM invite_requests WHERE status='pending' ORDER BY requested_at ASC")
            return cur.fetchall() or []

    def decide_invite(self, invite_id: int, status: str, decided_by: int) -> bool:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("""
                UPDATE invite_requests
                SET status=?, decided_at=datetime('now'), decided_by=?
                WHERE id=? AND status='pending'
            """, (status, decided_by, invite_id))
            return cur.rowcount > 0

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
            cur.execute("""
                SELECT * FROM tasks
                WHERE assigned_to=?
                ORDER BY created_at DESC
            """, (telegram_id,))
            return cur.fetchall() or []

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
            return cur.fetchone()

    def accept_task(self, task_id: int, telegram_id: int) -> bool:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("""
                UPDATE tasks SET status='accepted'
                WHERE id=? AND assigned_to=? AND status='new'
            """, (task_id, telegram_id))
            return cur.rowcount > 0

    def reject_task(self, task_id: int, telegram_id: int, reason: str) -> bool:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("""
                UPDATE tasks SET status='rejected', reason=?
                WHERE id=? AND assigned_to=? AND status IN ('new','accepted')
            """, (reason, task_id, telegram_id))
            return cur.rowcount > 0

    def mark_task_done(self, task_id: int, telegram_id: int) -> bool:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("""
                UPDATE tasks
                SET status='done', completed_at=datetime('now')
                WHERE id=? AND assigned_to=?
            """, (task_id, telegram_id))
            return cur.rowcount > 0

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
                    ORDER BY created_at DESC
                """, (e["telegram_id"],))
                tasks = cur.fetchall() or []
                out.append({"employee": e, "tasks": tasks})
            return out

    # ---------------- Reports ----------------
    def count_completed_today(self, telegram_id: int) -> int:
        with self._conn() as con:
            cur = con.cursor()
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
