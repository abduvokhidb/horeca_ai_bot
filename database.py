# database.py
import sqlite3
from contextlib import contextmanager
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import secrets

from config import Config

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
            c = con.cursor()
            c.execute("""
            CREATE TABLE IF NOT EXISTS users(
                telegram_id INTEGER PRIMARY KEY,
                username    TEXT,
                full_name   TEXT,
                phone       TEXT,
                position    TEXT,
                role        TEXT,                 -- MANAGER|EMPLOYEE|NULL
                language    TEXT DEFAULT 'uz',
                active      INTEGER DEFAULT 1
            )""")

            c.execute("""
            CREATE TABLE IF NOT EXISTS tasks(
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                title        TEXT,
                description  TEXT,
                created_by   INTEGER,
                assigned_to  INTEGER,
                deadline     TEXT,               -- ISO str
                status       TEXT DEFAULT 'new',  -- new|accepted|rejected|done|archived
                priority     TEXT DEFAULT 'Medium',
                created_at   TEXT DEFAULT (datetime('now')),
                accepted_at  TEXT,
                completed_at TEXT,
                report_text  TEXT,
                reject_reason TEXT
            )""")

            c.execute("""
            CREATE TABLE IF NOT EXISTS task_files(
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id   INTEGER,
                file_id   TEXT,      -- telegram file_id
                file_type TEXT,      -- photo|document|audio|video|voice|...
                file_name TEXT,
                caption   TEXT,
                added_by  INTEGER,
                added_at  TEXT DEFAULT (datetime('now'))
            )""")

            c.execute("""
            CREATE TABLE IF NOT EXISTS reports(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT,
                content TEXT,
                tasks_completed INTEGER
            )""")

            c.execute("""
            CREATE TABLE IF NOT EXISTS invite_requests(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER,
                username  TEXT,
                full_name TEXT,
                status    TEXT DEFAULT 'pending',  -- pending|approved|rejected
                reason    TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                decided_at TEXT
            )""")

            c.execute("""
            CREATE TABLE IF NOT EXISTS invites(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username   TEXT,
                full_name  TEXT,
                token      TEXT UNIQUE,
                status     TEXT DEFAULT 'active',  -- active|used|revoked
                created_at TEXT DEFAULT (datetime('now')),
                approved_by INTEGER,
                approved_at TEXT,
                used_by     INTEGER,
                used_at     TEXT
            )""")

            # Indexes
            c.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(lower(username))")
            c.execute("CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_invreq_status ON invite_requests(status)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_invites_token ON invites(token)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_task_files_task ON task_files(task_id)")

    # Users
    def upsert_user(self, telegram_id: int, username: Optional[str], full_name: str) -> Dict[str, Any]:
        with self._conn() as con:
            c = con.cursor()
            c.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
            row = c.fetchone()
            if row:
                c.execute("UPDATE users SET username=?, full_name=? WHERE telegram_id=?", (username, full_name, telegram_id))
            else:
                c.execute("INSERT INTO users(telegram_id, username, full_name) VALUES(?,?,?)", (telegram_id, username, full_name))
            c.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
            return c.fetchone()

    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        with self._conn() as con:
            return con.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        if not username: return None
        with self._conn() as con:
            return con.execute("SELECT * FROM users WHERE lower(username)=lower(?)", (username,)).fetchone()

    def list_all_users(self) -> List[Dict[str,Any]]:
        with self._conn() as con:
            return con.execute("SELECT * FROM users").fetchall() or []

    def set_user_role(self, telegram_id: int, role: Optional[str]) -> None:
        with self._conn() as con:
            con.execute("UPDATE users SET role=? WHERE telegram_id=?", (role, telegram_id,))

    def get_user_role(self, telegram_id: int) -> Optional[str]:
        with self._conn() as con:
            r = con.execute("SELECT role FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()
            return r["role"] if r else None

    def set_user_language(self, telegram_id: int, lang: str) -> None:
        with self._conn() as con:
            con.execute("UPDATE users SET language=? WHERE telegram_id=?", (lang, telegram_id,))

    def update_profile(self, telegram_id: int, full_name: Optional[str]=None, phone: Optional[str]=None) -> None:
        with self._conn() as con:
            if full_name is not None:
                con.execute("UPDATE users SET full_name=? WHERE telegram_id=?", (full_name, telegram_id))
            if phone is not None:
                con.execute("UPDATE users SET phone=? WHERE telegram_id=?", (phone, telegram_id))

    def set_user_active(self, telegram_id: int, active: bool) -> None:
        with self._conn() as con:
            con.execute("UPDATE users SET active=? WHERE telegram_id=?", (1 if active else 0, telegram_id,))

    def is_user_active(self, telegram_id: int) -> bool:
        with self._conn() as con:
            r = con.execute("SELECT COALESCE(active,1) AS a FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()
            return bool(r["a"]) if r else True

    def list_employees(self) -> List[Dict[str, Any]]:
        with self._conn() as con:
            return con.execute("""
                SELECT * FROM users
                WHERE role='EMPLOYEE' AND COALESCE(active,1)=1
                ORDER BY username IS NULL, lower(username)
            """).fetchall() or []

    def list_managers(self) -> List[Dict[str, Any]]:
        with self._conn() as con:
            return con.execute("SELECT * FROM users WHERE role='MANAGER'").fetchall() or []

    def remove_employee_by_username(self, username: str) -> bool:
        with self._conn() as con:
            r = con.execute("SELECT telegram_id FROM users WHERE lower(username)=lower(?) AND role='EMPLOYEE'", (username,)).fetchone()
            if not r: return False
            con.execute("UPDATE users SET role=NULL WHERE lower(username)=lower(?)", (username,))
            return True

    def resolve_assignee(self, name_or_username: str) -> Optional[Dict[str, Any]]:
        key = (name_or_username or "").strip()
        if not key: return None
        with self._conn() as con:
            if key.startswith("@"):
                return con.execute("SELECT * FROM users WHERE lower(username)=lower(?)", (key.lstrip("@"),)).fetchone()
            r = con.execute("SELECT * FROM users WHERE lower(full_name)=lower(?)", (key,)).fetchone()
            if r: return r
            return con.execute("SELECT * FROM users WHERE lower(full_name) LIKE lower(?) ORDER BY length(full_name) ASC LIMIT 1",
                               (f"%{key}%",)).fetchone()

    # Tasks
    def create_task(self, title: str, description: str, created_by: int, assigned_to_username: Optional[str],
                    deadline: Optional[str], priority: str) -> int:
        assigned_to_id = None
        with self._conn() as con:
            if assigned_to_username:
                r = con.execute("SELECT telegram_id FROM users WHERE lower(username)=lower(?)", (assigned_to_username,)).fetchone()
                if r: assigned_to_id = r["telegram_id"]
            cur = con.execute("""
                INSERT INTO tasks(title, description, created_by, assigned_to, deadline, status, priority)
                VALUES(?,?,?,?,?,?,?)
            """, (title, description, created_by, assigned_to_id, deadline or None, "new", priority))
            return cur.lastrowid

    def get_task(self, task_id: int) -> Optional[Dict[str,Any]]:
        with self._conn() as con:
            return con.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()

    def list_tasks_for_user(self, telegram_id: int) -> List[Dict[str,Any]]:
        with self._conn() as con:
            return con.execute("""
                SELECT * FROM tasks
                WHERE assigned_to=?
                ORDER BY CASE WHEN status='done' THEN 1 ELSE 0 END, created_at DESC
            """, (telegram_id,)).fetchall() or []

    def set_task_status(self, task_id: int, status: str, by: int, reason: Optional[str]=None) -> bool:
        with self._conn() as con:
            if status == "accepted":
                r = con.execute("UPDATE tasks SET status='accepted', accepted_at=datetime('now') WHERE id=? AND assigned_to=?",
                                (task_id, by))
            elif status == "rejected":
                r = con.execute("UPDATE tasks SET status='rejected', reject_reason=?, completed_at=NULL WHERE id=? AND assigned_to=?",
                                (reason or "", task_id, by))
            elif status == "done":
                r = con.execute("UPDATE tasks SET status='done', completed_at=datetime('now') WHERE id=? AND assigned_to=?",
                                (task_id, by))
            else:
                return False
            return r.rowcount > 0

    def mark_task_done_with_report(self, task_id: int, by: int, report: str) -> bool:
        if int(task_id) == 0:
            self.save_report(by, report, self.count_completed_today(by))
            return True
        with self._conn() as con:
            r = con.execute("""
                UPDATE tasks
                SET status='done', completed_at=datetime('now'), report_text=?
                WHERE id=? AND assigned_to=?
            """, (report or "", task_id, by))
            return r.rowcount > 0

    # Task files
    def add_task_file(self, task_id: int, file_id: str, file_type: str, file_name: Optional[str], caption: Optional[str], added_by: int):
        with self._conn() as con:
            con.execute("""
                INSERT INTO task_files(task_id, file_id, file_type, file_name, caption, added_by)
                VALUES(?,?,?,?,?,?)
            """, (task_id, file_id, file_type, file_name, caption, added_by))

    def list_task_files(self, task_id: int) -> List[Dict[str,Any]]:
        with self._conn() as con:
            return con.execute("SELECT * FROM task_files WHERE task_id=? ORDER BY id ASC", (task_id,)).fetchall() or []

    # Reports / dashboard
    def count_completed_today(self, telegram_id: int) -> int:
        with self._conn() as con:
            r = con.execute("""
                SELECT COUNT(*) AS c FROM tasks
                WHERE assigned_to=? AND status='done' AND date(completed_at)=date('now','localtime')
            """, (telegram_id,)).fetchone()
            return int(r["c"]) if r else 0

    def save_report(self, user_id: int, content: str, tasks_completed: int) -> None:
        with self._conn() as con:
            con.execute("INSERT INTO reports(user_id, date, content, tasks_completed) VALUES(?, date('now','localtime'), ?, ?)",
                        (user_id, content, tasks_completed))

    def build_daily_summary(self) -> List[Dict[str,Any]]:
        with self._conn() as con:
            return con.execute("""
                SELECT u.username,
                       SUM(CASE WHEN t.status='done' AND date(t.completed_at)=date('now','localtime') THEN 1 ELSE 0 END) AS completed,
                       COUNT(t.id) AS total
                FROM users u
                LEFT JOIN tasks t ON t.assigned_to=u.telegram_id
                WHERE u.role='EMPLOYEE' AND COALESCE(u.active,1)=1
                GROUP BY u.telegram_id
                ORDER BY lower(u.username)
            """).fetchall() or []

    def get_status_overview(self) -> List[Dict[str,Any]]:
        with self._conn() as con:
            emps = con.execute("SELECT * FROM users WHERE role='EMPLOYEE' AND COALESCE(active,1)=1 ORDER BY lower(username)").fetchall() or []
            out = []
            for e in emps:
                tasks = con.execute("""
                    SELECT * FROM tasks
                    WHERE assigned_to=? AND status!='archived'
                    ORDER BY CASE WHEN status='done' THEN 1 ELSE 0 END, created_at DESC
                """, (e["telegram_id"],)).fetchall() or []
                out.append({"employee": e, "tasks": tasks})
            return out

    # Invites
    def create_invite_request(self, user_id: int, username: Optional[str], full_name: Optional[str]) -> int:
        with self._conn() as con:
            r = con.execute("SELECT id FROM invite_requests WHERE user_id=? AND status='pending' ORDER BY id DESC LIMIT 1",
                            (user_id,)).fetchone()
            if r: return int(r["id"])
            cur = con.execute("INSERT INTO invite_requests(user_id, username, full_name) VALUES(?,?,?)",
                              (user_id, username, full_name))
            return cur.lastrowid

    def list_invite_requests(self) -> List[Dict[str,Any]]:
        with self._conn() as con:
            return con.execute("SELECT * FROM invite_requests WHERE status='pending' ORDER BY created_at ASC").fetchall() or []

    def _gen_token(self) -> str:
        return secrets.token_urlsafe(12)

    def approve_invite_request(self, req_id: int) -> str:
        with self._conn() as con:
            req = con.execute("SELECT * FROM invite_requests WHERE id=?", (req_id,)).fetchone()
            if not req: raise ValueError("Invite request topilmadi")
            token = self._gen_token()
            con.execute("""
                INSERT INTO invites(username, full_name, token, status, approved_by, approved_at)
                VALUES(?,?,?,?,?,datetime('now'))
            """, (req.get("username"), req.get("full_name"), token, "active", req.get("user_id")))
            con.execute("UPDATE invite_requests SET status='approved', decided_at=datetime('now') WHERE id=?", (req_id,))
            bot_name = Config.BOT_USERNAME or "<BOT_USERNAME>"
            return f"https://t.me/{bot_name}?start={token}"

    def reject_invite_request(self, req_id: int, reason: Optional[str]=None) -> None:
        with self._conn() as con:
            con.execute("UPDATE invite_requests SET status='rejected', reason=?, decided_at=datetime('now') WHERE id=?",
                        (reason or "", req_id))

    def create_invite_for(self, username: str, full_name: Optional[str]) -> Tuple[bool,str]:
        if not username: return False, ""
        with self._conn() as con:
            token = self._gen_token()
            con.execute("""
                INSERT INTO invites(username, full_name, token, status, approved_at)
                VALUES(?,?,?, 'active', datetime('now'))
            """, (username, full_name or None, token))
            bot_name = Config.BOT_USERNAME or "<BOT_USERNAME>"
            return True, f"https://t.me/{bot_name}?start={token}"

    def consume_invite_token(self, token: str, user_id: int, username: Optional[str], full_name: Optional[str]) -> bool:
        with self._conn() as con:
            inv = con.execute("SELECT * FROM invites WHERE token=? AND status='active'", (token,)).fetchone()
            if not inv: return False
            con.execute("""
                UPDATE users SET username=COALESCE(?,username), full_name=COALESCE(?,full_name),
                                 role=COALESCE(role,'EMPLOYEE'), active=1
                WHERE telegram_id=?
            """, (username, full_name, user_id))
            con.execute("UPDATE invites SET status='used', used_by=?, used_at=datetime('now') WHERE id=?",
                        (user_id, inv["id"]))
            return True
