import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).resolve().parent / "data" / "expenses.db"


@contextmanager
def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)

    try:
        with connection:
            yield connection
    finally:
        connection.close()


def init_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_date TEXT NOT NULL,
                amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
                category TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT ''
            )
        """)


def add_expense(expense_date, amount_cents, category, description):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO expenses (
                expense_date, amount_cents, category, description
            )
            VALUES (?, ?, ?, ?)
            """,
            (expense_date, amount_cents, category, description),
        )


def get_expenses():
    with get_connection() as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("""
            SELECT id, expense_date, amount_cents, category, description
            FROM expenses
            ORDER BY expense_date DESC, id DESC
        """).fetchall()

    return [dict(row) for row in rows]


def delete_expense(expense_id):
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM expenses WHERE id = ?",
            (expense_id,),
        )
        return cursor.rowcount > 0


def update_expense(
    expense_id, expense_date, amount_cents, category, description
):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE expenses
            SET expense_date = ?,
                amount_cents = ?,
                category = ?,
                description = ?
            WHERE id = ?
            """,
            (
                expense_date,
                amount_cents,
                category,
                description,
                expense_id,
            ),
        )
        return cursor.rowcount > 0