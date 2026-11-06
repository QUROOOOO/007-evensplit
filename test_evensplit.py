"""
test_evensplit.py - Automated Unit & Integration Tests for EvenSplit
====================================================================
Capstone CP-007: Group Expense Settlement Optimizer
"""

import os
import unittest
import engine
import data_manager


class TestEngine(unittest.TestCase):
    """Unit tests for engine.py core calculations and validation."""

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

    def test_record_expense_invalid_inputs(self):
        engine.add_member(self.members, "Alice")
        engine.add_member(self.members, "Bob")

        # Zero or negative amount
        with self.assertRaises(ValueError):
            engine.record_expense(self.expenses, self.members, "Test", 0, "Alice", ["Alice", "Bob"])
        with self.assertRaises(ValueError):
            engine.record_expense(self.expenses, self.members, "Test", -50, "Alice", ["Alice", "Bob"])

        # Non-existent payer
        with self.assertRaises(ValueError):
            engine.record_expense(self.expenses, self.members, "Test", 100, "Unknown", ["Alice", "Bob"])

        # Empty participants
        with self.assertRaises(ValueError):
            engine.record_expense(self.expenses, self.members, "Test", 100, "Alice", [])

        # Non-existent participant
        with self.assertRaises(ValueError):
            engine.record_expense(self.expenses, self.members, "Test", 100, "Alice", ["Alice", "Unknown"])

    def test_calculate_net_balances_simple(self):
        # Alice pays 100 for Alice and Bob
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
        # Alice pays 90 for all 3 (share = 30 each)
        # Bob pays 60 for Bob and Charlie (share = 30 each)
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
        # Alice: paid 90, consumed 30 -> Net = +60
        # Bob: paid 60, consumed 30 + 30 = 60 -> Net = 0
        # Charlie: paid 0, consumed 30 + 30 = 60 -> Net = -60
        balances = engine.calculate_net_balances(members, expenses)
        self.assertEqual(balances["Alice"], 60.0)
        self.assertEqual(balances["Bob"], 0.0)
        self.assertEqual(balances["Charlie"], -60.0)
        self.assertEqual(round(sum(balances.values()), 2), 0.0)

    def test_compute_min_settlements_greedy(self):
        # Alice: +60, Bob: 0, Charlie: -60
        net_balances = {"Alice": 60.0, "Bob": 0.0, "Charlie": -60.0}
        transfers = engine.compute_min_settlements(net_balances)

        self.assertEqual(len(transfers), 1)
        self.assertEqual(transfers[0]["from"], "Charlie")
        self.assertEqual(transfers[0]["to"], "Alice")
        self.assertEqual(transfers[0]["amount"], 60.0)

    def test_compute_min_settlements_complex(self):
        # 4 members complex debts:
        # A: +100, B: +50, C: -80, D: -70
        net_balances = {"A": 100.0, "B": 50.0, "C": -80.0, "D": -70.0}
        transfers = engine.compute_min_settlements(net_balances)

        # Total settled must equal total positive balance (150.0)
        total_settled = sum(t["amount"] for t in transfers)
        self.assertAlmostEqual(total_settled, 150.0, places=2)

        # Verify that applying transfers zeroes out everyone's balance
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


class TestDataManager(unittest.TestCase):
    """Unit tests for data_manager.py JSON persistence."""

    def setUp(self):
        self.test_file = "test_data_temp.json"

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_save_and_load_roundtrip(self):
        group_name = "Hackathon Squad"
        members = ["Dev1", "Dev2"]
        expenses = [
            {"id": 1, "description": "Pizza", "amount": 50.0, "payer": "Dev1", "participants": ["Dev1", "Dev2"], "split_amount": 25.0}
        ]

        save_res = data_manager.save_data(group_name, members, expenses, filepath=self.test_file)
        self.assertTrue(save_res)
        self.assertTrue(data_manager.data_file_exists(filepath=self.test_file))

        loaded_name, loaded_members, loaded_expenses = data_manager.load_data(filepath=self.test_file)
        self.assertEqual(loaded_name, group_name)
        self.assertEqual(loaded_members, members)
        self.assertEqual(len(loaded_expenses), 1)
        self.assertEqual(loaded_expenses[0]["description"], "Pizza")

    def test_load_non_existent(self):
        loaded_name, loaded_members, loaded_expenses = data_manager.load_data("non_existent_file_xyz.json")
        self.assertEqual(loaded_members, [])
        self.assertEqual(loaded_expenses, [])


if __name__ == "__main__":
    unittest.main()
