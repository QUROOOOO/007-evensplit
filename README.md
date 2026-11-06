# CP-007 EvenSplit: Group Expense Settlement Optimizer

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Standard Library Only](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)]()
[![Navigation](https://img.shields.io/badge/navigation-arrow--keys-green.svg)]()

## About the Project
When friends go on a trip or flatmates share expenses, different people pay for different bills—leading to a confusing chain of who owes whom. **EvenSplit** is a console-based expense manager and debt-simplification engine that tracks shared group expenses, calculates each member's real-time net balance, and resolves all debts using the **minimum possible number of payments**.

Built strictly with Python's standard library (`sys`, `time`, `json`, `math`, `os`, `msvcrt`), EvenSplit features interactive arrow-key navigation (OpenCode node-line style) and a refined 4-color palette.

---

## Architecture & Code Structure

```
007-evensplit/
├── engine.py          # Core mathematical logic & greedy cash-flow algorithm
├── data_manager.py    # Local JSON persistence (data.json)
├── tui.py             # OpenCode-styled terminal UI (arrow-key navigation, tables, spinner)
├── main.py            # Menu-driven controller with keyboard events
├── test_evensplit.py  # Automated unit test suite
├── evensplit.cmd      # Direct command wrapper for Windows CMD
├── evensplit.ps1      # Direct PowerShell execution wrapper
├── data.json          # Persistent JSON storage file (fresh empty state)
└── README.md          # Project documentation
```

### Module Responsibilities

1. **`engine.py` (Core Calculations)**:
   - `add_member(members, name)`: Validates non-empty names and enforces case-insensitive uniqueness.
   - `record_expense(expenses, members, desc, amount, payer, participants)`: Validates positive amounts and computes per-person equal shares.
   - `calculate_net_balances(members, expenses)`: Computes real-time `net = total_paid - total_consumed` for all members.
   - `compute_min_settlements(net_balances)`: Greedy Cash-Flow Minimization algorithm resolving debts in at most $N - 1$ transfers.

2. **`data_manager.py` (Persistence)**:
   - Reads and writes group name, member list, and expense history to `data.json`.
   - Returns safe defaults on missing or corrupted files.

3. **`tui.py` (Terminal User Interface)**:
   - Minimal header box and vertical connector node-line menu (`│`, `○`, `●`, `❯`).
   - Arrow-key navigation via `msvcrt`: `[↑/↓]` to navigate, `[Enter]` to select, `[Esc/q]` to cancel.
   - Multi-select participant toggles using `[Spacebar]` (`[✔]` / `[ ]`).
   - 4-Color Palette: Crisp White text, Bright Green accents, Dim Grey lines/borders, Black background.
   - 0.8-second braille dot spinner (`⠋ ⠙ ⠹ ...`).

4. **`main.py` (Interactive Controller)**:
   - Manages state, graceful empty-group hints, and keyboard-driven sub-menus.

---

## How the Greedy Settlement Algorithm Works

Instead of settling every bill individually:
1. Each member's **Net Balance** is calculated:
   $$\text{Net Balance} = \text{Total Amount Paid} - \text{Total Share Consumed}$$
   - Positive ($+$): The member is **owed** money.
   - Negative ($-$) The member **owes** money.
   - Zero ($0$): The member is settled.

2. The **Greedy Cash-Flow Minimization Algorithm**:
   - Match the largest debtor ($\text{balance} < -0.01$) with the largest creditor ($\text{balance} > 0.01$).
   - Transfer $\min(|\text{debtor}|, \text{creditor})$ from debtor to creditor.
   - Update both balances and repeat until all debts are cleared.

---

## How to Run

### Option 1: Direct Execution Wrapper (Recommended on Windows)
```cmd
evensplit
```
or in PowerShell:
```powershell
.\evensplit
```

### Option 2: Python Command
```bash
python3.11 main.py
```

### Visual Demo Showcase
```bash
python3.11 main.py --demo
```

### Run Automated Tests
```bash
python3.11 test_evensplit.py
```

---

## Team
- **Archak Aryan**
