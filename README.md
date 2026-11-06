# CP-007 EvenSplit: Group Expense Settlement Optimizer

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Standard Library Only](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)]()
[![Navigation](https://img.shields.io/badge/navigation-zero--flicker%20arrow--keys-green.svg)]()

## About the Project
When friends go on a trip or flatmates share expenses, different people pay for different bills—leading to a confusing chain of who owes whom. **EvenSplit** is a console-based expense manager and debt-simplification engine that tracks shared group expenses, calculates each member's real-time net balance, and resolves all debts using the **minimum possible number of payments**.

Built strictly with Python's standard library (`sys`, `time`, `json`, `math`, `os`, `msvcrt`), EvenSplit features a bold amber ASCII header, zero-flicker interactive arrow-key navigation (OpenCode node-line style), a dedicated Saved Bill Hub, universal `Esc` back-navigation, live member appending, an edit engine, and visual confirmation cards.

---

## Architecture & Code Structure

```
007-evensplit/
├── engine.py          # Core mathematical logic, debt minimization & edit engine
├── data_manager.py    # Multi-file bill persistence (saved_bills/ & data.json)
├── tui.py             # Zero-flicker buffer UI (ASCII header, alternate buffer, tables, card)
├── main.py            # Menu controller with keyboard events, Bill Hub & header sync
├── test_evensplit.py  # Automated unit test suite (21 tests)
├── evensplit.cmd      # Direct command wrapper for Windows CMD
├── evensplit.ps1      # Direct PowerShell execution wrapper
├── saved_bills/       # Saved trips/bills directory
├── data.json          # Working bill storage file
└── README.md          # Project documentation
```

### Module Responsibilities

1. **`engine.py` (Core Calculations & Edit Engine)**:
   - `parse_amount(text)`: Safe AST parser supporting literals and math expressions (`10 * 4`, `25 + 30 + 15`).
   - `add_member(members, name)`: Validates non-empty names and enforces case-insensitive uniqueness.
   - `rename_member(members, expenses, old_name, new_name)`: Cascades name updates across all expense records.
   - `delete_member(members, expenses, name)`: Removes participant and recalculates split shares.
   - `record_expense(expenses, members, desc, amount, payer, participants)`: Validates positive amounts and computes per-person equal shares.
   - `update_expense(expenses, members, id, ...)`: Updates expense fields and recomputes shares.
   - `delete_expense(expenses, id)`: Removes an expense record.
   - `calculate_net_balances(members, expenses)`: Computes real-time `net = total_paid - total_consumed` for all members.
   - `compute_min_settlements(net_balances)`: Greedy Cash-Flow Minimization algorithm resolving debts in at most $N - 1$ transfers.

2. **`data_manager.py` (Multi-File Persistence)**:
   - Auto-saves group records to both `saved_bills/<slug>.json` and primary `data.json`.
   - Cleans up stale slug files in `saved_bills/` upon group renaming.
   - `list_saved_bills()`: Dynamically scans and presents all saved bills with group name, member counts, and total spends.

3. **`tui.py` (Zero-Flicker Terminal UI)**:
   - Bold ASCII block header for **EVENSPLIT** in bright amber (`\033[38;5;220m`).
   - Alternate Screen Buffer (`\033[?1049h`/`\033[?1049l`) and scrollback clearing (`\033[3J`) to eliminate terminal buffer stacking.
   - Zero-flicker rendering via ANSI escape buffers (`\033[?25l`, `\033[H`, `\033[K`) with no screen blink during arrow navigation.
   - OpenCode vertical connector node-line menu (`│`, `○`, `●`, `❯`).
   - Arrow-key navigation via `msvcrt`: `[↑/↓]` to navigate, `[Enter]` to select, `[Esc]` to go back.
   - Multi-select participant toggles using `[Spacebar]` (`[✔]` / `[ ]`).
   - Visual Expense Confirmation Card rendered directly above prompts on every frame.
   - Table alignment with wide characters/emojis and description truncation.
   - Keystroke & signal protection (`Ctrl+C` / `Ctrl+Z` safely intercepted).

4. **`main.py` (Interactive Controller)**:
   - Fresh startup state: boots into clean session memory without auto-loading previous sessions.
   - Inline math calculator in amount prompts with instant evaluation feedback (`= ₹ 40.00`).
   - Auto-persistence across all user actions (group creation, member adds/edits, expense additions/modifications).
   - Streamlined first-time group creation: prompts directly for group name, followed immediately by live member entry.
   - Dedicated **Saved Bill Hub**: opens any bill from `saved_bills/` into an isolated exploration sub-console.
   - Universal `Esc` back-navigation across all views and sub-menus.

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
