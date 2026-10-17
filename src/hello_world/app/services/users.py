from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

from hello_world.app.core.config import settings
from hello_world.app.core.security import (
    hash_password,
    verify_password,
)

def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(
        settings.sqlite_path,
        check_same_thread=False,
    )
    connection.row_factory = sqlite3.Row
    return connection

def init_user_table() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

init_user_table()

def _row_to_user(
    row: sqlite3.Row | None,
) -> dict[str, str] | None:
    if row is None:
        return None

    return {
        "id": row["id"],
        "username": row["username"],
        "password_hash": row["password_hash"],
        "created_at": row["created_at"],
    }

def get_user_by_username(
    username: str,
) -> dict[str, str] | None:
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT id, username, password_hash, created_at
            FROM users
            WHERE username = ?
            """,
            (username,),
        ).fetchone()

    return _row_to_user(row)


def get_user_by_id(
    user_id: str,
) -> dict[str, str] | None:
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT id, username, password_hash, created_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

    return _row_to_user(row)


def create_user(
    username: str,
    password: str,
) -> dict[str, str] | None:
    user_id = uuid4().hex
    created_at = datetime.now(timezone.utc).isoformat()
    password_hash = hash_password(password)

    try:
        with _connect() as connection:
            connection.execute(
                """
                INSERT INTO users (
                    id,
                    username,
                    password_hash,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    user_id,
                    username,
                    password_hash,
                    created_at,
                ),
            )
    except sqlite3.IntegrityError:
        return None

    return {
        "id": user_id,
        "username": username,
        "password_hash": password_hash,
        "created_at": created_at,
    }


def authenticate_user(
    username: str,
    password: str,
) -> dict[str, str] | None:
    user = get_user_by_username(username)

    if user is None:
        return None

    if not verify_password(
        password,
        user["password_hash"],
    ):
        return None

    return user