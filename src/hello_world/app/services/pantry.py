from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

from hello_world.app.core.config import settings

def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(
        settings.sqlite_path,
        check_same_thread=False,
    )
    connection.row_factory = sqlite3.Row
    return connection


def init_pantry_table() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS pantry_items (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                expires_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_pantry_user
            ON pantry_items(user_id)
            """
        )


init_pantry_table()



def _row_to_item(row: sqlite3.Row) -> dict[str, object]:
    return {
        "id": row["id"],
        "name": row["name"],
        "quantity": row["quantity"],
        "unit": row["unit"],
        "expires_at": row["expires_at"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_pantry_items(user_id: str) -> list[dict[str, object]]:
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT id, name, quantity, unit, expires_at,
                   created_at, updated_at
            FROM pantry_items
            WHERE user_id = ?
            ORDER BY
                CASE WHEN expires_at IS NULL THEN 1 ELSE 0 END,
                expires_at ASC,
                created_at DESC
            """,
            (user_id,),
        ).fetchall()

    return [_row_to_item(row) for row in rows]


def get_pantry_item(
    user_id: str,
    item_id: str,
) -> dict[str, object] | None:
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT id, name, quantity, unit, expires_at,
                   created_at, updated_at
            FROM pantry_items
            WHERE id = ? AND user_id = ?
            """,
            (item_id, user_id),
        ).fetchone()

    return _row_to_item(row) if row else None


def create_pantry_item(
    user_id: str,
    name: str,
    quantity: float,
    unit: str,
    expires_at: str | None,
) -> dict[str, object]:
    now = datetime.now(timezone.utc).isoformat()
    item_id = uuid4().hex

    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO pantry_items (
                id, user_id, name, quantity, unit,
                expires_at, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                user_id,
                name,
                quantity,
                unit,
                expires_at,
                now,
                now,
            ),
        )

    return {
        "id": item_id,
        "name": name,
        "quantity": quantity,
        "unit": unit,
        "expires_at": expires_at,
        "created_at": now,
        "updated_at": now,
    }


def update_pantry_item(
    user_id: str,
    item_id: str,
    changes: dict[str, object],
) -> dict[str, object] | None:
    allowed_fields = {
        "name",
        "quantity",
        "unit",
        "expires_at",
    }

    updates = {
        key: value
        for key, value in changes.items()
        if key in allowed_fields
    }

    if not updates:
        return get_pantry_item(user_id, item_id)

    updates["updated_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    fields = ", ".join(f"{key} = ?" for key in updates)
    values = list(updates.values())
    values.extend([item_id, user_id])

    with _connect() as connection:
        cursor = connection.execute(
            f"""
            UPDATE pantry_items
            SET {fields}
            WHERE id = ? AND user_id = ?
            """,
            values,
        )

        if cursor.rowcount == 0:
            return None

    return get_pantry_item(user_id, item_id)


def delete_pantry_item(
    user_id: str,
    item_id: str,
) -> bool:
    with _connect() as connection:
        cursor = connection.execute(
            """
            DELETE FROM pantry_items
            WHERE id = ? AND user_id = ?
            """,
            (item_id, user_id),
        )

    return cursor.rowcount > 0
