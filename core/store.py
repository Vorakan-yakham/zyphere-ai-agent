"""SQLite long-term state: events, lessons, skills, tasks, settings, usage."""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

DEFAULT_DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "zyphere.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, kind TEXT, axis TEXT,
    goal TEXT, summary TEXT, file_info TEXT, status TEXT);
CREATE TABLE IF NOT EXISTS lessons(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, text TEXT, topic TEXT,
    source TEXT, score INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS skills(name TEXT PRIMARY KEY, ts TEXT, description TEXT, code TEXT, tests TEXT,
    version INTEGER DEFAULT 1, runs INTEGER DEFAULT 0, passes INTEGER DEFAULT 0, last_run TEXT);
CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, type TEXT, title TEXT,
    detail TEXT, status TEXT, result TEXT);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS usage(day TEXT, source TEXT, calls INTEGER DEFAULT 0, in_tokens INTEGER DEFAULT 0,
    out_tokens INTEGER DEFAULT 0, PRIMARY KEY(day, source));
"""
TABLES = ["events", "lessons", "skills", "tasks", "settings", "usage"]


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


class Store:
    def __init__(self, path: Optional[str] = None):
        self.path = path or os.environ.get("ZYPHERE_DB") or DEFAULT_DB
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with self._conn() as c:
            c.execute("PRAGMA journal_mode=WAL")
            c.executescript(SCHEMA)

    @contextmanager
    def _conn(self):
        c = sqlite3.connect(self.path, timeout=15)
        c.row_factory = sqlite3.Row
        try:
            yield c
            c.commit()
        finally:
            c.close()

    def _all(self, sql: str, args=()) -> List[Dict[str, Any]]:
        with self._conn() as c:
            return [dict(r) for r in c.execute(sql, args)]

    def _run(self, sql: str, args=()) -> int:
        with self._conn() as c:
            return c.execute(sql, args).lastrowid

    # ---- settings ----
    def get_setting(self, key: str, default: Any = None) -> Any:
        rows = self._all("SELECT value FROM settings WHERE key=?", (key,))
        if not rows:
            return default
        try:
            return json.loads(rows[0]["value"])
        except (json.JSONDecodeError, TypeError):
            return default

    def set_setting(self, key: str, value: Any) -> None:
        self._run("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                  (key, json.dumps(value)))

    # ---- usage ----
    def add_usage(self, source: str, calls: int = 1, in_tokens: int = 0, out_tokens: int = 0) -> None:
        self._run("INSERT INTO usage(day,source,calls,in_tokens,out_tokens) VALUES(?,?,?,?,?) "
                  "ON CONFLICT(day,source) DO UPDATE SET calls=calls+excluded.calls, "
                  "in_tokens=in_tokens+excluded.in_tokens, out_tokens=out_tokens+excluded.out_tokens",
                  (today(), source, calls, in_tokens, out_tokens))

    def usage_today(self, source: str) -> Dict[str, int]:
        rows = self._all("SELECT calls,in_tokens,out_tokens FROM usage WHERE day=? AND source=?", (today(), source))
        return rows[0] if rows else {"calls": 0, "in_tokens": 0, "out_tokens": 0}

    # ---- events ----
    def add_event(self, kind: str, goal: str = "", summary: str = "", axis: str = "", file_info: str = "",
                  status: str = "") -> int:
        return self._run("INSERT INTO events(ts,kind,axis,goal,summary,file_info,status) VALUES(?,?,?,?,?,?,?)",
                         (now(), kind, axis, goal, summary, file_info, status))

    def events(self, kind: Optional[str] = None, limit: int = 50, since_id: int = 0,
               kinds: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Newest first."""
        where, args = ["id>?"], [since_id]
        if kind:
            where.append("kind=?"); args.append(kind)
        if kinds:
            where.append("kind IN (%s)" % ",".join("?" * len(kinds))); args += kinds
        return self._all(f"SELECT * FROM events WHERE {' AND '.join(where)} ORDER BY id DESC LIMIT ?", (*args, limit))

    def count_events(self, kind: str) -> int:
        return self._all("SELECT COUNT(*) n FROM events WHERE kind=?", (kind,))[0]["n"]

    def clear_events(self, kind: str) -> None:
        self._run("DELETE FROM events WHERE kind=?", (kind,))

    # ---- lessons ----
    def add_lesson(self, text: str, topic: str = "", source: str = "reflection", score: int = 1) -> bool:
        """True if new; an existing identical lesson just gains score."""
        text = " ".join(str(text).split())[:240]
        if not text:
            return False
        with self._conn() as c:
            row = c.execute("SELECT id FROM lessons WHERE lower(text)=lower(?)", (text,)).fetchone()
            if row:
                c.execute("UPDATE lessons SET score=score+1 WHERE id=?", (row["id"],))
                return False
            c.execute("INSERT INTO lessons(ts,text,topic,source,score) VALUES(?,?,?,?,?)",
                      (now(), text, topic[:40], source, score))
        return True

    def top_lessons(self, n: int = 8) -> List[Dict[str, Any]]:
        return self._all("SELECT * FROM lessons ORDER BY score DESC, id DESC LIMIT ?", (n,))

    def delete_lesson(self, lesson_id: int) -> None:
        self._run("DELETE FROM lessons WHERE id=?", (lesson_id,))

    # ---- skills ----
    def save_skill(self, name: str, description: str, code: str, tests: str) -> int:
        with self._conn() as c:
            row = c.execute("SELECT version FROM skills WHERE name=?", (name,)).fetchone()
            version = (row["version"] + 1) if row else 1
            c.execute("INSERT INTO skills(name,ts,description,code,tests,version) VALUES(?,?,?,?,?,?) "
                      "ON CONFLICT(name) DO UPDATE SET ts=excluded.ts, description=excluded.description, "
                      "code=excluded.code, tests=excluded.tests, version=excluded.version",
                      (name, now(), description, code, tests, version))
        return version

    def get_skill(self, name: str) -> Optional[Dict[str, Any]]:
        rows = self._all("SELECT * FROM skills WHERE name=?", (name,))
        return rows[0] if rows else None

    def list_skills(self) -> List[Dict[str, Any]]:
        return self._all("SELECT * FROM skills ORDER BY name")

    def delete_skill(self, name: str) -> None:
        self._run("DELETE FROM skills WHERE name=?", (name,))

    def record_skill_run(self, name: str, ok: bool) -> None:
        self._run("UPDATE skills SET runs=runs+1, passes=passes+?, last_run=? WHERE name=?", (1 if ok else 0, now(), name))

    # ---- tasks ----
    def add_task(self, type_: str, title: str, detail: str = "", status: str = "pending") -> int:
        return self._run("INSERT INTO tasks(ts,type,title,detail,status,result) VALUES(?,?,?,?,?,'')",
                         (now(), type_, title[:160], detail[:1500], status))

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        rows = self._all("SELECT * FROM tasks WHERE id=?", (task_id,))
        return rows[0] if rows else None

    def tasks(self, statuses: Optional[List[str]] = None, limit: int = 30) -> List[Dict[str, Any]]:
        if statuses:
            q = "SELECT * FROM tasks WHERE status IN (%s) ORDER BY id DESC LIMIT ?" % ",".join("?" * len(statuses))
            return self._all(q, (*statuses, limit))
        return self._all("SELECT * FROM tasks ORDER BY id DESC LIMIT ?", (limit,))

    def update_task(self, task_id: int, status: str, result: Optional[str] = None) -> None:
        if result is None:
            self._run("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
        else:
            self._run("UPDATE tasks SET status=?, result=? WHERE id=?", (status, result[:6000], task_id))

    # ---- backup / restore ----
    def export_all(self) -> Dict[str, List[Dict[str, Any]]]:
        return {t: self._all(f"SELECT * FROM {t}") for t in TABLES}

    def import_all(self, data: Dict[str, Any]) -> None:
        if not isinstance(data, dict) or not any(t in data for t in TABLES):
            raise ValueError("ไฟล์สำรองไม่ถูกต้อง")
        with self._conn() as c:
            for t in TABLES:
                rows = data.get(t, [])
                if not isinstance(rows, list):
                    continue
                cols = [r[1] for r in c.execute(f"PRAGMA table_info({t})")]
                c.execute(f"DELETE FROM {t}")
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    keys = [k for k in row if k in cols]
                    if keys:
                        c.execute(f"INSERT INTO {t}({','.join(keys)}) VALUES({','.join('?' * len(keys))})",
                                  [row[k] for k in keys])

    def erase_all(self) -> None:
        with self._conn() as c:
            for t in TABLES:
                c.execute(f"DELETE FROM {t}")
