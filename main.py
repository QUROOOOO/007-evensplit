"""main.py - Menu-driven controller with arrow-key navigation for EvenSplit (CP-007)."""

import sys
import data_manager
import engine
import tui

MENU_ITEMS = [
    ("Create Group & Add Members", "Setup group name and register members"),
    ("Add Shared Expense", "Record a bill and split among participants"),
    ("View Member Net Balances", "Real-time ledger: who owes and who is owed"),
    ("Generate Minimum Settlement Plan", "Greedy cash-flow debt minimization"),
    ("Full Expense History", "Chronological audit log of all bills"),
    ("Save / Reload Data (JSON)", "Persist state to data.json or reload"),
    ("Exit", "Close EvenSplit")
]


class EvenSplitApp:
    """Main application controller managing state and navigation."""

    def __init__(self):
        self.group_name = ""
        self.members = []
        self.expenses = []
        self.is_dirty = False

        if data_manager.data_file_exists():
            loaded_name, loaded_members, loaded_expenses = data_manager.load_data()
            if loaded_name or loaded_members:
                self.group_name = loaded_name
                self.members = loaded_members
                self.expenses = loaded_expenses

    def render_app_header(self):
        """Render top header and group state hint."""
        tui.render_header()
        if self.group_name:
            count = len(self.members)
            label = f"{count} member{'s' if count != 1 else ''}"
            print(f"  {tui.WHITE}{self.group_name}{tui.RESET}  {tui.GREY}•  {label}{tui.RESET}\n")
        else:
            tui.hint("(No group created yet. Select 'Create Group & Add Members' to begin)\n")

    def run(self):
        """Main application navigation loop."""
        selected_index = 0
        while True:
            try:
                choice = tui.select_menu(
                    MENU_ITEMS,
                    selected=selected_index,
                    header_fn=self.render_app_header
                )

                if choice == -1 or choice == 6:  # Esc/q or Exit
                    if self.handle_exit():
                        break
                    continue

                selected_index = choice

                if choice == 0:
                    self.handle_group_and_members()
                elif choice == 1:
                    self.handle_add_expense()
                elif choice == 2:
                    self.handle_view_balances()
                elif choice == 3:
                    self.handle_settlement_plan()
                elif choice == 4:
                    self.handle_expense_history()
                elif choice == 5:
                    self.handle_save_reload()

            except (KeyboardInterrupt, EOFError):
                if self.handle_exit():
                    break

    def handle_group_and_members(self):
        """Feature 1: Group name and member registration."""
        while True:
            tui.clear_screen()
            self.render_app_header()

            if not self.group_name:
                print(f"  {tui.WHITE}Create a New Expense Group{tui.RESET}\n")
                new_group = tui.prompt_input("Enter group name (e.g. Weekend Trip, Apartment 4B)")
                if new_group:
                    self.group_name = new_group
                    self.is_dirty = True
                    tui.success(f"Group '{self.group_name}' created.")
                    tui.pause()
                else:
                    return

            actions = ["Add Member(s)", "Rename Group", "Back to Main Menu"]
            action_idx = tui.select_one(
                actions,
                prompt=f"Group: {self.group_name} ({len(self.members)} members)",
                header_fn=self.render_app_header
            )

            if action_idx in (-1, 2):  # Back / Cancel
                return

            if action_idx == 0:  # Add member
                tui.clear_screen()
                self.render_app_header()
                tui.hint("Enter a single name or comma-separated names (e.g. Alice, Bob, Charlie).")
                raw = tui.prompt_input("Member name(s)")
                if raw:
                    names = [n.strip() for n in raw.split(",") if n.strip()]
                    added = 0
                    for name in names:
                        try:
                            m = engine.add_member(self.members, name)
                            tui.success(f"Added member: {m}")
                            added += 1
                        except ValueError as err:
                            tui.error(str(err))
                    if added > 0:
                        self.is_dirty = True
                tui.pause()

            elif action_idx == 1:  # Rename group
                tui.clear_screen()
                self.render_app_header()
                new_name = tui.prompt_input("New group name", default=self.group_name)
                if new_name:
                    self.group_name = new_name
                    self.is_dirty = True
                    tui.success(f"Group renamed to '{self.group_name}'")
                tui.pause()

    def handle_add_expense(self):
        """Feature 2: Record a shared expense with interactive selections."""
        tui.clear_screen()
        self.render_app_header()

        if len(self.members) < 2:
            tui.hint("Need at least 2 members to record a shared expense.")
            tui.hint("Select 'Create Group & Add Members' to add members first.")
            tui.pause()
            return

        desc = tui.prompt_input("Expense description (e.g. Dinner, Groceries)")
        if not desc:
            return

        amount = None
        while amount is None:
            raw_amt = tui.prompt_input(f"Total amount ({tui.CURRENCY})")
            if not raw_amt:
                return
            try:
                val = float(raw_amt)
                if val <= 0:
                    tui.error("Amount must be greater than zero.")
                    continue
                amount = val
            except ValueError:
                tui.error("Please enter a valid numeric amount.")

        payer_idx = tui.select_one(
            self.members,
            prompt="Select who paid for this expense:",
            header_fn=self.render_app_header
        )
        if payer_idx == -1:
            return
        payer = self.members[payer_idx]

        participants = tui.select_multi(
            self.members,
            prompt="Select participants sharing this bill:",
            header_fn=self.render_app_header
        )
        if not participants:
            return

        share = round(amount / len(participants), 2)
        tui.clear_screen()
        self.render_app_header()
        print(f"  {tui.WHITE}Expense Summary:{tui.RESET}")
        print(f"  {tui.GREY}Description :{tui.RESET} {tui.WHITE}{desc}{tui.RESET}")
        print(f"  {tui.GREY}Total Amount:{tui.RESET} {tui.WHITE}{tui.CURRENCY} {amount:,.2f}{tui.RESET}")
        print(f"  {tui.GREY}Paid By     :{tui.RESET} {tui.WHITE}{payer}{tui.RESET}")
        print(f"  {tui.GREY}Participants:{tui.RESET} {tui.WHITE}{', '.join(participants)} ({len(participants)}){tui.RESET}")
        print(f"  {tui.GREY}Each Shares :{tui.RESET} {tui.WHITE}{tui.CURRENCY} {share:,.2f}{tui.RESET}\n")

        confirm = tui.select_one(
            ["Yes, record expense", "Cancel"],
            prompt="Confirm and save this expense:",
            header_fn=self.render_app_header
        )
        if confirm == 0:
            tui.spinner("Recording expense...", 0.6)
            engine.record_expense(self.expenses, self.members, desc, amount, payer, participants)
            self.is_dirty = True
            tui.success("Expense recorded successfully.")
        else:
            tui.hint("Expense cancelled.")
        tui.pause()

    def handle_view_balances(self):
        """Feature 3: Display member net balance ledger."""
        tui.clear_screen()
        self.render_app_header()

        if not self.members:
            tui.hint("(No members registered yet)")
            tui.pause()
            return

        tui.spinner("Calculating balances...", 0.6)
        breakdown = engine.get_member_breakdown(self.members, self.expenses)
        tui.render_balances_table(breakdown)
        tui.pause()

    def handle_settlement_plan(self):
        """Feature 4: Run greedy minimization algorithm."""
        tui.clear_screen()
        self.render_app_header()

        if not self.members:
            tui.hint("(No members registered yet)")
            tui.pause()
            return

        if not self.expenses:
            tui.hint("(No expenses recorded yet. All accounts are settled)")
            tui.pause()
            return

        tui.spinner("Optimizing cash flows...", 0.6)
        net_balances = engine.calculate_net_balances(self.members, self.expenses)
        transfers = engine.compute_min_settlements(net_balances)
        tui.render_settlement_plan(transfers, net_balances)
        tui.pause()

    def handle_expense_history(self):
        """Feature 5: Full chronological expense log."""
        tui.clear_screen()
        self.render_app_header()

        if not self.expenses:
            tui.hint("(No expenses recorded yet)")
        else:
            tui.render_expense_history(self.expenses)
        tui.pause()

    def handle_save_reload(self):
        """Feature 6: Persist or reload JSON storage."""
        actions = [
            f"Save Data to {data_manager.DEFAULT_FILEPATH}",
            f"Reload Data from {data_manager.DEFAULT_FILEPATH}",
            "Back to Main Menu"
        ]
        choice = tui.select_one(
            actions,
            prompt="Data Persistence (JSON):",
            header_fn=self.render_app_header
        )

        if choice == 0:
            tui.spinner("Saving data...", 0.6)
            if data_manager.save_data(self.group_name, self.members, self.expenses):
                self.is_dirty = False
                tui.success(f"Data saved to {data_manager.DEFAULT_FILEPATH}.")
            else:
                tui.error("Failed to save data.")
            tui.pause()

        elif choice == 1:
            tui.spinner("Reloading data...", 0.6)
            name, members, expenses = data_manager.load_data()
            self.group_name = name
            self.members = members
            self.expenses = expenses
            self.is_dirty = False
            tui.success(f"Loaded '{self.group_name or 'Untitled'}' with {len(self.members)} members.")
            tui.pause()

    def handle_exit(self) -> bool:
        """Handle application exit with dirty-check prompt."""
        if self.is_dirty:
            tui.clear_screen()
            self.render_app_header()
            choice = tui.select_one(
                ["Save and exit", "Exit without saving", "Cancel"],
                prompt="You have unsaved changes:",
                header_fn=self.render_app_header
            )
            if choice == 0:
                data_manager.save_data(self.group_name, self.members, self.expenses)
                tui.success("Saved successfully.")
            elif choice in (-1, 2):
                return False

        tui.clear_screen()
        print(f"\n  {tui.WHITE}EvenSplit closed.{tui.RESET}\n")
        return True


def run_demo():
    """Non-interactive showcase of EvenSplit."""
    tui.clear_screen()
    tui.render_header()
    print(f"  {tui.GREEN}⚡ EVENSPLIT DEMO SHOWCASE{tui.RESET}\n")

    members = ["Alice", "Bob", "Charlie", "Diana"]
    expenses = [
        {"id": 1, "description": "Airbnb Villa", "amount": 12000.0, "payer": "Alice", "participants": members, "split_amount": 3000.0},
        {"id": 2, "description": "Seafood Dinner", "amount": 4000.0, "payer": "Bob", "participants": ["Alice", "Bob", "Charlie"], "split_amount": 1333.33},
        {"id": 3, "description": "Scooter Rentals", "amount": 1500.0, "payer": "Charlie", "participants": ["Bob", "Charlie", "Diana"], "split_amount": 500.0}
    ]

    print(f"  {tui.WHITE}Trip to Goa{tui.RESET}  {tui.GREY}•  4 members  •  3 bills (₹ 17,500.00){tui.RESET}\n")

    tui.hint("1. Expense History")
    tui.render_expense_history(expenses)
    print()

    tui.hint("2. Net Balances Ledger")
    breakdown = engine.get_member_breakdown(members, expenses)
    tui.render_balances_table(breakdown)
    print()

    tui.hint("3. Greedy Minimum Settlement Plan")
    net_balances = engine.calculate_net_balances(members, expenses)
    transfers = engine.compute_min_settlements(net_balances)
    tui.render_settlement_plan(transfers, net_balances)

    tui.success("Demo complete. Run without arguments for interactive mode.")
    print()


def main():
    """Entrypoint with CLI argument support."""
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("--demo", "-d"):
            run_demo()
            return
        elif arg in ("--test", "-t"):
            import unittest
            suite = unittest.defaultTestLoader.discover(".", pattern="test_*.py")
            runner = unittest.TextTestRunner(verbosity=2)
            runner.run(suite)
            return
        elif arg in ("--help", "-h"):
            print("EvenSplit (CP-007): Group Expense Settlement Optimizer")
            print("Usage: python main.py [OPTION]\n")
            print("  (no args)    Interactive arrow-key console application")
            print("  --demo, -d   Run non-interactive showcase")
            print("  --test, -t   Run automated unit tests")
            print("  --help, -h   Show help message")
            return

    app = EvenSplitApp()
    app.run()


if __name__ == "__main__":
    main()
