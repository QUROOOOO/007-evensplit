# CP-007 EvenSplit: Group Expense Settlement Optimizer

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Standard Library Only](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)]()
[![Navigation](https://img.shields.io/badge/navigation-zero--flicker%20arrow--keys-green.svg)]()

## About the Project
When friends go on a trip or flatmates share expenses, different people pay for different bills—leading to a confusing chain of who owes whom. **EvenSplit** is a console-based expense manager and debt-simplification engine that tracks shared group expenses, calculates each member's real-time net balance, and resolves all debts using the **minimum possible number of payments**.

Built strictly with Python's standard library (`sys`, `time`, `json`, `math`, `os`, `msvcrt`), EvenSplit features zero-flicker interactive arrow-key navigation (OpenCode node-line style), live member appending, an edit engine, multi-file bill storage, and visual confirmation cards.

---

## Architecture & Code Structure

```
007-evensplit/
├── engine.py          # Core mathematical logic, debt minimization & edit engine
├── data_manager.py    # Multi-file bill persistence (saved_bills/ & data.json)
├── tui.py             # Zero-flicker buffer UI (arrow navigation, tables, card, spinner)
├── main.py            # Menu controller with keyboard events & header sync
├── test_evensplit.py  # Automated unit test suite (17 tests)
├── evensplit.cmd      # Direct command wrapper for Windows CMD
├── evensplit.ps1      # Direct PowerShell execution wrapper
├── saved_bills/       # Saved trips/bills directory
├── data.json          # Working bill storage file
└── README.md          # Project documentation
```

### Module Responsibilities

1. **`engine.py` (Core Calculations & Edit Engine)**:
   - `add_member(members, name)`: Validates non-empty names and enforces case-insensitive uniqueness.
   - `rename_member(members, expenses, old_name, new_name)`: Cascades name updates across all expense records.
   - `delete_member(members, expenses, name)`: Removes participant and recalculates split shares.
   - `record_expense(expenses, members, desc, amount, payer, participants)`: Validates positive amounts and computes per-person equal shares.
   - `update_expense(expenses, members, id, ...)`: Updates expense fields and recomputes shares.
   - `delete_expense(expenses, id)`: Removes an expense record.
   - `calculate_net_balances(members, expenses)`: Computes real-time `net = total_paid - total_consumed` for all members.
   - `compute_min_settlements(net_balances)`: Greedy Cash-Flow Minimization algorithm resolving debts in at most $N - 1$ transfers.

2. **`data_manager.py` (Multi-File Persistence)**:
   - Saves group records to `saved_bills/<slug>.json` and maintains `data.json`.
   - `list_saved_bills()`: Scans and presents all saved bills with group name, member counts, and total spends.

3. **`tui.py` (Zero-Flicker Terminal UI)**:
   - Zero-flicker rendering via ANSI escape buffers (`\033[?25l`, `\033[H`, `\033[K`) with no screen blink during arrow navigation.
   - Minimal header box and vertical connector node-line menu (`│`, `○`, `●`, `❯`).
   - Arrow-key navigation via `msvcrt`: `[↑/↓]` to navigate, `[Enter]` to select, `[Esc/q]` to cancel.
   - Multi-select participant toggles using `[Spacebar]` (`[✔]` / `[ ]`).
   - Visual Expense Confirmation Card with dynamic character padding.
   - Table alignment with wide characters/emojis and description truncation.
   - Color Hierarchy:
     - **Punchy Bright Green (`\033[92m`)**: Rails `│`, active node `●`, cursor `❯`, checked boxes `[✔]`, positive balance.
     - **Punchy Amber (`\033[38;5;220m`)**: EVENSPLIT title, active group banner, total spends.
     - **White (`\033[97m`)**: Reading text, member names, table headers.
     - **Dim Grey (`\033[90m`)**: Inactive nodes `○`, borders, descriptions.

4. **`main.py` (Interactive Controller)**:
   - Prominent group header sync showing group name, member count, and total spend in amber.
   - Live-appending member registration loop.
   - Universal Edit Engine (`Edit Recorded Data`).
   - Multi-file bill selection (`Open Saved Bill`).

---

## How to Run

### Direct Command Wrapper (Windows)
```cmd
evensplit
```
or in PowerShell:
```powershell
.\evensplit
```

### Python Command
```bash
python3.11 main.py
```

### Non-Interactive Demo Showcase
```bash
python3.11 main.py --demo
```

### Run Automated Unit Tests
```bash
python3.11 test_evensplit.py
```

---

## Team
- **Archak Aryan**
