"""main.py - Menu controller with zero-flicker navigation, Saved Bill Hub, and edit engine for EvenSplit (CP-007)."""

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
    ("Edit Recorded Data", "Modify group name, members, or expenses"),
    ("Open Saved Bill", "Load and explore saved bills in Bill Hub"),
    ("Save Data (JSON)", "Persist state to saved_bills/ and data.json"),
    ("Exit", "Close EvenSplit")
]


class EvenSplitApp:
    """Main application controller managing state and zero-flicker UI flows."""

    def __init__(self):
        # Fresh startup state: no auto-loading
        self.group_name = ""
        self.members = []
        self.expenses = []
        self.is_dirty = False

    def render_app_header(self) -> list[str]:
        """Return header lines with group status banner."""
        lines = tui.get_header_lines()
        if self.group_name:
            count = len(self.members)
            label = f"{count} member{'s' if count != 1 else ''}"
            total = sum(e.get("amount", 0.0) for e in self.expenses)
            spend_tag = f"{tui.CURRENCY} {total:,.2f}"
            lines.append(
                f"  {tui.BOLD_AMBER}{self.group_name}{tui.RESET}  "
                f"{tui.GREY}•{tui.RESET}  {tui.WHITE}{label}{tui.RESET}  "
                f"{tui.GREY}•{tui.RESET}  {tui.BOLD_AMBER}{spend_tag}{tui.RESET}"
            )
            lines.append("")
        else:
            lines.append(f"  {tui.GREY}(No active group. Create a new group or open a saved bill){tui.RESET}")
            lines.append("")
        return lines

    def run(self):
        """Zero-flicker main menu loop with signal protection."""
        selected_index = 0
        while True:
            try:
                choice = tui.select_menu(
                    MENU_ITEMS,
                    selected=selected_index,
                    header_fn=self.render_app_header,
                    nav_help="[↑/↓] Navigate   [Enter] Select   [Esc] Exit"
                )

                if choice == -1 or choice == 8:
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
                    self.handle_edit_engine()
                elif choice == 6:
                    self.handle_open_saved_bill()
                elif choice == 7:
                    self.handle_save_data()

            except (KeyboardInterrupt, EOFError):
                continue

    def live_add_members(self, header_fn=None):
        """Live appending member registration loop with immediate node display."""
        hdr = header_fn or self.render_app_header
        while True:
            tui.clear_screen()
            for line in hdr():
                print(line)

            print(f"  {tui.WHITE}Group Members:{tui.RESET}")
            if not self.members:
                print(f"  {tui.GREY}(No members registered yet){tui.RESET}")
            else:
                for m in self.members:
                    print(f"  {tui.GREEN}│{tui.RESET}  {tui.GREEN}●{tui.RESET} {tui.WHITE}{m}{tui.RESET}")
            print(f"  {tui.GREEN}│{tui.RESET}\n")

            name = tui.prompt_input("Enter member name (or press Enter to finish)")
            if not name:
                break

            parts = [p.strip() for p in name.split(",") if p.strip()]
            for p in parts:
                try:
                    engine.add_member(self.members, p)
                    self.is_dirty = True
                except ValueError as err:
                    print(f"  {tui.GREY}✖{tui.RESET}  {tui.WHITE}{err}{tui.RESET}")
                    tui.pause()

    def handle_group_and_members(self):
        """Feature 1: Streamlined group creation or roster management."""
        if not self.group_name:
            tui.clear_screen()
            for line in self.render_app_header():
                print(line)
            print(f"  {tui.WHITE}Create a New Expense Group{tui.RESET}\n")
            new_group = tui.prompt_input("Enter Group Name (e.g. Kanak bday, Goa Trip)")
            if not new_group:
                return
            self.group_name = new_group
            self.is_dirty = True
            self.live_add_members()
            return

        while True:
            actions = ["Add Member(s)", "Rename Group"]
            action_idx = tui.select_one(
                actions,
                prompt=f"Group: {self.group_name} ({len(self.members)} members)",
                header_fn=self.render_app_header
            )

            if action_idx == -1:
                return

            if action_idx == 0:
                self.live_add_members()
            elif action_idx == 1:
                tui.clear_screen()
                for line in self.render_app_header():
                    print(line)
                new_name = tui.prompt_input("New group name", default=self.group_name)
                if new_name and new_name != self.group_name:
                    self.group_name = new_name
                    self.is_dirty = True
                    tui.success(f"Group renamed to '{self.group_name}'.")
                    tui.pause()

    def handle_add_expense(self):
        """Feature 2: Record a shared expense with visual confirmation card."""
        tui.clear_screen()
        for line in self.render_app_header():
            print(line)

        if len(self.members) < 2:
            tui.hint("Need at least 2 members to record a shared expense.")
            tui.hint("Select 'Create Group & Add Members' to add members first.")
            tui.pause()
            return

        desc = tui.prompt_input("Expense description (e.g. Starters, Villa Booking)")
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
        for line in self.render_app_header():
            print(line)
        tui.render_expense_card(desc, amount, payer, len(participants), share)

        confirm = tui.select_one(
            ["Yes, record expense", "Cancel"],
            prompt="Confirm and save this expense:",
            header_fn=self.render_app_header
        )
        if confirm == 0:
            tui.spinner("Recording expense...", 0.6)
            engine.record_expense(self.expenses, self.members, desc, amount, payer, participants)
            self.is_dirty = True
            tui.clear_screen()
            for line in self.render_app_header():
                print(line)
            tui.success("Expense recorded successfully.")
        else:
            tui.hint("Expense cancelled.")
        tui.pause()

    def handle_view_balances(self, header_fn=None):
        """Feature 3: Display member net balance ledger."""
        hdr = header_fn or self.render_app_header
        tui.clear_screen()
        for line in hdr():
            print(line)

        if not self.members:
            tui.hint("(No members registered yet)")
            tui.pause()
            return

        tui.spinner("Calculating balances...", 0.5)
        breakdown = engine.get_member_breakdown(self.members, self.expenses)
        tui.render_balances_table(breakdown)
        tui.pause()

    def handle_settlement_plan(self, header_fn=None):
        """Feature 4: Run greedy cash-flow minimization algorithm."""
        hdr = header_fn or self.render_app_header
        tui.clear_screen()
        for line in hdr():
            print(line)

        if not self.members:
            tui.hint("(No members registered yet)")
            tui.pause()
            return

        if not self.expenses:
            tui.hint("(No expenses recorded yet. All accounts are settled)")
            tui.pause()
            return

        tui.spinner("Optimizing cash flows...", 0.5)
        net_balances = engine.calculate_net_balances(self.members, self.expenses)
        transfers = engine.compute_min_settlements(net_balances)
        tui.render_settlement_plan(transfers, net_balances)
        tui.pause()

    def handle_expense_history(self, header_fn=None):
        """Feature 5: Chronological expense log with emoji width alignment."""
        hdr = header_fn or self.render_app_header
        tui.clear_screen()
        for line in hdr():
            print(line)

        if not self.expenses:
            tui.hint("(No expenses recorded yet)")
        else:
            tui.render_expense_history(self.expenses)
        tui.pause()

    def handle_edit_engine(self, header_fn=None):
        """Feature 6: Universal Edit Engine for group, members, and expenses."""
        hdr = header_fn or self.render_app_header
        while True:
            actions = [
                "Edit Group Name",
                "Edit / Add / Remove Members",
                "Edit / Delete an Expense"
            ]
            choice = tui.select_one(actions, prompt="Universal Edit Engine:", header_fn=hdr)
            if choice == -1:
                return

            if choice == 0:
                tui.clear_screen()
                for line in hdr():
                    print(line)
                new_name = tui.prompt_input("Enter new group name", default=self.group_name)
                if new_name and new_name != self.group_name:
                    self.group_name = new_name
                    self.is_dirty = True
                    tui.success(f"Group name updated to '{self.group_name}'.")
                tui.pause()

            elif choice == 1:
                self.handle_edit_members(header_fn=hdr)

            elif choice == 2:
                self.handle_edit_expenses(header_fn=hdr)

    def handle_edit_members(self, header_fn=None):
        """Sub-menu for editing member list."""
        hdr = header_fn or self.render_app_header
        while True:
            actions = ["Add Member(s)", "Rename a Member", "Remove a Member"]
            c = tui.select_one(actions, prompt="Member Management:", header_fn=hdr)
            if c == -1:
                return

            if c == 0:
                self.live_add_members(header_fn=hdr)
            elif c == 1:
                if not self.members:
                    tui.clear_screen()
                    tui.hint("No members to rename.")
                    tui.pause()
                    continue
                m_idx = tui.select_one(self.members, prompt="Select member to rename:", header_fn=hdr)
                if m_idx != -1:
                    old_m = self.members[m_idx]
                    tui.clear_screen()
                    for line in hdr():
                        print(line)
                    new_m = tui.prompt_input(f"Enter new name for '{old_m}'")
                    if new_m:
                        try:
                            engine.rename_member(self.members, self.expenses, old_m, new_m)
                            self.is_dirty = True
                            tui.success(f"Renamed '{old_m}' to '{new_m}'.")
                        except ValueError as err:
                            tui.error(str(err))
                    tui.pause()
            elif c == 2:
                if not self.members:
                    tui.clear_screen()
                    tui.hint("No members to remove.")
                    tui.pause()
                    continue
                m_idx = tui.select_one(self.members, prompt="Select member to remove:", header_fn=hdr)
                if m_idx != -1:
                    target = self.members[m_idx]
                    tui.clear_screen()
                    for line in hdr():
                        print(line)
                    try:
                        engine.delete_member(self.members, self.expenses, target)
                        self.is_dirty = True
                        tui.success(f"Removed member '{target}'.")
                    except ValueError as err:
                        tui.error(str(err))
                    tui.pause()

    def handle_edit_expenses(self, header_fn=None):
        """Sub-menu for modifying or deleting expenses."""
        hdr = header_fn or self.render_app_header
        while True:
            if not self.expenses:
                tui.clear_screen()
                for line in hdr():
                    print(line)
                tui.hint("No expenses recorded to edit.")
                tui.pause()
                return

            labels = [
                f"#{e.get('id', i+1)} {tui.truncate_visible(e['description'], 16)} - {tui.CURRENCY} {e['amount']:,.2f} ({e['payer']})"
                for i, e in enumerate(self.expenses)
            ]

            idx = tui.select_one(labels, prompt="Select an expense to modify:", header_fn=hdr)
            if idx == -1:
                return

            target = self.expenses[idx]
            exp_actions = [
                f"Edit Description ({tui.truncate_visible(target['description'], 16)})",
                f"Edit Amount ({tui.CURRENCY} {target['amount']:,.2f})",
                f"Edit Payer ({target['payer']})",
                f"Edit Participants ({len(target['participants'])} members)",
                "Delete This Expense"
            ]
            action = tui.select_one(exp_actions, prompt=f"Modify Expense #{target.get('id', idx+1)}:", header_fn=hdr)
            if action == -1:
                continue

            if action == 0:
                tui.clear_screen()
                for line in hdr():
                    print(line)
                new_desc = tui.prompt_input("New description", default=target["description"])
                if new_desc:
                    engine.update_expense(self.expenses, self.members, target["id"], desc=new_desc)
                    self.is_dirty = True
                    tui.success("Description updated.")
                tui.pause()
            elif action == 1:
                tui.clear_screen()
                for line in hdr():
                    print(line)
                new_amt = tui.prompt_input(f"New amount in {tui.CURRENCY}", default=str(target["amount"]))
                try:
                    engine.update_expense(self.expenses, self.members, target["id"], amount=float(new_amt))
                    self.is_dirty = True
                    tui.success("Amount updated.")
                except ValueError as err:
                    tui.error(str(err))
                tui.pause()
            elif action == 2:
                p_idx = tui.select_one(self.members, prompt="Select new payer:", header_fn=hdr)
                if p_idx != -1:
                    engine.update_expense(self.expenses, self.members, target["id"], payer=self.members[p_idx])
                    self.is_dirty = True
                    tui.success("Payer updated.")
                tui.pause()
            elif action == 3:
                pre = [m in target["participants"] for m in self.members]
                parts = tui.select_multi(self.members, checked=pre, prompt="Select participants:", header_fn=hdr)
                if parts:
                    engine.update_expense(self.expenses, self.members, target["id"], participants=parts)
                    self.is_dirty = True
                    tui.success("Participants updated.")
                tui.pause()
            elif action == 4:
                confirm = tui.select_one(["Yes, delete expense", "Cancel"], prompt="Are you sure you want to delete this expense?", header_fn=hdr)
                if confirm == 0:
                    engine.delete_expense(self.expenses, target["id"])
                    self.is_dirty = True
                    tui.success("Expense deleted.")
                tui.pause()

    def handle_open_saved_bill(self):
        """Feature 7: Open and load a bill from saved_bills/ directory into dedicated Bill Hub."""
        while True:
            tui.clear_screen()
            bills = data_manager.list_saved_bills()
            if not bills:
                for line in self.render_app_header():
                    print(line)
                tui.hint(f"No saved bills found in '{data_manager.SAVED_BILLS_DIR}/'.")
                tui.pause("Press Esc or any key to return...")
                return

            options = [
                f"{b['group_name']}  {tui.GREY}•  {b['members_count']} members  •  {tui.CURRENCY} {b['total_spend']:,.2f}  ({b['filename']}){tui.RESET}"
                for b in bills
            ]

            choice = tui.select_one(
                options,
                prompt="Select a saved bill to open:",
                header_fn=self.render_app_header,
                nav_help="[↑/↓] Navigate   [Enter] Open   [Esc] Back"
            )
            if choice == -1:
                return

            selected_bill = bills[choice]
            tui.spinner(f"Loading '{selected_bill['group_name']}'...", 0.4)
            name, members, expenses = data_manager.load_data(selected_bill["filepath"])
            self.group_name = name
            self.members = members
            self.expenses = expenses
            self.is_dirty = False

            # Launch Dedicated Bill Hub sub-console
            self.run_saved_bill_hub()

    def run_saved_bill_hub(self):
        """Dedicated sub-console for exploring and editing an active saved bill."""
        hub_items = [
            ("View Member Net Balances", "Real-time ledger: who owes and who is owed"),
            ("Generate Minimum Settlement Plan", "Greedy cash-flow debt minimization"),
            ("Full Expense History", "Chronological audit log of all bills"),
            ("Edit Recorded Data", "Modify group name, members, or expenses")
        ]

        def hub_header() -> list[str]:
            lines = tui.get_header_lines()
            count = len(self.members)
            total = sum(e.get("amount", 0.0) for e in self.expenses)
            spend_tag = f"{tui.CURRENCY} {total:,.2f}"
            lines.append(
                f"  {tui.GREY}Active Bill:{tui.RESET} {tui.BOLD_AMBER}{self.group_name}{tui.RESET}  "
                f"{tui.GREY}•{tui.RESET}  {tui.WHITE}{count} members{tui.RESET}  "
                f"{tui.GREY}•{tui.RESET}  {tui.BOLD_AMBER}{spend_tag}{tui.RESET}"
            )
            lines.append("")
            return lines

        selected_hub = 0
        while True:
            action = tui.select_menu(
                hub_items,
                selected=selected_hub,
                header_fn=hub_header,
                nav_help="[↑/↓] Navigate   [Enter] Select   [Esc] Back to Saved Bills"
            )

            if action == -1:
                return

            selected_hub = action

            if action == 0:
                self.handle_view_balances(header_fn=hub_header)
            elif action == 1:
                self.handle_settlement_plan(header_fn=hub_header)
            elif action == 2:
                self.handle_expense_history(header_fn=hub_header)
            elif action == 3:
                self.handle_edit_engine(header_fn=hub_header)

    def handle_save_data(self):
        """Feature 8: Save data to saved_bills/<slug>.json and data.json."""
        if not self.group_name:
            tui.clear_screen()
            for line in self.render_app_header():
                print(line)
            tui.hint("Please create a group before saving.")
            tui.pause()
            return

        tui.spinner("Saving data...", 0.5)
        ok, path = data_manager.save_data(self.group_name, self.members, self.expenses)
        if ok:
            self.is_dirty = False
            tui.clear_screen()
            for line in self.render_app_header():
                print(line)
            tui.success(f"Saved to '{path}' and backed up in data.json.")
        else:
            tui.error("Failed to save data.")
        tui.pause()

    def handle_exit(self) -> bool:
        """Handle application exit with dirty-check prompt."""
        if self.is_dirty and self.group_name:
            tui.clear_screen()
            for line in self.render_app_header():
                print(line)
            choice = tui.select_one(
                ["Save and exit", "Exit without saving", "Cancel"],
                prompt="You have unsaved changes:"
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
    """Non-interactive showcase of EvenSplit with ASCII header and visual card."""
    tui.clear_screen()
    tui.render_header()
    print(f"  {tui.BOLD_AMBER}Kanak bday{tui.RESET}  {tui.GREY}•  4 members  •  {tui.BOLD_AMBER}₹ 17,500.00{tui.RESET}\n")

    members = ["Alice", "Bob", "Charlie", "Diana"]
    expenses = [
        {"id": 1, "description": "Airbnb Villa", "amount": 12000.0, "payer": "Alice", "participants": members, "split_amount": 3000.0},
        {"id": 2, "description": "Starters & Grill 🍔", "amount": 4000.0, "payer": "Bob", "participants": ["Alice", "Bob", "Charlie"], "split_amount": 1333.33},
        {"id": 3, "description": "Scooter Rentals", "amount": 1500.0, "payer": "Charlie", "participants": ["Bob", "Charlie", "Diana"], "split_amount": 500.0}
    ]

    tui.hint("1. Visual Expense Confirmation Card:")
    tui.render_expense_card("Starters & Grill 🍔", 4000.0, "Bob", 3, 1333.33)

    tui.hint("2. Expense History (Emoji & Width Aligned):")
    tui.render_expense_history(expenses)
    print()

    tui.hint("3. Net Balances Ledger:")
    breakdown = engine.get_member_breakdown(members, expenses)
    tui.render_balances_table(breakdown)
    print()

    tui.hint("4. Greedy Minimum Settlement Plan:")
    net_balances = engine.calculate_net_balances(members, expenses)
    transfers = engine.compute_min_settlements(net_balances)
    tui.render_settlement_plan(transfers, net_balances)

    tui.success("Demo complete. Run without arguments for interactive mode.")
    print()


def main():
    """Entrypoint with signal protection and CLI argument support."""
    try:
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
                print("  (no args)    Interactive zero-flicker arrow-key console application")
                print("  --demo, -d   Run non-interactive showcase")
                print("  --test, -t   Run automated unit tests")
                print("  --help, -h   Show help message")
                return

        app = EvenSplitApp()
        app.run()
    except (KeyboardInterrupt, EOFError):
        print(f"\n  {tui.WHITE}EvenSplit closed.{tui.RESET}\n")


if __name__ == "__main__":
    main()
