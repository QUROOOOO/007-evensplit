"""test_evensplit.py - Automated unit tests for EvenSplit (CP-007)."""

import os
import shutil
import unittest
import engine
import data_manager


class TestEngine(unittest.TestCase):
    """Unit tests for engine.py core calculations, validation, and editing."""

    def setUp(self):
        self.members = []
        self.expenses = []

    def test_add_member_valid(self):
        added = engine.add_member(self.members, "Alice")
        self.assertEqual(added, "Alice")
        self.assertIn("Alice", self.members)

        added2 = engine.add_member(self.members, "  Bob  ")
        self.assertEqual(added2, "Bob")
        self.assertIn("Bob", self.members)

    def test_add_member_empty_or_whitespace(self):
        with self.assertRaises(ValueError):
            engine.add_member(self.members, "")
        with self.assertRaises(ValueError):
            engine.add_member(self.members, "   ")

    def test_add_member_case_insensitive_duplicate(self):
        engine.add_member(self.members, "Alice")
        with self.assertRaises(ValueError):
            engine.add_member(self.members, "alice")
        with self.assertRaises(ValueError):
            engine.add_member(self.members, "ALICE")
        with self.assertRaises(ValueError):
            engine.add_member(self.members, " Alice ")

    def test_record_expense_valid(self):
        engine.add_member(self.members, "Alice")
        engine.add_member(self.members, "Bob")
        engine.add_member(self.members, "Charlie")

        exp = engine.record_expense(
            self.expenses,
            self.members,
            desc="Dinner",
            amount=90.0,
            payer="Alice",
            participants=["Alice", "Bob", "Charlie"]
        )
        self.assertEqual(exp["amount"], 90.0)
        self.assertEqual(exp["payer"], "Alice")
        self.assertEqual(len(exp["participants"]), 3)
        self.assertEqual(exp["split_amount"], 30.0)
        self.assertEqual(len(self.expenses), 1)

    def test_record_expense_with_quantity(self):
        engine.add_member(self.members, "Alice")
        engine.add_member(self.members, "Bob")
        exp = engine.record_expense(
            self.expenses,
            self.members,
            desc="Masala Dosa (x2)",
            amount=80.0,
            payer="Alice",
            participants=["Alice", "Bob"],
            quantity=2
        )
        self.assertEqual(exp["quantity"], 2)
        self.assertEqual(exp["amount"], 80.0)
        self.assertEqual(exp["split_amount"], 40.0)

    def test_record_expense_invalid_inputs(self):
        engine.add_member(self.members, "Alice")
        engine.add_member(self.members, "Bob")

        with self.assertRaises(ValueError):
            engine.record_expense(self.expenses, self.members, "Test", 0, "Alice", ["Alice", "Bob"])
        with self.assertRaises(ValueError):
            engine.record_expense(self.expenses, self.members, "Test", -50, "Alice", ["Alice", "Bob"])
        with self.assertRaises(ValueError):
            engine.record_expense(self.expenses, self.members, "Test", 100, "Unknown", ["Alice", "Bob"])
        with self.assertRaises(ValueError):
            engine.record_expense(self.expenses, self.members, "Test", 100, "Alice", [])
        with self.assertRaises(ValueError):
            engine.record_expense(self.expenses, self.members, "Test", 100, "Alice", ["Alice", "Unknown"])

    def test_calculate_net_balances_simple(self):
        members = ["Alice", "Bob"]
        expenses = [{
            "id": 1,
            "description": "Lunch",
            "amount": 100.0,
            "payer": "Alice",
            "participants": ["Alice", "Bob"],
            "split_amount": 50.0
        }]
        balances = engine.calculate_net_balances(members, expenses)
        self.assertEqual(balances["Alice"], 50.0)
        self.assertEqual(balances["Bob"], -50.0)
        self.assertEqual(round(sum(balances.values()), 2), 0.0)

    def test_calculate_net_balances_multi(self):
        members = ["Alice", "Bob", "Charlie"]
        expenses = [
            {
                "id": 1, "description": "Dinner", "amount": 90.0,
                "payer": "Alice", "participants": ["Alice", "Bob", "Charlie"], "split_amount": 30.0
            },
            {
                "id": 2, "description": "Taxi", "amount": 60.0,
                "payer": "Bob", "participants": ["Bob", "Charlie"], "split_amount": 30.0
            }
        ]
        balances = engine.calculate_net_balances(members, expenses)
        self.assertEqual(balances["Alice"], 60.0)
        self.assertEqual(balances["Bob"], 0.0)
        self.assertEqual(balances["Charlie"], -60.0)
        self.assertEqual(round(sum(balances.values()), 2), 0.0)

    def test_compute_min_settlements_greedy(self):
        net_balances = {"Alice": 60.0, "Bob": 0.0, "Charlie": -60.0}
        transfers = engine.compute_min_settlements(net_balances)
        self.assertEqual(len(transfers), 1)
        self.assertEqual(transfers[0]["from"], "Charlie")
        self.assertEqual(transfers[0]["to"], "Alice")
        self.assertEqual(transfers[0]["amount"], 60.0)

    def test_compute_min_settlements_complex(self):
        net_balances = {"A": 100.0, "B": 50.0, "C": -80.0, "D": -70.0}
        transfers = engine.compute_min_settlements(net_balances)

        total_settled = sum(t["amount"] for t in transfers)
        self.assertAlmostEqual(total_settled, 150.0, places=2)

        working = dict(net_balances)
        for t in transfers:
            working[t["from"]] += t["amount"]
            working[t["to"]] -= t["amount"]

        for person, bal in working.items():
            self.assertAlmostEqual(bal, 0.0, places=2)

    def test_compute_min_settlements_already_settled(self):
        net_balances = {"Alice": 0.0, "Bob": 0.0}
        transfers = engine.compute_min_settlements(net_balances)
        self.assertEqual(len(transfers), 0)

    def test_edit_engine_rename_member(self):
        members = ["Alice", "Bob"]
        expenses = [
            {"id": 1, "description": "Taxi", "amount": 40.0, "payer": "Alice", "participants": ["Alice", "Bob"], "split_amount": 20.0}
        ]
        engine.rename_member(members, expenses, "Alice", "Alicia")
        self.assertIn("Alicia", members)
        self.assertNotIn("Alice", members)
        self.assertEqual(expenses[0]["payer"], "Alicia")
        self.assertIn("Alicia", expenses[0]["participants"])

    def test_edit_engine_delete_member_prevent_payer(self):
        members = ["Alice", "Bob"]
        expenses = [
            {"id": 1, "description": "Taxi", "amount": 40.0, "payer": "Alice", "participants": ["Alice", "Bob"], "split_amount": 20.0}
        ]
        with self.assertRaises(ValueError):
            engine.delete_member(members, expenses, "Alice")

    def test_edit_engine_delete_member_participant(self):
        members = ["Alice", "Bob", "Charlie"]
        expenses = [
            {"id": 1, "description": "Pizza", "amount": 60.0, "payer": "Alice", "participants": ["Alice", "Bob", "Charlie"], "split_amount": 20.0}
        ]
        engine.delete_member(members, expenses, "Charlie")
        self.assertNotIn("Charlie", members)
        self.assertEqual(expenses[0]["participants"], ["Alice", "Bob"])
        self.assertEqual(expenses[0]["split_amount"], 30.0)

    def test_parse_amount_valid_literals(self):
        self.assertEqual(engine.parse_amount("40"), 40.0)
        self.assertEqual(engine.parse_amount("150.50"), 150.50)
        self.assertEqual(engine.parse_amount("  99.9  "), 99.9)

    def test_parse_amount_valid_expressions(self):
        self.assertEqual(engine.parse_amount("10 * 4"), 40.0)
        self.assertEqual(engine.parse_amount("25 + 30 + 15"), 70.0)
        self.assertEqual(engine.parse_amount("500 / 4"), 125.0)
        self.assertEqual(engine.parse_amount("100 - 25.50"), 74.50)
        self.assertEqual(engine.parse_amount("(10 + 5) * 2"), 30.0)

    def test_parse_amount_invalid(self):
        with self.assertRaises(ValueError):
            engine.parse_amount("0")
        with self.assertRaises(ValueError):
            engine.parse_amount("-50")
        with self.assertRaises(ValueError):
            engine.parse_amount("10 / 0")
        with self.assertRaises(ValueError):
            engine.parse_amount("invalid_text")
        with self.assertRaises(ValueError):
            engine.parse_amount("__import__('os')")
        with self.assertRaises(ValueError):
            engine.parse_amount("")

    def test_edit_engine_update_and_delete_expense(self):
        members = ["Alice", "Bob"]
        expenses = [
            {"id": 1, "description": "Coffee", "amount": 10.0, "payer": "Alice", "participants": ["Alice", "Bob"], "split_amount": 5.0}
        ]
        engine.update_expense(expenses, members, 1, desc="Specialty Coffee", amount=20.0)
        self.assertEqual(expenses[0]["description"], "Specialty Coffee")
        self.assertEqual(expenses[0]["amount"], 20.0)
        self.assertEqual(expenses[0]["split_amount"], 10.0)

        deleted = engine.delete_expense(expenses, 1)
        self.assertTrue(deleted)
        self.assertEqual(len(expenses), 0)


class TestDataManager(unittest.TestCase):
    """Unit tests for data_manager.py JSON persistence and multi-file storage."""

    def setUp(self):
        self.test_file = "test_data_temp.json"
        self.test_dir = "test_saved_bills"
        data_manager.SAVED_BILLS_DIR = self.test_dir

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        data_manager.SAVED_BILLS_DIR = "saved_bills"

    def test_save_and_load_roundtrip(self):
        group_name = "Hackathon Squad"
        members = ["Dev1", "Dev2"]
        expenses = [
            {"id": 1, "description": "Pizza", "amount": 50.0, "payer": "Dev1", "participants": ["Dev1", "Dev2"], "split_amount": 25.0}
        ]

        ok, path = data_manager.save_data(group_name, members, expenses, filepath=self.test_file)
        self.assertTrue(ok)
        self.assertTrue(data_manager.data_file_exists(filepath=self.test_file))

        loaded_name, loaded_members, loaded_expenses = data_manager.load_data(filepath=self.test_file)
        self.assertEqual(loaded_name, group_name)
        self.assertEqual(loaded_members, members)
        self.assertEqual(len(loaded_expenses), 1)

    def test_multi_file_saved_bills(self):
        group_name = "Kanak Bday"
        members = ["Kanak", "Archak"]
        expenses = [{"id": 1, "description": "Cake", "amount": 500.0, "payer": "Archak", "participants": members, "split_amount": 250.0}]

        data_manager.save_data(group_name, members, expenses, filepath=self.test_file)
        bills = data_manager.list_saved_bills()
        self.assertEqual(len(bills), 1)
        self.assertEqual(bills[0]["group_name"], "Kanak Bday")
        self.assertEqual(bills[0]["members_count"], 2)
        self.assertEqual(bills[0]["total_spend"], 500.0)

    def test_rename_group_cleans_old_file(self):
        data_manager.save_data("Trip Goa", ["A", "B"], [], filepath=self.test_file)
        self.assertTrue(os.path.isfile(os.path.join(self.test_dir, "trip_goa.json")))

        data_manager.save_data("Trip Manali", ["A", "B"], [], filepath=self.test_file, old_group_name="Trip Goa")
        self.assertFalse(os.path.isfile(os.path.join(self.test_dir, "trip_goa.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.test_dir, "trip_manali.json")))

    def test_load_non_existent(self):
        loaded_name, loaded_members, loaded_expenses = data_manager.load_data("non_existent_file_xyz.json")
        self.assertEqual(loaded_members, [])
        self.assertEqual(loaded_expenses, [])


if __name__ == "__main__":
    unittest.main()
