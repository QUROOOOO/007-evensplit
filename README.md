# CP-007 EvenSplit: Group Expense Settlement Optimiser

## About the Project
When friends go on a trip or flatmates share expenses, different people pay for different bills—leading to a confusing chain of who owes whom. **EvenSplit** is a console-based expense manager and debt-simplification engine that tracks shared group expenses, calculates each member's real-time net balance, and resolves all debts using the **minimum possible number of payments**.

## How It Works
Instead of settling every bill individually, EvenSplit calculates a running **Net Balance** for each member (`Total Paid - Total Share Owed`) and uses a **Greedy Settlement Algorithm** to match the largest debtor with the largest creditor until everyone's balance reaches zero.

## Core Features
1. **Create a Group & Add Members:** Set up a group and register unique members with duplicate validation.
2. **Add Shared Expenses:** Record who paid, how much, and split the bill equally among chosen participants.
3. **View Member Net Balances:** See at a glance who is owed money (`+`), who owes money (`-`), and who is settled (`0`).
4. **Minimum Settlement Plan:** Generate the shortest list of exact transfers needed to clear all group debts.
5. **Full Expense History:** View a complete chronological log of every bill recorded in the group.

## Stretch Features
* **Unequal Splits:** Split expenses by custom percentages or exact amounts.
* **Multiple Groups:** Manage separate balances and histories across different groups.

## Team
* Archak Aryan and Archak Aryan

## How to Run
```bash
git clone [https://github.com/QUROOOOO/007-evensplit.git](https://github.com/QUROOOOO/007-evensplit.git)
cd 007-evensplit
python main.py