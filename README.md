# CP-007 EvenSplit: Group Expense Settlement Optimizer

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Standard Library Only](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)]()
[![License](https://img.shields.io/badge/architecture-modular-amber.svg)]()

---

## 1. Project Purpose

When friends go on a trip, flatmates split utilities, or colleagues dine out, multiple people often pay for different expenses on behalf of varying subsets of the group. 

In real life, this results in a chaotic web of peer-to-peer debts:
- Alice paid ₹ 1,200 for lunch shared by Alice, Bob, and Charlie.
- Bob paid ₹ 400 for taxis shared only by Bob and Charlie.
- Charlie paid ₹ 300 for dessert shared by everyone.

Trying to resolve these individually creates unnecessary friction, redundant bank transfers, and cyclic debts (where Alice owes Bob, Bob owes Charlie, and Charlie owes Alice).

**EvenSplit (CP-007)** is an algorithmic expense manager and debt-simplification engine. Its primary purpose is to track group expenses, maintain an exact real-time ledger of what each person paid versus consumed, and **compress the entire group's debts into the minimum possible number of direct transactions**.

---

## 2. What EvenSplit Does

- **Dynamic Group & Member Roster**:
  Setup a group name and register members on-the-fly with case-insensitive uniqueness validation.
- **Shared Expense Tracking with Quantities**:
  Record expenses with custom descriptions, payment attribution, and multi-selected participants. Includes an interactive item quantity stepper (`[Qty: ◄ 2 ►]`) with smart unit-price multiplication.
- **Real-Time Net Balance Ledger**:
  Instantly computes total money paid, total value consumed, and the resulting net balance for every group member.
- **Greedy Minimum Cash-Flow Settlement**:
  Eliminates cyclic debts and reduces complex group balances into a minimal, clean payment plan.
- **Chronological Expense History**:
  Detailed tabular audit log of all bills with payer attribution, participant counts, and per-person split amounts.
- **Universal In-Memory Edit Engine**:
  Edit group names, rename members (with automatic cascade across historical expenses), remove members safely, or edit/delete recorded bills.
- **Saved Bill Hub**:
  Auto-persists trips to `saved_bills/<slug>.json` and `data.json`, with a dedicated sub-console to reopen and audit past bills.
- **Zero-Flicker Terminal Experience**:
  Features a fluid beam-sweep intro logo animation, OpenCode-style vertical connector node menus, interactive arrow-key navigation, spacebar multi-select toggles, and ANSI Alternate Screen Buffer isolation.

---

## 3. Technical Working & Core Architecture

EvenSplit is built strictly with the Python Standard Library (`sys`, `time`, `json`, `math`, `os`, `ast`, `operator`, `unicodedata`, `msvcrt`), requiring zero third-party packages.

```
007-evensplit/
├── engine.py          # Pure mathematical calculations & debt minimization
├── data_manager.py    # Multi-file JSON persistence & directory scanning
├── tui.py             # ANSI buffer rendering, animations & keystroke listener
├── main.py            # State controller & interactive workflow loops
└── test_evensplit.py  # Automated unit test suite
```

### Module Responsibilities

| Module | Core Responsibility |
| :--- | :--- |
| **`engine.py`** | Computational kernel. Validates inputs, parses arithmetic strings via AST, computes equal shares, calculates net ledgers, and minimizes cash flows. |
| **`data_manager.py`** | Persistence layer. Serializes state to JSON, handles filesystem slugification, manages trip archives in `saved_bills/`, and cleans up stale files upon renaming. |
| **`tui.py`** | Presentation layer. Manages ANSI Alternate Screen Buffer, zero-flicker double-buffer string writes, column-width text truncation, emoji alignment, and raw keyboard decoding. |
| **`main.py`** | Orchestrator. Connects the UI and Engine, manages active session memory, routes commands, and triggers auto-persistence. |

---

## 4. Algorithmic Principles

### A. Net Balance Calculation
For any member $m \in M$, their net balance is defined as:

$$\text{Net}(m) = \text{Total Paid}(m) - \text{Total Consumed}(m)$$

Where:
- $\text{Total Paid}(m) = \sum_{e \in E, \text{payer}(e) = m} \text{Amount}(e)$
- $\text{Total Consumed}(m) = \sum_{e \in E, m \in \text{participants}(e)} \frac{\text{Amount}(e)}{|\text{participants}(e)|}$

Members with $\text{Net} > 0$ are **creditors** (owed money). Members with $\text{Net} < 0$ are **debtors** (owe money). The sum of all net balances across the group is mathematically zero:

$$\sum_{m \in M} \text{Net}(m) = 0$$

#### Floating-Point Remainder Balancing
When splitting indivisible amounts (such as ₹ 100 split equally among 3 members), simple rounding causes fractional cent errors ($33.33 \times 3 = 99.99$, leaving a ₹ 0.01 residual). EvenSplit computes the exact floating-point discrepancy and balances it against the primary share, guaranteeing that $\sum \text{Net}(m) = 0.00$ exactly.

---

### B. Greedy Cash-Flow Debt Minimization Algorithm
Rather than performing pairwise settlements ($O(N^2)$ transactions), EvenSplit uses a greedy two-pointer strategy that solves all debts in at most $N - 1$ direct payments:

1. **Classify**: Split all active group members into two pools based on their net balance:
   - **Debtors**: Members where $\text{Net}(m) \le -0.01$.
   - **Creditors**: Members where $\text{Net}(m) \ge +0.01$.
2. **Select Extremes**:
   - Find the largest debtor $D$ (minimum negative value).
   - Find the largest creditor $C$ (maximum positive value).
3. **Execute Transfer**:
   - Transfer amount: $T = \min(| \text{Net}(D) |, \text{Net}(C))$.
   - Record payment: $D \longrightarrow C : \text{₹ } T$.
4. **Update Balances**:
   - $\text{Net}(D) \leftarrow \text{Net}(D) + T$
   - $\text{Net}(C) \leftarrow \text{Net}(C) - T$
5. **Iterate**: Repeat steps 1–4 until all balances are settled within $\pm 0.01$.

Because at least one member (either the debtor or the creditor) is completely settled to zero during each step, the algorithm terminates in at most $N - 1$ steps.

---

### C. Safe Math Expression Parsing via AST
To allow users to type expressions directly into amount prompts (e.g., `10 * 4` or `(500 + 250) / 3`), EvenSplit uses Python's standard `ast` (Abstract Syntax Tree) module instead of unsafe `eval()`:

1. Parses the input into an AST node tree via `ast.parse(clean_str, mode="eval")`.
2. Recursively evaluates only whitelisted node types: `ast.Constant`, `ast.UnaryOp` (`+`, `-`), and `ast.BinOp` (`+`, `-`, `*`, `/`).
3. Explicitly rejects function calls, identifiers, imports, attribute lookups, or non-arithmetic operators.
4. Checks for division by zero and rejects negative or zero totals.

---

### D. Zero-Flicker Terminal Buffer Architecture
Console applications frequently suffer from screen tearing and scrollbar stack buildup when repeatedly clearing the screen. EvenSplit solves this using ANSI terminal controls:

1. **Alternate Screen Buffer (`\033[?1049h`)**:
   Switches the terminal to an isolated secondary buffer upon boot. When EvenSplit exits, it emits `\033[?1049l` to cleanly restore the user's previous shell scrollback with zero history pollution.
2. **Scrollback Purging (`\033[2J\033[3J\033[H`)**:
   Clears both the visible viewport and the scrollback memory buffer during view switches.
3. **In-Memory Frame Buffering**:
   Interactive menus render their entire visual state into an in-memory string list before emitting a single atomic `sys.stdout.write()` call, eliminating redraw flicker during rapid arrow-key navigation.
4. **East-Asian & Emoji Width Calculation**:
   Calculates visual column widths using `unicodedata.east_asian_width` and Unicode block inspection, guaranteeing that descriptions containing emojis (e.g. 🍔, 🌴) maintain perfectly aligned Unicode table borders.
