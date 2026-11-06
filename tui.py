"""tui.py - Zero-flicker terminal UI with arrow navigation and refined palette."""

import os
import re
import sys
import time
import unicodedata

# ---------------------------------------------------------------------------
# Terminal Setup & Refined 4-Color ANSI Palette
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
GREEN = "\033[92m"           # Point-line rails, cursor ❯, checked [✔]
BOLD_GREEN = "\033[1;92m"
AMBER = "\033[38;5;220m"     # EVENSPLIT title, group name, total bill sums
BOLD_AMBER = "\033[1;38;5;220m"
GREY = "\033[90m"            # Unselected nodes ○, descriptions, borders
CURRENCY = "₹"


# ---------------------------------------------------------------------------
# Visual Width & Emoji Handling
# ---------------------------------------------------------------------------
def visible_char_width(ch: str) -> int:
    """Calculate terminal column display width of a single character."""
    if ch in ("\ufe0e", "\ufe0f") or unicodedata.combining(ch):
        return 0
    w = unicodedata.east_asian_width(ch)
    if w in ("W", "F"):
        return 2
    cp = ord(ch)
    if (0x1F300 <= cp <= 0x1FAFF) or (0x2600 <= cp <= 0x27BF):
        return 2
    return 1


def visible_len(text: str) -> int:
    """Return visible terminal column width, ignoring ANSI escapes and counting emojis as 2."""
    clean = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)
    return sum(visible_char_width(ch) for ch in clean)


def truncate_visible(text: str, max_w: int = 15) -> str:
    """Truncate text to max visible columns, appending '...' if truncated."""
    clean = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)
    if visible_len(clean) <= max_w:
        return clean
    cur_w = 0
    res = []
    for ch in clean:
        cw = visible_char_width(ch)
        if cur_w + cw > max_w - 3:
            break
        res.append(ch)
        cur_w += cw
    return "".join(res) + "..."


def clear_screen():
    """Clear screen completely and move cursor to home (used on screen transitions)."""
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def show_cursor():
    """Ensure cursor is visible."""
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Keyboard Input (msvcrt on Windows)
# ---------------------------------------------------------------------------
def read_key() -> str:
    """Read a single interactive keypress with signal protection."""
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
        if ch in ("\x1b", "q", "Q", "\x03", "\x1a"):
            return "ESC"
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
            if ch in ("q", "Q", "\x03", "\x1a"):
                return "ESC"
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


# ---------------------------------------------------------------------------
# Visual Elements & Headers
# ---------------------------------------------------------------------------
def get_header_lines() -> list[str]:
    """Return lines for the bold ASCII art EvenSplit header."""
    return [
        f"{BOLD_AMBER}  ███████╗██╗   ██╗███████╗███╗   ██╗███████╗██████╗ ██╗     ██╗████████╗{RESET}",
        f"{BOLD_AMBER}  ██╔════╝██║   ██║██╔════╝████╗  ██║██╔════╝██╔══██╗██║     ██║╚══██╔══╝{RESET}",
        f"{BOLD_AMBER}  █████╗  ██║   ██║█████╗  ██╔██╗ ██║███████╗██████╔╝██║     ██║   ██║   {RESET}",
        f"{BOLD_AMBER}  ██╔══╝  ╚██╗ ██╔╝██╔══╝  ██║╚██╗██║╚════██║██╔═══╝ ██║     ██║   ██║   {RESET}",
        f"{BOLD_AMBER}  ███████╗ ╚████╔╝ ███████╗██║ ╚████║███████║██║     ███████╗██║   ██║   {RESET}",
        f"{BOLD_AMBER}  ╚══════╝  ╚═══╝  ╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝     ╚══════╝╚═╝   ╚═╝   {RESET}",
        f"  {WHITE}Group Expense Settlement Optimizer{RESET}",
        ""
    ]


def render_header():
    """Print the clean header box directly."""
    for line in get_header_lines():
        print(line)


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
    """Prompt user for standard text input with visible cursor."""
    show_cursor()
    def_str = f" {GREY}(default: {default}){RESET}" if default else ""
    try:
        val = input(f"  {GREEN}❯{RESET} {WHITE}{label}{RESET}{def_str}: ").strip()
        return default if not val and default is not None else val
    except (KeyboardInterrupt, EOFError):
        print()
        return ""


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
        show_cursor()


# ---------------------------------------------------------------------------
# Zero-Flicker Interactive Arrow Selection (Buffer-based)
# ---------------------------------------------------------------------------
def select_menu(items: list, selected: int = 0, header_fn=None, nav_help: str = None) -> int:
    """Zero-flicker OpenCode vertical connector node menu."""
    n = len(items)
    clear_screen()
    help_text = nav_help or "[↑/↓] Navigate   [Enter] Select   [Esc] Back"

    while True:
        buf = ["\033[?25l\033[H"]
        if header_fn:
            for line in header_fn():
                buf.append(line + "\033[K\n")

        buf.append(f"  {GREEN}│{RESET}\033[K\n")
        for i, (title, desc) in enumerate(items):
            if i == selected:
                cursor = f"{GREEN}❯ ●{RESET}"
                title_fmt = f"{BOLD_WHITE}{title:<34}{RESET}"
                desc_fmt = f"{GREY}{desc}{RESET}"
            else:
                cursor = f"  {GREY}○{RESET}"
                title_fmt = f"{WHITE}{title:<34}{RESET}"
                desc_fmt = f"{GREY}{desc}{RESET}"

            buf.append(f"{cursor}  {title_fmt}  {desc_fmt}\033[K\n")
            buf.append(f"  {GREEN}│{RESET}\033[K\n")

        buf.append(f"\n  {GREY}{help_text}{RESET}\033[K\n")
        buf.append("\033[J")

        sys.stdout.write("".join(buf))
        sys.stdout.flush()

        key = read_key()
        if key == "UP":
            selected = (selected - 1) % n
        elif key == "DOWN":
            selected = (selected + 1) % n
        elif key == "ENTER":
            show_cursor()
            return selected
        elif key in ("ESC", "q"):
            show_cursor()
            return -1


def select_one(items: list, selected: int = 0, prompt: str = "Select an option:", header_fn=None, nav_help: str = None) -> int:
    """Zero-flicker single selection list with node lines."""
    n = len(items)
    if n == 0:
        return -1
    clear_screen()
    help_text = nav_help or "[↑/↓] Navigate   [Enter] Select   [Esc] Back"

    while True:
        buf = ["\033[?25l\033[H"]
        if header_fn:
            for line in header_fn():
                buf.append(line + "\033[K\n")

        buf.append(f"  {WHITE}{prompt}{RESET}\033[K\n\n")
        buf.append(f"  {GREEN}│{RESET}\033[K\n")
        for i, item in enumerate(items):
            if i == selected:
                cursor = f"{GREEN}❯ ●{RESET}"
                item_fmt = f"{BOLD_WHITE}{str(item)}{RESET}"
            else:
                cursor = f"  {GREY}○{RESET}"
                item_fmt = f"{WHITE}{str(item)}{RESET}"

            buf.append(f"{cursor}  {item_fmt}\033[K\n")
            buf.append(f"  {GREEN}│{RESET}\033[K\n")

        buf.append(f"\n  {GREY}{help_text}{RESET}\033[K\n")
        buf.append("\033[J")

        sys.stdout.write("".join(buf))
        sys.stdout.flush()

        key = read_key()
        if key == "UP":
            selected = (selected - 1) % n
        elif key == "DOWN":
            selected = (selected + 1) % n
        elif key == "ENTER":
            show_cursor()
            return selected
        elif key in ("ESC", "q"):
            show_cursor()
            return -1


def select_multi(items: list, checked: list = None, prompt: str = "Select participants:", header_fn=None, nav_help: str = None) -> list:
    """Zero-flicker multi-select list with [✔] / [ ] toggled via Spacebar."""
    n = len(items)
    if n == 0:
        return []

    checked = [True] * n if checked is None else list(checked)
    selected = 0
    clear_screen()
    help_text = nav_help or "[↑/↓] Navigate   [Space] Toggle   [Enter] Confirm   [a] All/None   [Esc] Back"

    while True:
        buf = ["\033[?25l\033[H"]
        if header_fn:
            for line in header_fn():
                buf.append(line + "\033[K\n")

        buf.append(f"  {WHITE}{prompt}{RESET}\033[K\n\n")
        buf.append(f"  {GREEN}│{RESET}\033[K\n")
        for i, item in enumerate(items):
            box = f"{GREEN}[✔]{RESET}" if checked[i] else f"{GREY}[ ]{RESET}"
            if i == selected:
                cursor = f"{GREEN}❯ ●{RESET}"
                item_fmt = f"{BOLD_WHITE}{str(item)}{RESET}"
            else:
                cursor = f"  {GREY}○{RESET}"
                item_fmt = f"{WHITE}{str(item)}{RESET}"

            buf.append(f"{cursor}  {box} {item_fmt}\033[K\n")
            buf.append(f"  {GREEN}│{RESET}\033[K\n")

        buf.append(f"\n  {GREY}{help_text}{RESET}\033[K\n")
        buf.append("\033[J")

        sys.stdout.write("".join(buf))
        sys.stdout.flush()

        key = read_key()
        if key == "UP":
            selected = (selected - 1) % n
        elif key == "DOWN":
            selected = (selected + 1) % n
        elif key == "SPACE":
            checked[selected] = not checked[selected]
        elif key in ("a", "A"):
            all_on = all(checked)
            checked = [not all_on] * n
        elif key == "ENTER":
            chosen = [items[i] for i in range(n) if checked[i]]
            if not chosen:
                continue
            show_cursor()
            return chosen
        elif key in ("ESC", "q"):
            show_cursor()
            return None


# ---------------------------------------------------------------------------
# Visual Card on Expense Confirmation
# ---------------------------------------------------------------------------
def render_expense_card(desc: str, amount: float, payer: str, count: int, share: float):
    """Render a visual summary card for expense confirmation."""
    inner_w = 42
    title_str = truncate_visible(desc, 22)
    amt_str = f"{CURRENCY} {amount:,.2f}"
    split_str = f"{count} members ({CURRENCY} {share:,.2f} each)"

    lines = [
        f"  {GREY}Title:      {RESET} {WHITE}{title_str}{RESET}",
        f"  {GREY}Amount:     {RESET} {BOLD_AMBER}{amt_str}{RESET}",
        f"  {GREY}Paid By:    {RESET} {WHITE}{payer}{RESET}",
        f"  {GREY}Split With: {RESET} {WHITE}{split_str}{RESET}"
    ]

    header_text = "── Expense Summary "
    dashes = max(0, inner_w - len(header_text))
    print(f"  {GREY}╭{header_text}{'─' * dashes}╮{RESET}")
    for line in lines:
        pad = max(0, inner_w - visible_len(line))
        print(f"  {GREY}│{RESET}{line}{' ' * pad}{GREY}│{RESET}")
    print(f"  {GREY}╰{'─' * inner_w}╯{RESET}")
    print()


# ---------------------------------------------------------------------------
# Tabular Formatting with Emoji / Wide-Char Alignment
# ---------------------------------------------------------------------------
def render_table(headers: list, rows: list, alignments: list = None):
    """Render Unicode box table with proper wide-char padding."""
    num_cols = len(headers)
    alignments = ["L"] * num_cols if not alignments else alignments

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
        pad = max(0, w - visible_len(h))
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
        pad = max(0, total_w - visible_len(msg))
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
            net_str = f"{BOLD_GREEN}+{CURRENCY} {abs(net):,.2f}{RESET}"
            status_str = f"{BOLD_GREEN}▲ IS OWED{RESET}"
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
    """Render chronological expense log table with truncated descriptions and emoji alignment."""
    headers = ["#", "Description", "Paid By", "Amount", "Split With", "Each Share"]
    alignments = ["C", "L", "L", "R", "L", "R"]
    rows = []

    for exp in expenses:
        exp_id = str(exp.get("id", "-"))
        desc = truncate_visible(exp["description"], 15)
        payer = exp["payer"]
        amt = exp["amount"]
        parts = exp["participants"]
        split_amt = exp.get("split_amount", round(amt / len(parts), 2))

        parts_str = ", ".join(parts) if len(parts) <= 3 else f"{', '.join(parts[:2])} + {len(parts) - 2} more"

        rows.append([
            f"{GREY}{exp_id}{RESET}",
            f"{WHITE}{desc}{RESET}",
            f"{WHITE}{payer}{RESET}",
            f"{BOLD_AMBER}{CURRENCY} {amt:,.2f}{RESET}",
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

        tag = f"{BOLD_AMBER}{CURRENCY} {amt:,.2f}{RESET}"
        line = (
            f"  {GREY}[#{i}]{RESET}  "
            f"{WHITE}{debtor:<12}{RESET}  "
            f"{GREY}───────[{RESET} {tag} {GREY}]───────{RESET}{GREEN}❯{RESET}  "
            f"{WHITE}{creditor:<12}{RESET}"
        )
        print(line)
    print()
