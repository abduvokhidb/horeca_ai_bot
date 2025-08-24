# database.py
# SQLite wrapper — PTB v21 bot.py bilan mos.
# Jadvalar:
# users(telegram_id PK, username, full_name, role, language, active)
# tasks(id PK, title, description, created_by, assigned_to, deadline, status, priority, created_at, completed_at,
#       report_text, reject_reason, accepted_at)
# reports(id PK, user_id, date, content, tasks_completed)
# invite_requests(id PK, user_id, username, full_name, status, reason, created_at, decided_at)
# invites(id PK, username, full_name, token UNIQUE, status, created_at, approved_by, approved_at, used_by, used_at)

import os
import sqlite3
import secrets
from contextlib import contextmanager
from typing import Dict, Any, List, Optional, Tuple

try:
    # deep-link yaratish uchun bot username
    from config import Config
    BOT_USERNAME = getattr(Config, "BOT_USERNAME", "")
except Exception:
    BOT_USERNAME = ""

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

    # ---------------- Schema ----------------
    def _init_db(self):
        with self._conn() as con:
            cur = con.cursor()

            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username    TEXT,
                full_name   TEXT,
                role        TEXT,
                language    TEXT DEFAULT 'uz',
                active      INTEGER DEFAULT 1
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                title         TEXT,
                description   TEXT,
                created_by    INTEGER,
                assigned_to   INTEGER,
                deadline      TEXT,
                status        TEXT DEFAULT 'new',              -- new|accepted|rejected|done|archived
                priority      TEXT DEFAULT 'Medium',
                created_at    TEXT DEFAULT (datetime('now')),
                completed_at  TEXT,
                report_text   TEXT,
                reject_reason TEXT,
                accepted_at   TEXT
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT,
                content TEXT,
                tasks_completed INTEGER
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS invite_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER,
                username   TEXT,
                full_name  TEXT,
                status     TEXT DEFAULT 'pending',            -- pending|approved|rejected
                reason     TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                decided_at TEXT
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS invites (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT,
                full_name   TEXT,
                token       TEXT UNIQUE,
                status      TEXT DEFAULT 'active',            -- active|used|revoked
                created_at  TEXT DEFAULT (datetime('now')),
                approved_by INTEGER,
                approved_at TEXT,
                used_by     INTEGER,
                used_at     TEXT
            )
            """)

            # Indekslar
            cur.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(lower(username))")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status   ON tasks(status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_invreq_status  ON invite_requests(status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_invites_token  ON invites(token)")

    # ---------------- Users ----------------
    def upsert_user(self, telegram_id: int, username: Optional[str], full_name: str) -> Dict[str, Any]:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
            row = cur.fetchone()
            if row:
                cur.execute(
                    "UPDATE users SET username=?, full_name=? WHERE telegram_id=?",
                    (username, full_name, telegram_id),
                )
            else:
                cur.execute(
                    "INSERT INTO users(telegram_id, username, full_name) VALUES(?,?,?)",
                    (telegram_id, username, full_name),
                )
            cur.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
            return cur.fetchone()

    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
            return cur.fetchone()

    def list_all_users(self) -> List[Dict[str, Any]]:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM users ORDER BY username IS NULL, lower(username)")
            return cur.fetchall() or []

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        if not username:
            return None
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE lower(username)=lower(?)", (username,))
            return cur.fetchone()

    def set_user_role(self, telegram_id: int, role: str) -> None:
        with self._conn() as con:
            con.execute("UPDATE users SET role=? WHERE telegram_id=?", (role, telegram_id))

    def get_user_role(self, telegram_id: int) -> Optional[str]:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT role FROM users WHERE telegram_id=?", (telegram_id,))
            r = cur.fetchone()
            return r["role"] if r else None

    def set_user_language(self, telegram_id: int, lang: str) -> None:
        with self._conn() as con:
            con.execute("UPDATE users SET language=? WHERE telegram_id=?", (lang, telegram_id))

    def set_user_active(self, telegram_id: int, active: bool) -> None:
        with self._conn() as con:
            con.execute("UPDATE users SET active=? WHERE telegram_id=?", (1 if active else 0, telegram_id))

    def is_user_active(self, telegram_id: int) -> bool:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT COALESCE(active,1) AS a FROM users WHERE telegram_id=?", (telegram_id,))
            r = cur.fetchone()
            return bool(r["a"]) if r else True

    def list_employees(self) -> List[Dict[str, Any]]:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("""
                SELECT * FROM users
                WHERE role='EMPLOYEE' AND COALESCE(active,1)=1
                ORDER BY username IS NULL, lower(username)
            """)
            return cur.fetchall() or []

    def list_managers(self) -> List[Dict[str, Any]]:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE role='MANAGER'")
            return cur.fetchall() or []

    def remove_employee_by_username(self, username: str) -> bool:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT telegram_id FROM users WHERE lower(username)=lower(?) AND role='EMPLOYEE'", (username,))
            row = cur.fetchone()
            if not row:
                return False
            cur.execute("UPDATE users SET role=NULL WHERE lower(username)=lower(?)", (username,))
            return True

    # ---------- Assignee resolution ----------
    def resolve_assignee(self, name_or_username: str) -> Optional[Dict[str, Any]]:
        key = (name_or_username or "").strip()
        if not key:
            return None
        with self._conn() as con:
            cur = con.cursor()
            if key.startswith("@"):
                cur.execute("SELECT * FROM users WHERE lower(username)=lower(?)", (key.lstrip("@"),))
                return cur.fetchone()
            # full_name bo‘yicha — avval aniq, keyin LIKE
            cur.execute("SELECT * FROM users WHERE lower(full_name)=lower(?)", (key,))
            r = cur.fetchone()
            if r:
                return r
            cur.execute("""
                SELECT * FROM users
                WHERE lower(full_name) LIKE lower(?)
                ORDER BY length(full_name) ASC
                LIMIT 1
            """, (f"%{key}%",))
            return cur.fetchone()

    # ---------------- Tasks ----------------
    def create_task(
        self,
        title: str,
        description: str,
        created_by: int,
        assigned_to_username: Optional[str],
        deadline: Optional[str],
        priority: str,
    ) -> int:
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
                ORDER BY CASE WHEN status='done' THEN 1 ELSE 0 END, created_at DESC
            """, (telegram_id,))
            return cur.fetchall() or []

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
            return cur.fetchone()

    def set_task_status(self, task_id: int, status: str, by: int, reason: Optional[str] = None) -> bool:
        with self._conn() as con:
            cur = con.cursor()
            if status == "accepted":
                cur.execute("UPDATE tasks SET status='accepted', accepted_at=datetime('now') WHERE id=? AND assigned_to=?",
                            (task_id, by))
            elif status == "rejected":
                cur.execute("""
                    UPDATE tasks
                    SET status='rejected', reject_reason=?, completed_at=NULL
                    WHERE id=? AND assigned_to=?
                """, (reason or "", task_id, by))
            elif status == "done":
                cur.execute("""
                    UPDATE tasks
                    SET status='done', completed_at=datetime('now')
                    WHERE id=? AND assigned_to=?
                """, (task_id, by))
            else:
                return False
            return cur.rowcount > 0

    def mark_task_done_with_report(self, task_id: int, by: int, report: str) -> bool:
        # task_id==0 — umumiy (kundalik) hisobot
        if int(task_id) == 0:
            self.save_report(by, report, self.count_completed_today(by))
            return True
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("""
                UPDATE tasks
                SET status='done',
                    completed_at=datetime('now'),
                    report_text=?
                WHERE id=? AND assigned_to=?
            """, (report or "", task_id, by))
            return cur.rowcount > 0

    # ---------------- Reports & overview ----------------
    def count_completed_today(self, telegram_id: int) -> int:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("""
                SELECT COUNT(*) AS c
                FROM tasks
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
                WHERE u.role='EMPLOYEE' AND COALESCE(u.active,1)=1
                GROUP BY u.telegram_id
                ORDER BY lower(u.username)
            """)
            return cur.fetchall() or []

    def get_status_overview(self) -> List[Dict[str, Any]]:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE role='EMPLOYEE' AND COALESCE(active,1)=1 ORDER BY lower(username)")
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

    # ---------------- Invites (requests & tokens) ----------------
    def _gen_token(self) -> str:
        return secrets.token_urlsafe(12)

    def create_invite_request(self, user_id: int, username: Optional[str], full_name: Optional[str]) -> int:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT id FROM invite_requests WHERE user_id=? AND status='pending' ORDER BY id DESC LIMIT 1",
                (user_id,),
            )
            r = cur.fetchone()
            if r:
                return int(r["id"])
            cur.execute("""
                INSERT INTO invite_requests(user_id, username, full_name)
                VALUES(?,?,?)
            """, (user_id, username, full_name))
            return cur.lastrowid

    def list_invite_requests(self) -> List[Dict[str, Any]]:
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM invite_requests WHERE status='pending' ORDER BY created_at ASC")
            return cur.fetchall() or []

    def approve_invite_request(self, req_id: int) -> str:
        """Requestni tasdiqlab, tokenli invite yaratadi va deep-link qaytaradi."""
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM invite_requests WHERE id=?", (req_id,))
            req = cur.fetchone()
            if not req:
                raise ValueError("Invite request topilmadi")

            token = self._gen_token()
            cur.execute("""
                INSERT INTO invites(username, full_name, token, status, approved_by, approved_at)
                VALUES(?,?,?,?,?,datetime('now'))
            """, (req.get("username"), req.get("full_name"), token, "active", req.get("user_id")))
            cur.execute("UPDATE invite_requests SET status='approved', decided_at=datetime('now') WHERE id=?", (req_id,))

            bot = BOT_USERNAME or os.getenv("BOT_USERNAME", "")
            link = f"https://t.me/{bot}?start=invite-{token}" if bot else f"invite-{token}"
            return link

    def reject_invite_request(self, req_id: int, reason: Optional[str] = None) -> None:
        with self._conn() as con:
            con.execute("UPDATE invite_requests SET status='rejected', reason=?, decided_at=datetime('now') WHERE id=?",
                        (reason or "", req_id))

    def create_invite_for(self, username: str, full_name: Optional[str], created_by: int | None = None) -> Tuple[bool, str]:
        """Manager panelidan bevosita invite yaratish (requestsiz)."""
        if not username:
            return False, ""
        with self._conn() as con:
            cur = con.cursor()
            token = self._gen_token()
            cur.execute("""
                INSERT INTO invites(username, full_name, token, status, approved_by, approved_at)
                VALUES(?,?,?, 'active', ?, datetime('now'))
            """, (username, full_name or None, token, created_by))
        bot = BOT_USERNAME or os.getenv("BOT_USERNAME", "")
        link = f"https://t.me/{bot}?start=invite-{token}" if bot else f"invite-{token}"
        return True, link

    def consume_invite(self, token: str, user_id: int, username: Optional[str], full_name: Optional[str]) -> bool:
        """Deep-link tokenini ishlatadi va foydalanuvchini EMPLOYEE sifatida yoqadi."""
        # /start invite-<token>
        token = token.replace("invite-", "")
        with self._conn() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM invites WHERE token=? AND status='active'", (token,))
            inv = cur.fetchone()
            if not inv:
                return False
            # userni yangilaymiz / role=EMPLOYEE
            cur.execute("""
                INSERT INTO users(telegram_id, username, full_name, role, active)
                VALUES(?,?,?,?,1)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    username=COALESCE(excluded.username, users.username),
                    full_name=COALESCE(excluded.full_name, users.full_name),
                    role=COALESCE(users.role, 'EMPLOYEE'),
                    active=1
            """, (user_id, username, full_name, 'EMPLOYEE'))
            # tokenni used
            cur.execute("UPDATE invites SET status='used', used_by=?, used_at=datetime('now') WHERE id=?",
                        (user_id, inv["id"]))
            return True
