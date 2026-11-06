"""tui.py - OpenCode-styled terminal UI with arrow-key navigation for EvenSplit."""

import os
import re
import sys
import time

# ---------------------------------------------------------------------------
# Terminal Setup & 4-Color ANSI Palette
# ---------------------------------------------------------------------------
if os.name == "nt":
    os.system("")
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

RESET = "\033[0m"
WHITE = "\033[97m"
BOLD_WHITE = "\033[1;97m"
GREEN = "\033[92m"           # Bright punchy green
BOLD_GREEN = "\033[1;92m"
GREY = "\033[90m"            # Dim grey
CURRENCY = "₹"


def visible_len(text: str) -> int:
    """Return visible character count excluding ANSI escape sequences."""
    return len(re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text))


def clear_screen():
    """Clear terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


# ---------------------------------------------------------------------------
# Keyboard Input (msvcrt on Windows)
# ---------------------------------------------------------------------------
def read_key() -> str:
    """
    Read a single interactive keypress.
    Returns: 'UP', 'DOWN', 'ENTER', 'SPACE', 'ESC', 'q', or raw char.
    """
    if os.name == "nt":
        import msvcrt
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            code = msvcrt.getwch()
            keys = {"H": "UP", "P": "DOWN", "K": "LEFT", "M": "RIGHT"}
            return keys.get(code, code)
        if ch in ("\r", "\n"):
            return "ENTER"
        if ch == " ":
            return "SPACE"
        if ch == "\x1b":
            return "ESC"
        if ch in ("q", "Q"):
            return "q"
        if ch == "\x03":
            raise KeyboardInterrupt
        return ch
    else:
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                ch2 = sys.stdin.read(1)
                if ch2 == "[":
                    ch3 = sys.stdin.read(1)
                    return {"A": "UP", "B": "DOWN", "C": "RIGHT", "D": "LEFT"}.get(ch3, "ESC")
                return "ESC"
            if ch in ("\r", "\n"):
                return "ENTER"
            if ch == " ":
                return "SPACE"
            if ch in ("q", "Q"):
                return "q"
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


# ---------------------------------------------------------------------------
# Spinner Animation
# ---------------------------------------------------------------------------
def spinner(message: str = "Processing...", duration: float = 0.8):
    """Display a lightweight braille dot spinner for the given duration."""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    start = time.time()
    i = 0

    sys.stdout.write("\033[?25l")
    sys.stdout.flush()
    try:
        while time.time() - start < duration:
            frame = frames[i % len(frames)]
            sys.stdout.write(f"\r  {GREEN}{frame}{RESET}  {GREY}{message}{RESET}")
            sys.stdout.flush()
            time.sleep(0.08)
            i += 1
    finally:
        sys.stdout.write("\r\033[K")
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()


# ---------------------------------------------------------------------------
# Header & Visual Elements
# ---------------------------------------------------------------------------
def render_header():
    """Render minimal, clean EvenSplit header box."""
    print(f"{GREY}╭────────────────────────────────────────╮{RESET}")
    print(f"{GREY}│{RESET}  {BOLD_WHITE}EVENSPLIT{RESET}                             {GREY}│{RESET}")
    print(f"{GREY}│{RESET}  {WHITE}Group Expense Settlement Optimizer{RESET}    {GREY}│{RESET}")
    print(f"{GREY}╰────────────────────────────────────────╯{RESET}")
    print()


def hint(message: str):
    """Print a muted grey helper message."""
    print(f"  {GREY}{message}{RESET}")


def success(message: str):
    """Print success notification with green checkmark."""
    print(f"  {GREEN}✔{RESET}  {WHITE}{message}{RESET}")


def error(message: str):
    """Print error message."""
    print(f"  {GREY}✖{RESET}  {WHITE}{message}{RESET}")


def pause():
    """Wait for user keypress to return."""
    print(f"\n  {GREY}Press any key to continue...{RESET}", end="", flush=True)
    try:
        read_key()
    except (KeyboardInterrupt, EOFError):
        pass
    print()


def prompt_input(label: str, default: str = None) -> str:
    """Prompt user for standard text input."""
    def_str = f" {GREY}(default: {default}){RESET}" if default else ""
    try:
        val = input(f"  {GREEN}❯{RESET} {WHITE}{label}{RESET}{def_str}: ").strip()
        return default if not val and default is not None else val
    except (KeyboardInterrupt, EOFError):
        print()
        return ""


# ---------------------------------------------------------------------------
# Interactive Arrow-Key Navigation (OpenCode Node-Line Style)
# ---------------------------------------------------------------------------
def select_menu(items: list, selected: int = 0, header_fn=None) -> int:
    """
    OpenCode-styled vertical connector node menu.
    items: list of (title, description) tuples.
    Returns: chosen index, or -1 on Esc/q.
    """
    n = len(items)
    while True:
        clear_screen()
        if header_fn:
            header_fn()

        print(f"  {GREY}│{RESET}")
        for i, (title, desc) in enumerate(items):
            if i == selected:
                cursor = f"{GREEN}❯ ●{RESET}"
                title_fmt = f"{BOLD_WHITE}{title:<34}{RESET}"
                desc_fmt = f"{GREY}{desc}{RESET}"
            else:
                cursor = f"  {GREY}○{RESET}"
                title_fmt = f"{WHITE}{title:<34}{RESET}"
                desc_fmt = f"{GREY}{desc}{RESET}"

            print(f"{cursor}  {title_fmt}  {desc_fmt}")
            print(f"  {GREY}│{RESET}")

        print(f"\n  {GREY}[↑/↓] Navigate   [Enter] Select   [Esc/q] Exit{RESET}")

        key = read_key()
        if key == "UP":
            selected = (selected - 1) % n
        elif key == "DOWN":
            selected = (selected + 1) % n
        elif key == "ENTER":
            return selected
        elif key in ("ESC", "q"):
            return -1


def select_one(items: list, selected: int = 0, prompt: str = "Select an option:", header_fn=None) -> int:
    """
    Interactive single-selection list with node lines.
    Returns: selected index, or -1 on cancel.
    """
    n = len(items)
    if n == 0:
        return -1

    while True:
        clear_screen()
        if header_fn:
            header_fn()

        print(f"  {WHITE}{prompt}{RESET}\n")
        print(f"  {GREY}│{RESET}")
        for i, item in enumerate(items):
            if i == selected:
                cursor = f"{GREEN}❯ ●{RESET}"
                item_fmt = f"{BOLD_WHITE}{str(item)}{RESET}"
            else:
                cursor = f"  {GREY}○{RESET}"
                item_fmt = f"{WHITE}{str(item)}{RESET}"

            print(f"{cursor}  {item_fmt}")
            print(f"  {GREY}│{RESET}")

        print(f"\n  {GREY}[↑/↓] Navigate   [Enter] Select   [Esc/q] Back{RESET}")

        key = read_key()
        if key == "UP":
            selected = (selected - 1) % n
        elif key == "DOWN":
            selected = (selected + 1) % n
        elif key == "ENTER":
            return selected
        elif key in ("ESC", "q"):
            return -1


def select_multi(items: list, checked: list = None, prompt: str = "Select participants:", header_fn=None) -> list:
    """
    Interactive multi-select list with [✔] / [ ] toggled via Spacebar.
    Returns: list of selected item values, or None if cancelled.
    """
    n = len(items)
    if n == 0:
        return []

    if checked is None:
        checked = [True] * n
    else:
        checked = list(checked)

    selected = 0
    while True:
        clear_screen()
        if header_fn:
            header_fn()

        print(f"  {WHITE}{prompt}{RESET}\n")
        print(f"  {GREY}│{RESET}")
        for i, item in enumerate(items):
            box = f"{GREEN}[✔]{RESET}" if checked[i] else f"{GREY}[ ]{RESET}"
            if i == selected:
                cursor = f"{GREEN}❯ ●{RESET}"
                item_fmt = f"{BOLD_WHITE}{str(item)}{RESET}"
            else:
                cursor = f"  {GREY}○{RESET}"
                item_fmt = f"{WHITE}{str(item)}{RESET}"

            print(f"{cursor}  {box} {item_fmt}")
            print(f"  {GREY}│{RESET}")

        print(f"\n  {GREY}[↑/↓] Navigate   [Space] Toggle   [Enter] Confirm   [a] All/None   [Esc/q] Cancel{RESET}")

        key = read_key()
        if key == "UP":
            selected = (selected - 1) % n
        elif key == "DOWN":
            selected = (selected + 1) % n
        elif key == "SPACE":
            checked[selected] = not checked[selected]
        elif key in ("a", "A"):
            all_checked = all(checked)
            checked = [not all_checked] * n
        elif key == "ENTER":
            chosen = [items[i] for i in range(n) if checked[i]]
            if not chosen:
                print(f"\n  {GREY}Please select at least one participant.{RESET}")
                time.sleep(0.8)
                continue
            return chosen
        elif key in ("ESC", "q"):
            return None


# ---------------------------------------------------------------------------
# Tabular Formatting
# ---------------------------------------------------------------------------
def render_table(headers: list, rows: list, alignments: list = None):
    """Render Unicode box table adhering to the 4-color palette."""
    num_cols = len(headers)
    if not alignments:
        alignments = ["L"] * num_cols

    widths = [visible_len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], visible_len(str(cell)))
    col_widths = [w + 2 for w in widths]

    # Top border
    print(f"  {GREY}╭{'┬'.join(['─' * w for w in col_widths])}╮{RESET}")

    # Header cells
    h_cells = []
    for i, h in enumerate(headers):
        w = col_widths[i]
        align = alignments[i]
        pad = w - visible_len(h)
        if align == "R":
            cell_str = f"{' ' * (pad - 1)}{BOLD_WHITE}{h}{RESET} "
        elif align == "C":
            lp = pad // 2
            cell_str = f"{' ' * lp}{BOLD_WHITE}{h}{RESET}{' ' * (pad - lp)}"
        else:
            cell_str = f" {BOLD_WHITE}{h}{RESET}{' ' * (pad - 1)}"
        h_cells.append(cell_str)
    print(f"  {GREY}│{RESET}{f'{GREY}│{RESET}'.join(h_cells)}{GREY}│{RESET}")

    # Header divider
    print(f"  {GREY}├{'┼'.join(['─' * w for w in col_widths])}┤{RESET}")

    # Data rows
    if not rows:
        total_w = sum(col_widths) + len(col_widths) - 1
        msg = f"{GREY}No records{RESET}"
        pad = total_w - visible_len(msg)
        print(f"  {GREY}│{RESET}{' ' * (pad // 2)}{msg}{' ' * (pad - pad // 2)}{GREY}│{RESET}")
    else:
        for row in rows:
            r_cells = []
            for i, cell in enumerate(row):
                w = col_widths[i]
                align = alignments[i]
                c_str = str(cell)
                pad = max(0, w - visible_len(c_str))
                if align == "R":
                    cell_str = f"{' ' * (pad - 1)}{c_str} "
                elif align == "C":
                    lp = pad // 2
                    cell_str = f"{' ' * lp}{c_str}{' ' * (pad - lp)}"
                else:
                    cell_str = f" {c_str}{' ' * (pad - 1)}"
                r_cells.append(cell_str)
            print(f"  {GREY}│{RESET}{f'{GREY}│{RESET}'.join(r_cells)}{GREY}│{RESET}")

    # Bottom border
    print(f"  {GREY}╰{'┴'.join(['─' * w for w in col_widths])}╯{RESET}")


def render_balances_table(breakdown: dict):
    """Render real-time Net Balances ledger."""
    headers = ["Member Name", "Total Paid", "Total Share", "Net Balance", "Status"]
    alignments = ["L", "R", "R", "R", "L"]
    rows = []

    for member, data in breakdown.items():
        paid = data["paid"]
        consumed = data["consumed"]
        net = data["net"]

        paid_str = f"{WHITE}{CURRENCY} {paid:,.2f}{RESET}"
        consumed_str = f"{WHITE}{CURRENCY} {consumed:,.2f}{RESET}"

        if net > 0.01:
            net_str = f"{GREEN}+{CURRENCY} {abs(net):,.2f}{RESET}"
            status_str = f"{GREEN}▲ IS OWED{RESET}"
        elif net < -0.01:
            net_str = f"{WHITE}-{CURRENCY} {abs(net):,.2f}{RESET}"
            status_str = f"{GREY}▼ OWES{RESET}"
        else:
            net_str = f"{GREY}{CURRENCY} 0.00{RESET}"
            status_str = f"{GREY}✔ SETTLED{RESET}"

        rows.append([
            f"{BOLD_WHITE}{member}{RESET}",
            paid_str,
            consumed_str,
            net_str,
            status_str
        ])

    render_table(headers, rows, alignments)


def render_expense_history(expenses: list):
    """Render chronological expense log table."""
    headers = ["#", "Description", "Paid By", "Amount", "Split With", "Each Share"]
    alignments = ["C", "L", "L", "R", "L", "R"]
    rows = []

    for exp in expenses:
        exp_id = str(exp.get("id", "-"))
        desc = exp["description"]
        payer = exp["payer"]
        amt = exp["amount"]
        parts = exp["participants"]
        split_amt = exp.get("split_amount", round(amt / len(parts), 2))

        parts_str = ", ".join(parts) if len(parts) <= 3 else f"{', '.join(parts[:2])} + {len(parts) - 2} more"

        rows.append([
            f"{GREY}{exp_id}{RESET}",
            f"{WHITE}{desc}{RESET}",
            f"{WHITE}{payer}{RESET}",
            f"{WHITE}{CURRENCY} {amt:,.2f}{RESET}",
            f"{GREY}{parts_str} ({len(parts)}){RESET}",
            f"{WHITE}{CURRENCY} {split_amt:,.2f}{RESET}"
        ])

    render_table(headers, rows, alignments)


def render_settlement_plan(transfers: list, net_balances: dict):
    """Render minimized cash-flow transfers."""
    if not transfers:
        print(f"  {GREEN}✔{RESET}  {WHITE}All group balances are settled. No transfers required.{RESET}\n")
        return

    print(f"  {GREY}Reduced complex group debts to {WHITE}{len(transfers)}{GREY} direct transfer(s):{RESET}\n")

    for i, t in enumerate(transfers, start=1):
        debtor = t["from"]
        creditor = t["to"]
        amt = t["amount"]

        tag = f"{WHITE}{CURRENCY} {amt:,.2f}{RESET}"
        line = (
            f"  {GREY}[#{i}]{RESET}  "
            f"{WHITE}{debtor:<12}{RESET}  "
            f"{GREY}───────[{RESET} {tag} {GREY}]───────{RESET}{GREEN}❯{RESET}  "
            f"{WHITE}{creditor:<12}{RESET}"
        )
        print(line)

    print()
