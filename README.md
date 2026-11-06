# CP-007 EvenSplit: Group Expense Settlement Optimizer

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Standard Library Only](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)]()
[![Code Style](https://img.shields.io/badge/aesthetic-Claude%20Code-purple.svg)]()

## About the Project
When friends go on a trip or flatmates share expenses, different people pay for different bills—leading to a confusing chain of who owes whom. **EvenSplit** is a console-based expense manager and debt-simplification engine that tracks shared group expenses, calculates each member's real-time net balance, and resolves all debts using the **minimum possible number of payments**.

Built strictly with Python's standard library (`sys`, `time`, `json`, `math`, `os`), EvenSplit combines simple, easy-to-understand arithmetic and algorithms with a developer-tool terminal interface inspired by Claude Code.

---

## Architecture & Code Structure

The project is structured into 4 modular, readable files:

```
007-evensplit/
├── engine.py          # Core mathematical logic & greedy cash-flow algorithm
├── data_manager.py    # Local JSON persistence (data.json)
├── tui.py             # Claude Code developer-tool terminal UI (Unicode boxes, colors, spinner)
├── main.py            # Menu-driven controller & input validation loops
├── test_evensplit.py  # Automated unit test suite
├── data.json          # Persistent JSON storage file
└── README.md          # Project documentation
```

### Module Responsibilities

1. **`engine.py` (Core Calculations)**:
   - `add_member(members, name)`: Validates non-empty names and enforces case-insensitive uniqueness.
   - `record_expense(expenses, members, desc, amount, payer, participants)`: Validates positive amounts, existing payers/participants, and computes per-person equal shares.
   - `calculate_net_balances(members, expenses)`: Computes real-time `net = total_paid - total_consumed` for all members.
   - `compute_min_settlements(net_balances)`: Greedy Cash-Flow Minimization algorithm that resolves debts in at most $N - 1$ peer-to-peer transfers.

2. **`data_manager.py` (Persistence)**:
   - Reads and writes group name, member list, and expense history to `data.json`.
   - Handles corrupted or missing files without crashing.

3. **`tui.py` (Terminal User Interface)**:
   - Unicode box-drawing characters (`╭`, `─`, `╮`, `│`, `╰`, `╯`, `├`, `┤`, `┬`, `┴`, `┼`).
   - Claude Code ANSI styling (cyan accents, purple badges, bold white headers, emerald green checks, crimson warnings).
   - 0.8-second braille spinner animation (`⠋ ⠙ ⠹ ...`).
   - Formatted tabular views with automatic padding and visible character alignment.

4. **`main.py` (Interactive Controller)**:
   - Robust input validation loops (never crashes on letters, blank inputs, or out-of-range choices).
   - Coordinates all 6 core menu features.

---

## How the Greedy Settlement Algorithm Works

Instead of settling every bill individually:
1. Each member's **Net Balance** is calculated:
   $$\text{Net Balance} = \text{Total Amount Paid} - \text{Total Share Consumed}$$
   - Positive ($+$): The member paid more than their share; they are **owed** money.
   - Negative ($-$) The member consumed more than they paid; they **owe** money.
   - Zero ($0$): The member is settled.

2. The **Greedy Cash-Flow Minimization Algorithm**:
   - **Step 1:** Identify the largest debtor (minimum negative balance $< -0.01$).
   - **Step 2:** Identify the largest creditor (maximum positive balance $> 0.01$).
   - **Step 3:** Settle an amount equal to $\min(|\text{debtor}|, \text{creditor})$.
   - **Step 4:** Update both balances and repeat until all debts are eliminated.
   - **Outcome:** Guarantees that at least one person's debt is cleared to zero at every step, minimizing the total number of peer-to-peer transactions.

---

## Core Features (Bizotic CP-007)

1. **[1] Create Group & Add Members:**
   - Register group names (e.g. "Trip to Goa 2026").
   - Add single members or comma-separated lists (`Alice, Bob, Charlie`).
   - Automatic case-insensitive duplicate rejection.

2. **[2] Add Shared Expense:**
   - Select payer by number or name.
   - Choose split participants (`all` or comma-separated indices `1, 3`).
   - Computes per-person share and displays confirmation summary.

3. **[3] View Member Net Balances:**
   - Visual ledger displaying Total Paid, Total Consumed, Net Balance, and status pills:
     - `▲ IS OWED (Gets Back)` (Green)
     - `▼ OWES (Must Pay)` (Red)
     - `✔ SETTLED` (Dim)

4. **[4] Generate Minimum Settlement Plan:**
   - Visual cash-flow transfer routes:
     `[#1]  Diana  ────────[ ₹ 3,500.00 ]────────❯  Alice`
   - Optimization metrics displaying total transactions saved.

5. **[5] Full Expense History:**
   - Chronological audit log of all recorded bills with participant counts and individual shares.

6. **[6] Save / Reload Data (JSON):**
   - Save session state to `data.json` or reload from disk anytime.
   - Automatic prompt to save unsaved changes upon exit.

---

## How to Run

### 1. Prerequisites
- Python 3.8 or higher.
- No external libraries required (pure Python standard library).

### 2. Clone and Start
```bash
git clone https://github.com/QUROOOOO/007-evensplit.git
cd 007-evensplit
python main.py
```
*(On systems where Python 3 is aliased, run `python3 main.py` or `python3.11 main.py`)*

### 3. Run Automated Tests
```bash
python -m unittest test_evensplit.py
```

---

## Team
- **Archak Aryan**
