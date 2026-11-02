from pathlib import Path

import database


DEMO_EXPENSES = [
    ("2026-09-03", 4250, "Food", "Weekly groceries"),
    ("2026-09-07", 2700, "Transport", "Public transport pass"),
    ("2026-09-12", 65000, "Housing", "Monthly rent"),
    ("2026-09-18", 5800, "Bills", "Electricity bill"),
    ("2026-09-23", 1800, "Entertainment", "Cinema tickets"),
    ("2026-10-02", 3675, "Food", "Weekly groceries"),
    ("2026-10-06", 2200, "Health", "Pharmacy"),
    ("2026-10-12", 65000, "Housing", "Monthly rent"),
    ("2026-10-16", 3200, "Bills", "Internet bill"),
    ("2026-10-21", 1450, "Transport", "Taxi"),
    ("2026-11-01", 4850, "Food", "Weekly groceries"),
    ("2026-11-02", 1200, "Entertainment", "Museum admission"),
]


def main():
    original_path = database.DB_PATH
    demo_path = (
        Path(__file__).resolve().parent
        / "data"
        / "demo_expenses.db"
    )

    try:
        database.DB_PATH = demo_path
        database.init_database()

        if database.get_expenses():
            print("Demo database already contains data. No changes made.")
            return

        with database.get_connection() as connection:
            connection.executemany(
                """
                INSERT INTO expenses (
                    expense_date,
                    amount_cents,
                    category,
                    description
                )
                VALUES (?, ?, ?, ?)
                """,
                DEMO_EXPENSES,
            )

        print(f"Created {len(DEMO_EXPENSES)} fictional demo expenses.")
    finally:
        database.DB_PATH = original_path


if __name__ == "__main__":
    main()