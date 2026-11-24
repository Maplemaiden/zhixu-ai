"""演示用账号 + 标注：SQLite 落盘，重启不丢。"""
from __future__ import annotations

import hashlib
import secrets
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from app.config import get_settings

DEMO_USERS = [
    {"username": "demo", "password": "demo123", "display_name": "演示学生"},
    {"username": "student", "password": "student123", "display_name": "体验学生"},
]

TAG_PRESETS = ["重点", "公式", "易错", "案例", "待复习"]


def _db_path() -> Path:
    settings = get_settings()
    path = Path(settings.user_db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_db_path()), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    ).hex()
    return digest, salt


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              id TEXT PRIMARY KEY,
              username TEXT UNIQUE NOT NULL,
              password_hash TEXT NOT NULL,
              salt TEXT NOT NULL,
              display_name TEXT NOT NULL,
              created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tokens (
              token TEXT PRIMARY KEY,
              user_id TEXT NOT NULL,
              created_at REAL NOT NULL,
              FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS notes (
              id TEXT PRIMARY KEY,
              user_id TEXT NOT NULL,
              method_id TEXT NOT NULL,
              section_index INTEGER NOT NULL DEFAULT 0,
              quote TEXT NOT NULL,
              color TEXT NOT NULL DEFAULT 'amber',
              tag TEXT NOT NULL DEFAULT '',
              remark TEXT NOT NULL DEFAULT '',
              created_at REAL NOT NULL,
              updated_at REAL NOT NULL,
              FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_notes_user ON notes(user_id);
            CREATE INDEX IF NOT EXISTS idx_notes_method ON notes(user_id, method_id);
            """
        )
        for demo in DEMO_USERS:
            row = conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (demo["username"],),
            ).fetchone()
            if row:
                continue
            pwd_hash, salt = _hash_password(demo["password"])
            conn.execute(
                "INSERT INTO users (id, username, password_hash, salt, display_name, created_at) VALUES (?,?,?,?,?,?)",
                (
                    str(uuid.uuid4()),
                    demo["username"],
                    pwd_hash,
                    salt,
                    demo["display_name"],
                    time.time(),
                ),
            )
        conn.commit()


def _user_public(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"],
    }


def register_user(username: str, password: str, display_name: str = "") -> dict[str, Any]:
    username = username.strip()
    if not username or len(username) < 2:
        raise ValueError("账号至少 2 个字符")
    if not password or len(password) < 4:
        raise ValueError("密码至少 4 位")
    display_name = (display_name or username).strip()
    pwd_hash, salt = _hash_password(password)
    user_id = str(uuid.uuid4())
    with _connect() as conn:
        exists = conn.execute(
            "SELECT 1 FROM users WHERE username = ?", (username,)
        ).fetchone()
        if exists:
            raise ValueError("账号已存在")
        conn.execute(
            "INSERT INTO users (id, username, password_hash, salt, display_name, created_at) VALUES (?,?,?,?,?,?)",
            (user_id, username, pwd_hash, salt, display_name, time.time()),
        )
        conn.commit()
    return {"id": user_id, "username": username, "display_name": display_name}


def authenticate(username: str, password: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username.strip(),)
        ).fetchone()
    if not row:
        return None
    digest, _ = _hash_password(password, row["salt"])
    if not secrets.compare_digest(digest, row["password_hash"]):
        return None
    return _user_public(row)


def create_token(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    with _connect() as conn:
        conn.execute(
            "INSERT INTO tokens (token, user_id, created_at) VALUES (?,?,?)",
            (token, user_id, time.time()),
        )
        conn.commit()
    return token


def revoke_token(token: str) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM tokens WHERE token = ?", (token,))
        conn.commit()


def user_from_token(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT u.id, u.username, u.display_name
            FROM tokens t
            JOIN users u ON u.id = t.user_id
            WHERE t.token = ?
            """,
            (token,),
        ).fetchone()
    return _user_public(row) if row else None


def _note_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "method_id": row["method_id"],
        "section_index": row["section_index"],
        "quote": row["quote"],
        "color": row["color"],
        "tag": row["tag"] or "",
        "remark": row["remark"] or "",
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_notes(user_id: str, method_id: str | None = None) -> list[dict[str, Any]]:
    with _connect() as conn:
        if method_id:
            rows = conn.execute(
                "SELECT * FROM notes WHERE user_id = ? AND method_id = ? ORDER BY created_at DESC",
                (user_id, method_id),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM notes WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
    return [_note_row(r) for r in rows]


def create_note(
    user_id: str,
    *,
    method_id: str,
    quote: str,
    section_index: int = 0,
    color: str = "amber",
    tag: str = "",
    remark: str = "",
) -> dict[str, Any]:
    quote = (quote or "").strip()
    if not quote:
        raise ValueError("高亮内容不能为空")
    if len(quote) > 2000:
        raise ValueError("高亮过长，请缩短选区")
    note_id = str(uuid.uuid4())
    now = time.time()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO notes
            (id, user_id, method_id, section_index, quote, color, tag, remark, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (
                note_id,
                user_id,
                method_id.strip(),
                int(section_index or 0),
                quote,
                (color or "amber").strip()[:20],
                (tag or "").strip()[:40],
                (remark or "").strip()[:500],
                now,
                now,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    return _note_row(row)


def update_note(
    user_id: str,
    note_id: str,
    *,
    color: str | None = None,
    tag: str | None = None,
    remark: str | None = None,
) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM notes WHERE id = ? AND user_id = ?",
            (note_id, user_id),
        ).fetchone()
        if not row:
            return None
        new_color = color if color is not None else row["color"]
        new_tag = tag if tag is not None else row["tag"]
        new_remark = remark if remark is not None else row["remark"]
        now = time.time()
        conn.execute(
            "UPDATE notes SET color = ?, tag = ?, remark = ?, updated_at = ? WHERE id = ?",
            (
                (new_color or "amber").strip()[:20],
                (new_tag or "").strip()[:40],
                (new_remark or "").strip()[:500],
                now,
                note_id,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    return _note_row(row)


def delete_note(user_id: str, note_id: str) -> bool:
    with _connect() as conn:
        cur = conn.execute(
            "DELETE FROM notes WHERE id = ? AND user_id = ?",
            (note_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0
