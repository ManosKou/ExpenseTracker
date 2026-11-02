import sqlite3
import tempfile
import unittest
from pathlib import Path

import database


class TestExpenseDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.original_db_path = database.DB_PATH

        database.DB_PATH = (
            Path(self.temp_directory.name) / "test_expenses.db"
        )
        database.init_database()

    def tearDown(self):
        database.DB_PATH = self.original_db_path
        self.temp_directory.cleanup()

    def add_sample_expense(self):
        database.add_expense(
            "2026-11-02",
            1250,
            "Food",
            "Lunch",
        )
        return database.get_expenses()[0]["id"]

    def test_add_and_read_expense(self):
        self.add_sample_expense()

        expenses = database.get_expenses()

        self.assertEqual(len(expenses), 1)
        self.assertEqual(expenses[0]["amount_cents"], 1250)
        self.assertEqual(expenses[0]["category"], "Food")

    def test_update_expense(self):
        expense_id = self.add_sample_expense()

        updated = database.update_expense(
            expense_id,
            "2026-11-03",
            2000,
            "Transport",
            "Taxi",
        )

        expense = database.get_expenses()[0]

        self.assertTrue(updated)
        self.assertEqual(expense["id"], expense_id)
        self.assertEqual(expense["expense_date"], "2026-11-03")
        self.assertEqual(expense["amount_cents"], 2000)
        self.assertEqual(expense["category"], "Transport")
        self.assertEqual(expense["description"], "Taxi")

    def test_delete_only_selected_expense(self):
        first_id = self.add_sample_expense()
        second_id = self.add_sample_expense()

        deleted = database.delete_expense(first_id)

        remaining = database.get_expenses()

        self.assertTrue(deleted)
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["id"], second_id)

    def test_delete_missing_expense(self):
        self.assertFalse(database.delete_expense(999))

    def test_update_missing_expense(self):
        updated = database.update_expense(
            999,
            "2026-11-02",
            500,
            "Food",
            "Missing",
        )
        self.assertFalse(updated)

    def test_reject_non_positive_amounts(self):
        for amount in (0, -100):
            with self.subTest(amount=amount):
                with self.assertRaises(sqlite3.IntegrityError):
                    database.add_expense(
                        "2026-11-02",
                        amount,
                        "Food",
                        "Invalid amount",
                    )

        self.assertEqual(database.get_expenses(), [])

    def test_description_with_sql_characters(self):
        description = "Lunch'); DROP TABLE expenses; --"

        database.add_expense(
            "2026-11-02",
            1000,
            "Food",
            description,
        )

        expenses = database.get_expenses()

        self.assertEqual(len(expenses), 1)
        self.assertEqual(
            expenses[0]["description"],
            description,
        )


if __name__ == "__main__":
    unittest.main()