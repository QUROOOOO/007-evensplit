"""
tui.py - Terminal User Interface for EvenSplit
==============================================
Capstone CP-007: Group Expense Settlement Optimizer

Implements a Claude Code developer-tool terminal aesthetic:
  - Unicode box characters (╭, ─, ╮, │, ╰, ╯, ├, ┤, ┬, ┴, ┼)
  - ANSI styling: bold white headers, cyan/purple/dim accents
  - Badges, status pills, and visual debt transfer flowcards
  - 0.8-second braille spinner animation
  - Formatted tabular layouts for Expenses, Balances, and Settlements
"""

import os
import re
import sys
import time

# ---------------------------------------------------------------------------
# Terminal Setup & ANSI Escape Sequences
# ---------------------------------------------------------------------------
# Enable VT100 / ANSI escapes on Windows command prompt
if os.name == "nt":
    os.system("")
    # Ensure stdout handles UTF-8 characters cleanly
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

# Styling Palette (Claude Code Inspired)
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"

# Colors
WHITE = "\033[97m"
BOLD_WHITE = "\033[1;97m"
CYAN = "\033[36m"
BRIGHT_CYAN = "\033[1;96m"
BOLD_CYAN = "\033[1;36m"
PURPLE = "\033[38;5;141m"       # Claude purple
BOLD_PURPLE = "\033[1;38;5;141m"
GREEN = "\033[38;5;114m"        # Emerald green
BOLD_GREEN = "\033[1;38;5;114m"
AMBER = "\033[38;5;214m"        # Amber warning
BOLD_AMBER = "\033[1;38;5;214m"
RED = "\033[38;5;203m"          # Soft crimson
BOLD_RED = "\033[1;38;5;203m"
GRAY = "\033[38;5;242m"         # Subtle borders & dim text
DARK_GRAY = "\033[38;5;238m"
BLUE = "\033[38;5;75m"

# Status Badges
ICON_SUCCESS = f"{BOLD_GREEN}✔{RESET}"
ICON_ERROR = f"{BOLD_RED}✖{RESET}"
ICON_WARN = f"{BOLD_AMBER}▲{RESET}"
ICON_INFO = f"{BOLD_CYAN}ℹ{RESET}"
ICON_BULLET = f"{CYAN}●{RESET}"
ICON_ARROW = f"{PURPLE}❯{RESET}"

# Currency Symbol
CURRENCY = "₹"


def visible_len(text: str) -> int:
    """Calculates visible character length of a string by stripping ANSI escape codes."""
    clean = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)
    return len(clean)


def clear_screen():
    """Clears the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


# ---------------------------------------------------------------------------
# Spinner Animation
# ---------------------------------------------------------------------------
def spinner(message: str = "Processing...", duration: float = 0.8):
    """
    Displays a smooth braille dot spinner for the specified duration.

    Args:
        message (str): Text to show next to the spinner.
        duration (float): Seconds to animate (defaults to 0.8s).
    """
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    start_time = time.time()
    idx = 0

    # Hide cursor
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

    try:
        while time.time() - start_time < duration:
            frame = frames[idx % len(frames)]
            sys.stdout.write(f"\r  {BOLD_CYAN}{frame}{RESET}  {DIM}{message}{RESET}")
            sys.stdout.flush()
            time.sleep(0.08)
            idx += 1
    finally:
        # Show cursor again
        sys.stdout.write("\r\033[K")
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()


# ---------------------------------------------------------------------------
# Box and Banner Elements
# ---------------------------------------------------------------------------
def render_banner(width: int = 84):
    """Renders the top Claude Code-styled EvenSplit banner."""
    w = width
    top = f"{GRAY}╭{'─' * (w - 2)}╮{RESET}"
    bot = f"{GRAY}╰{'─' * (w - 2)}╯{RESET}"

    content1 = f"  {BOLD_CYAN}●{RESET} {BOLD_WHITE}EVENSPLIT{RESET} {DIM}007{RESET}  {GRAY}•{RESET}  {BOLD_PURPLE}Group Expense Settlement Optimizer{RESET}"
    content2 = f"  {DIM}Claude Code DevTool Aesthetic  •  Pure Python StdLib  •  Greedy MinFlow{RESET}"

    pad1 = max(0, w - 2 - visible_len(content1))
    pad2 = max(0, w - 2 - visible_len(content2))

    line1 = f"{GRAY}│{RESET}{content1}{' ' * pad1}{GRAY}│{RESET}"
    line2 = f"{GRAY}│{RESET}{content2}{' ' * pad2}{GRAY}│{RESET}"

    print(top)
    print(line1)
    print(line2)
    print(bot)


def render_status_bar(group_name: str, member_count: int, expense_count: int, total_spend: float):
    """Renders an inline status capsule bar with group statistics."""
    group_tag = f"{BOLD_WHITE}{group_name}{RESET}"
    members_tag = f"{CYAN}{member_count} member{'s' if member_count != 1 else ''}{RESET}"
    exp_tag = f"{PURPLE}{expense_count} record{'s' if expense_count != 1 else ''}{RESET}"
    spend_tag = f"{BOLD_GREEN}{CURRENCY} {total_spend:,.2f}{RESET}"

    pill = (
        f"  {GRAY}[{RESET} {BOLD}Group:{RESET} {group_tag} {GRAY}|{RESET} "
        f"{BOLD}Roster:{RESET} {members_tag} {GRAY}|{RESET} "
        f"{BOLD}Expenses:{RESET} {exp_tag} {GRAY}|{RESET} "
        f"{BOLD}Total Spend:{RESET} {spend_tag} {GRAY}]{RESET}"
    )
    print(pill)
    print()


def render_card(title: str, lines: list, width: int = 84, border_color: str = GRAY):
    """
    Renders a clean Unicode box card containing title and content lines.
    """
    inner_w = width - 2
    title_text = f"─ {BOLD_WHITE}{title}{border_color} "
    title_vis = visible_len(f"─ {title} ")
    top = f"{border_color}╭{title_text}{'─' * max(0, inner_w - title_vis)}╮{RESET}"
    print(top)
    for line in lines:
        v_len = visible_len(line)
        pad = max(0, width - 2 - v_len - 2)
        print(f"{border_color}│{RESET}  {line}{' ' * pad}{border_color}│{RESET}")
    print(f"{border_color}╰{'─' * (width - 2)}╯{RESET}")


def render_menu(width: int = 84):
    """Renders the main command menu in Claude Code style."""
    w = width
    title_text = f"─ {BOLD_CYAN}COMMAND MENU{RESET} "
    title_vis = visible_len("─ COMMAND MENU ")
    top = f"{GRAY}╭{title_text}{'─' * max(0, w - 2 - title_vis)}╮{RESET}"
    print(top)
    
    items = [
        ("1", "Create Group & Add Members", "Register members with uniqueness checks"),
        ("2", "Add Shared Expense", "Record bill & split among members"),
        ("3", "View Member Net Balances", "Ledger: who owes and who is owed"),
        ("4", "Generate Minimum Settlement Plan", "Greedy debt-minimization algorithm"),
        ("5", "Full Expense History", "Chronological audit log of bills"),
        ("6", "Save / Reload Data (JSON)", "Persist state to data.json or reload"),
        ("0", "Exit Application", "Save changes and close EvenSplit")
    ]

    for key, label, desc in items:
        key_badge = f"{BOLD_CYAN}[{key}]{RESET}"
        label_text = f"{BOLD_WHITE}{label:<33}{RESET}"
        desc_text = f"{DIM}{desc}{RESET}"
        content = f"  {key_badge} {label_text} {GRAY}│{RESET} {desc_text}"
        
        v_len = visible_len(content)
        pad = max(0, w - 2 - v_len)
        print(f"{GRAY}│{RESET}{content}{' ' * pad}{GRAY}│{RESET}")

    print(f"{GRAY}╰{'─' * (w - 2)}╯{RESET}")


# ---------------------------------------------------------------------------
# Feedback Alerts
# ---------------------------------------------------------------------------
def success(message: str):
    """Displays a success notification with green checkmark."""
    print(f"  {ICON_SUCCESS}  {BOLD_GREEN}{message}{RESET}")


def error(message: str):
    """Displays an error alert with red cross."""
    print(f"  {ICON_ERROR}  {BOLD_RED}{message}{RESET}")


def warning(message: str):
    """Displays an amber warning message."""
    print(f"  {ICON_WARN}  {BOLD_AMBER}{message}{RESET}")


def info(message: str):
    """Displays an informational note."""
    print(f"  {ICON_INFO}  {CYAN}{message}{RESET}")


def section_header(title: str, subtitle: str = None):
    """Renders a section header banner."""
    print()
    print(f"{BOLD_CYAN}─── {BOLD_WHITE}{title.upper()}{RESET} {BOLD_CYAN}────────────────────────────────────────────────{RESET}")
    if subtitle:
        print(f"    {DIM}{subtitle}{RESET}")
    print()


# ---------------------------------------------------------------------------
# Input Prompt Helpers
# ---------------------------------------------------------------------------
def prompt_input(prompt_label: str, default: str = None) -> str:
    """
    Renders a styled interactive input prompt.

    Args:
        prompt_label (str): Label explaining what to input.
        default (str, optional): Default value if user presses Enter.

    Returns:
        str: User input string.
    """
    def_text = f" {GRAY}(default: {default}){RESET}" if default else ""
    try:
        raw = input(f"  {PURPLE}❯{RESET} {BOLD_WHITE}{prompt_label}{RESET}{def_text}: ")
        trimmed = raw.strip()
        if not trimmed and default is not None:
            return default
        return trimmed
    except (KeyboardInterrupt, EOFError):
        print()
        return ""


def pause():
    """Pauses until user presses Enter."""
    try:
        input(f"\n  {DIM}Press [Enter] to return to menu...{RESET}")
    except (KeyboardInterrupt, EOFError):
        print()


# ---------------------------------------------------------------------------
# Tabular Displays
# ---------------------------------------------------------------------------
def render_table(headers: list, rows: list, alignments: list = None, col_widths: list = None):
    """
    Generic Unicode box table renderer with proper padding and alignment.

    Args:
        headers (list): List of column header strings.
        rows (list): List of row tuples/lists containing strings.
        alignments (list, optional): List of 'L', 'R', or 'C' per column. Defaults to 'L'.
        col_widths (list, optional): Explicit column widths. Computed if None.
    """
    num_cols = len(headers)
    if not alignments:
        alignments = ["L"] * num_cols

    # Compute optimal column widths
    if not col_widths:
        widths = [visible_len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], visible_len(str(cell)))
        # Add 2 spaces padding to each column
        col_widths = [w + 2 for w in widths]

    # Draw Top Border: ╭ ┬ ╮
    top_parts = [f"{'─' * w}" for w in col_widths]
    top_line = f"{GRAY}╭{'┬'.join(top_parts)}╮{RESET}"
    print(f"  {top_line}")

    # Draw Header Row: │ Header1 │ Header2 │
    header_cells = []
    for i, h in enumerate(headers):
        w = col_widths[i]
        align = alignments[i]
        v_h = visible_len(h)
        pad = w - v_h
        if align == "R":
            cell_str = f"{' ' * (pad - 1)}{BOLD_WHITE}{h}{RESET} "
        elif align == "C":
            left_pad = pad // 2
            right_pad = pad - left_pad
            cell_str = f"{' ' * left_pad}{BOLD_WHITE}{h}{RESET}{' ' * right_pad}"
        else:
            cell_str = f" {BOLD_WHITE}{h}{RESET}{' ' * (pad - 1)}"
        header_cells.append(cell_str)

    header_line = f"{GRAY}│{RESET}".join(header_cells)
    print(f"  {GRAY}│{RESET}{header_line}{GRAY}│{RESET}")

    # Draw Header Separator: ├ ┼ ┤
    mid_parts = [f"{'─' * w}" for w in col_widths]
    mid_line = f"{GRAY}├{'┼'.join(mid_parts)}┤{RESET}"
    print(f"  {mid_line}")

    # Draw Data Rows
    if not rows:
        total_w = sum(col_widths) + len(col_widths) - 1
        empty_msg = f"{DIM}No records found.{RESET}"
        pad = total_w - visible_len(empty_msg)
        print(f"  {GRAY}│{RESET}{' ' * (pad // 2)}{empty_msg}{' ' * (pad - pad // 2)}{GRAY}│{RESET}")
    else:
        for r_idx, row in enumerate(rows):
            row_cells = []
            for i, cell in enumerate(row):
                w = col_widths[i]
                align = alignments[i]
                cell_val = str(cell)
                v_len = visible_len(cell_val)
                pad = max(0, w - v_len)
                if align == "R":
                    cell_str = f"{' ' * (pad - 1)}{cell_val} "
                elif align == "C":
                    left_pad = pad // 2
                    right_pad = pad - left_pad
                    cell_str = f"{' ' * left_pad}{cell_val}{' ' * right_pad}"
                else:
                    cell_str = f" {cell_val}{' ' * (pad - 1)}"
                row_cells.append(cell_str)

            row_line = f"{GRAY}│{RESET}".join(row_cells)
            print(f"  {GRAY}│{RESET}{row_line}{GRAY}│{RESET}")

    # Draw Bottom Border: ╰ ┴ ╯
    bot_parts = [f"{'─' * w}" for w in col_widths]
    bot_line = f"{GRAY}╰{'┴'.join(bot_parts)}╯{RESET}"
    print(f"  {bot_line}")


def render_balances_table(breakdown: dict):
    """
    Renders a formatted Net Balances table showing member totals,
    net balance, and visual status pill (+owed, -owes, settled).

    Args:
        breakdown (dict): {member: {"paid": float, "consumed": float, "net": float}}
    """
    headers = ["Member Name", "Total Paid", "Total Share", "Net Balance", "Status"]
    alignments = ["L", "R", "R", "R", "L"]

    rows = []
    total_group_paid = 0.0

    for member, data in breakdown.items():
        paid = data["paid"]
        consumed = data["consumed"]
        net = data["net"]
        total_group_paid += paid

        paid_str = f"{CURRENCY} {paid:,.2f}"
        consumed_str = f"{CURRENCY} {consumed:,.2f}"

        if net > 0.01:
            net_str = f"{BOLD_GREEN}+{CURRENCY} {abs(net):,.2f}{RESET}"
            status_str = f"{BOLD_GREEN}▲ IS OWED{RESET} {DIM}(Gets Back){RESET}"
        elif net < -0.01:
            net_str = f"{BOLD_RED}-{CURRENCY} {abs(net):,.2f}{RESET}"
            status_str = f"{BOLD_RED}▼ OWES{RESET} {DIM}(Must Pay){RESET}"
        else:
            net_str = f"{GRAY}{CURRENCY} 0.00{RESET}"
            status_str = f"{GRAY}✔ SETTLED{RESET}"

        rows.append([
            f"{BOLD_WHITE}{member}{RESET}",
            paid_str,
            consumed_str,
            net_str,
            status_str
        ])

    render_table(headers, rows, alignments)
    print()
    print(f"  {DIM}Summary: {len(breakdown)} members tracked. Total group expenditure: {BOLD_WHITE}{CURRENCY} {total_group_paid:,.2f}{RESET}")


def render_expense_history(expenses: list):
    """
    Renders a formatted chronological audit table of all expenses.

    Args:
        expenses (list): List of expense dictionaries.
    """
    if not expenses:
        warning("No expenses have been recorded yet.")
        return

    headers = ["#", "Description", "Paid By", "Amount", "Split With", "Each Share"]
    alignments = ["C", "L", "L", "R", "L", "R"]

    rows = []
    total_amount = 0.0

    for exp in expenses:
        exp_id = str(exp.get("id", "-"))
        desc = exp["description"]
        payer = exp["payer"]
        amt = exp["amount"]
        participants = exp["participants"]
        split_amt = exp.get("split_amount", round(amt / len(participants), 2))
        total_amount += amt

        # Format participants display
        if len(participants) <= 3:
            parts_str = ", ".join(participants)
        else:
            parts_str = f"{', '.join(participants[:2])} + {len(participants) - 2} more"

        rows.append([
            f"{CYAN}{exp_id}{RESET}",
            f"{BOLD_WHITE}{desc}{RESET}",
            f"{PURPLE}{payer}{RESET}",
            f"{BOLD_WHITE}{CURRENCY} {amt:,.2f}{RESET}",
            f"{DIM}{parts_str} ({len(participants)}){RESET}",
            f"{GREEN}{CURRENCY} {split_amt:,.2f}{RESET}"
        ])

    render_table(headers, rows, alignments)
    print()
    print(f"  {DIM}Total {len(expenses)} bill{'s' if len(expenses) != 1 else ''} recorded. Aggregate: {BOLD_GREEN}{CURRENCY} {total_amount:,.2f}{RESET}")


def render_settlement_plan(transfers: list, net_balances: dict):
    """
    Renders the step-by-step debt minimization transfer plan
    with Claude Code visual arrows and metrics.

    Args:
        transfers (list): List of {"from": debtor, "to": creditor, "amount": val}
        net_balances (dict): Current net balances.
    """
    if not transfers:
        print()
        lines = [
            f"{BOLD_GREEN}✔ Perfect Financial Equilibrium!{RESET}",
            f"{DIM}All group balances are settled at {CURRENCY} 0.00.{RESET}",
            f"{DIM}No peer-to-peer transfers are required.{RESET}"
        ]
        render_card("SETTLEMENT STATUS", lines, border_color=GREEN)
        return

    total_settled_amount = sum(t["amount"] for t in transfers)
    debtors_count = sum(1 for bal in net_balances.values() if bal < -0.01)
    creditors_count = sum(1 for bal in net_balances.values() if bal > 0.01)

    print(f"  {ICON_INFO} {BOLD_WHITE}Optimization Metric:{RESET} {DIM}Reduced complex debts into {BOLD_PURPLE}{len(transfers)}{RESET}{DIM} direct transaction(s).{RESET}")
    print()

    w = 84
    title_text = f"─ {BOLD_PURPLE}OPTIMIZED MINIMUM SETTLEMENT PLAN{RESET} "
    title_vis = visible_len("─ OPTIMIZED MINIMUM SETTLEMENT PLAN ")
    top = f"{GRAY}╭{title_text}{'─' * max(0, w - 2 - title_vis)}╮{RESET}"
    print(top)
    
    sub_text = "  Step-by-step debt elimination routes:"
    pad_sub = max(0, w - 2 - visible_len(sub_text))
    print(f"{GRAY}│{RESET}{DIM}{sub_text}{RESET}{' ' * pad_sub}{GRAY}│{RESET}")
    print(f"{GRAY}│{' ' * (w - 2)}│{RESET}")

    for idx, t in enumerate(transfers, start=1):
        debtor = t["from"]
        creditor = t["to"]
        amount = t["amount"]

        # Transfer line format:
        # [#1]  Debtor  ──────────[ ₹ 150.00 ]──────────❯  Creditor
        step_badge = f"{BOLD_CYAN}[#{idx}]{RESET}"
        debtor_badge = f"{BOLD_RED}{debtor:<12}{RESET}"
        creditor_badge = f"{BOLD_GREEN}{creditor:<12}{RESET}"
        amount_tag = f"{BOLD_WHITE}{CURRENCY} {amount:,.2f}{RESET}"
        
        arrow_segment = f"{GRAY}────────{RESET}[ {amount_tag} ]{PURPLE}────────❯{RESET}"
        flow_line = f"  {step_badge}  {debtor_badge} {arrow_segment}  {creditor_badge}"

        v_len = visible_len(flow_line)
        pad = max(0, w - 2 - v_len)
        print(f"{GRAY}│{RESET}{flow_line}{' ' * pad}{GRAY}│{RESET}")

    print(f"{GRAY}│{' ' * (w - 2)}│{RESET}")
    summary_line = f"  {DIM}Total volume settled:{RESET} {BOLD_GREEN}{CURRENCY} {total_settled_amount:,.2f}{RESET}  {GRAY}•{RESET}  {DIM}Parties cleared: {debtors_count} debtor(s) / {creditors_count} creditor(s){RESET}"
    v_sum = visible_len(summary_line)
    pad_sum = max(0, w - 2 - v_sum)
    print(f"{GRAY}│{RESET}{summary_line}{' ' * pad_sum}{GRAY}│{RESET}")
    print(f"{GRAY}╰{'─' * (w - 2)}╯{RESET}")
