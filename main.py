"""
main.py - Main Application Controller for EvenSplit
===================================================
Capstone CP-007: Group Expense Settlement Optimizer

Modular, console-based group expense settlement application.
Implements the 5 Bizotic Core Features + Save/Reload + Claude Code TUI:
  [1] Create Group & Add Members
  [2] Add Shared Expense
  [3] View Member Net Balances
  [4] Generate Minimum Settlement Plan
  [5] Full Expense History
  [6] Save / Reload Data (JSON)
  [0] Exit Application
"""

import sys
import data_manager
import engine
import tui


class EvenSplitApp:
    """Application controller coordinating data, engine calculations, and TUI."""

    def __init__(self):
        self.group_name = "Trip to Goa"
        self.members = []
        self.expenses = []
        self.is_dirty = False

        # Attempt to auto-load existing data.json on startup
        if data_manager.data_file_exists():
            loaded_name, loaded_members, loaded_expenses = data_manager.load_data()
            if loaded_members:
                self.group_name = loaded_name
                self.members = loaded_members
                self.expenses = loaded_expenses

    def get_total_spend(self) -> float:
        """Computes aggregate expenditure of the group."""
        return sum(exp.get("amount", 0.0) for exp in self.expenses)

    def run(self):
        """Main application execution loop."""
        while True:
            try:
                tui.clear_screen()
                tui.render_banner()
                tui.render_status_bar(
                    self.group_name,
                    len(self.members),
                    len(self.expenses),
                    self.get_total_spend()
                )
                tui.render_menu()

                choice = tui.prompt_input("Select an option (0-6)")

                if choice == "1":
                    self.handle_group_and_members()
                elif choice == "2":
                    self.handle_add_expense()
                elif choice == "3":
                    self.handle_view_balances()
                elif choice == "4":
                    self.handle_settlement_plan()
                elif choice == "5":
                    self.handle_expense_history()
                elif choice == "6":
                    self.handle_save_reload()
                elif choice == "0":
                    if self.handle_exit():
                        break
                else:
                    tui.warning("Invalid choice. Please select a number from 0 to 6.")
                    tui.pause()

            except (KeyboardInterrupt, EOFError):
                print()
                if self.handle_exit():
                    break

    # -----------------------------------------------------------------------
    # Feature 1: Create Group & Add Members
    # -----------------------------------------------------------------------
    def handle_group_and_members(self):
        """Feature 1: Setup group name and register unique members."""
        tui.clear_screen()
        tui.render_banner()
        tui.section_header(
            "Feature 1: Group & Member Management",
            "Set group name and register unique member names (case-insensitive duplicate check)"
        )

        print(f"  {tui.BOLD_WHITE}Current Group Name:{tui.RESET} {tui.BOLD_CYAN}{self.group_name}{tui.RESET}")
        
        # Display existing roster
        if self.members:
            headers = ["#", "Member Name", "Registered Status"]
            rows = [[str(idx), m, f"{tui.BOLD_GREEN}Active{tui.RESET}"] for idx, m in enumerate(self.members, start=1)]
            tui.render_table(headers, rows, alignments=["C", "L", "L"])
        else:
            tui.info("No members registered yet. Add at least 2 members to begin tracking expenses.")

        print()
        print(f"  {tui.BOLD_CYAN}[1]{tui.RESET} Rename Group")
        print(f"  {tui.BOLD_CYAN}[2]{tui.RESET} Add New Member(s)")
        print(f"  {tui.BOLD_CYAN}[0]{tui.RESET} Return to Main Menu")
        print()

        sub_choice = tui.prompt_input("Choose action (0-2)", default="2")

        if sub_choice == "1":
            new_name = tui.prompt_input("Enter new group name", default=self.group_name)
            if new_name:
                self.group_name = new_name
                self.is_dirty = True
                tui.success(f"Group name updated to '{self.group_name}'")
                tui.pause()

        elif sub_choice == "2":
            print()
            tui.info("Tip: You can add a single name, or multiple names separated by commas (e.g., 'Alice, Bob, Charlie').")
            names_input = tui.prompt_input("Enter member name(s)")

            if not names_input:
                tui.warning("No names entered.")
                tui.pause()
                return

            candidates = [n.strip() for n in names_input.split(",") if n.strip()]
            added_count = 0

            for candidate in candidates:
                try:
                    added_name = engine.add_member(self.members, candidate)
                    tui.success(f"Added member: '{added_name}'")
                    added_count += 1
                except ValueError as err:
                    tui.error(f"Could not add '{candidate}': {err}")

            if added_count > 0:
                self.is_dirty = True
                tui.spinner("Updating roster...", 0.6)

            tui.pause()

    # -----------------------------------------------------------------------
    # Feature 2: Add Shared Expense
    # -----------------------------------------------------------------------
    def handle_add_expense(self):
        """Feature 2: Add a new bill with payer and participant selection."""
        tui.clear_screen()
        tui.render_banner()
        tui.section_header(
            "Feature 2: Add Shared Expense",
            "Record who paid, the total amount, and choose participants to split with"
        )

        # Validation: Must have at least 2 members
        if len(self.members) < 2:
            tui.warning("You need at least 2 registered members to record a shared expense.")
            tui.info("Please use Option [1] to add members first.")
            tui.pause()
            return

        # 1. Expense Description
        while True:
            desc = tui.prompt_input("Expense Description (e.g., 'Dinner', 'Villa Stay')")
            if desc:
                break
            tui.warning("Description cannot be empty.")

        # 2. Expense Amount
        while True:
            amount_str = tui.prompt_input(f"Total Amount in {tui.CURRENCY}")
            try:
                amount = float(amount_str)
                if amount <= 0:
                    tui.warning("Amount must be strictly greater than 0.")
                    continue
                break
            except ValueError:
                tui.error("Invalid amount. Please enter a valid positive number.")

        # 3. Payer Selection
        print()
        print(f"  {tui.BOLD_WHITE}Select who paid for this expense:{tui.RESET}")
        for idx, m in enumerate(self.members, start=1):
            print(f"    {tui.BOLD_CYAN}[{idx}]{tui.RESET} {m}")
        print()

        payer = None
        while not payer:
            payer_input = tui.prompt_input("Payer (enter member number or name)")
            # Try index first
            if payer_input.isdigit():
                p_idx = int(payer_input) - 1
                if 0 <= p_idx < len(self.members):
                    payer = self.members[p_idx]
                else:
                    tui.warning(f"Please enter a number between 1 and {len(self.members)}.")
            else:
                # Match by name
                for m in self.members:
                    if m.lower() == payer_input.lower():
                        payer = m
                        break
                if not payer:
                    tui.warning(f"'{payer_input}' not found in group roster.")

        # 4. Participants Selection
        print()
        print(f"  {tui.BOLD_WHITE}Select participants sharing this bill:{tui.RESET}")
        for idx, m in enumerate(self.members, start=1):
            print(f"    {tui.BOLD_CYAN}[{idx}]{tui.RESET} {m}")
        print()
        tui.info("Options: Enter 'all' to split among everyone, or enter comma-separated numbers (e.g. '1, 3').")

        selected_participants = []
        while not selected_participants:
            part_input = tui.prompt_input("Participants", default="all")

            if part_input.lower() == "all":
                selected_participants = list(self.members)
                break

            # Parse comma-separated numbers or names
            tokens = [t.strip() for t in part_input.split(",") if t.strip()]
            resolved = []
            has_error = False

            for tok in tokens:
                if tok.isdigit():
                    idx = int(tok) - 1
                    if 0 <= idx < len(self.members):
                        m_name = self.members[idx]
                        if m_name not in resolved:
                            resolved.append(m_name)
                    else:
                        tui.warning(f"Invalid member index: {tok}")
                        has_error = True
                else:
                    matched = None
                    for m in self.members:
                        if m.lower() == tok.lower():
                            matched = m
                            break
                    if matched:
                        if matched not in resolved:
                            resolved.append(matched)
                    else:
                        tui.warning(f"Unknown member name: '{tok}'")
                        has_error = True

            if not has_error and resolved:
                selected_participants = resolved
            elif not resolved:
                tui.error("At least one valid participant must be selected.")

        # 5. Calculation Summary & Confirmation
        share = round(amount / len(selected_participants), 2)
        print()
        summary_lines = [
            f"{tui.BOLD}Description:{tui.RESET}   {desc}",
            f"{tui.BOLD}Total Amount:{tui.RESET}  {tui.BOLD_GREEN}{tui.CURRENCY} {amount:,.2f}{tui.RESET}",
            f"{tui.BOLD}Paid By:{tui.RESET}       {tui.BOLD_CYAN}{payer}{tui.RESET}",
            f"{tui.BOLD}Split Among:{tui.RESET}   {', '.join(selected_participants)} ({len(selected_participants)} members)",
            f"{tui.BOLD}Each Shares:{tui.RESET}   {tui.BOLD_WHITE}{tui.CURRENCY} {share:,.2f}{tui.RESET}"
        ]
        tui.render_card("EXPENSE SUMMARY", summary_lines, border_color=tui.CYAN)

        confirm = tui.prompt_input("Confirm and record this expense? (y/n)", default="y")
        if confirm.lower() in ("y", "yes"):
            tui.spinner("Recording expense and recalculating ledger...", 0.8)
            try:
                engine.record_expense(
                    self.expenses,
                    self.members,
                    desc,
                    amount,
                    payer,
                    selected_participants
                )
                self.is_dirty = True
                tui.success("Expense successfully recorded!")
            except ValueError as err:
                tui.error(f"Failed to record expense: {err}")
        else:
            tui.warning("Expense recording cancelled.")

        tui.pause()

    # -----------------------------------------------------------------------
    # Feature 3: View Member Net Balances
    # -----------------------------------------------------------------------
    def handle_view_balances(self):
        """Feature 3: Display current balance ledger for all members."""
        tui.clear_screen()
        tui.render_banner()
        tui.section_header(
            "Feature 3: Member Net Balances",
            "Real-time breakdown: Total Paid vs Total Consumed and Net Balances"
        )

        if not self.members:
            tui.warning("No members registered yet.")
            tui.pause()
            return

        tui.spinner("Computing real-time net balances...", 0.8)
        breakdown = engine.get_member_breakdown(self.members, self.expenses)
        tui.render_balances_table(breakdown)

        tui.pause()

    # -----------------------------------------------------------------------
    # Feature 4: Generate Minimum Settlement Plan
    # -----------------------------------------------------------------------
    def handle_settlement_plan(self):
        """Feature 4: Execute greedy algorithm to simplify debts to minimum transactions."""
        tui.clear_screen()
        tui.render_banner()
        tui.section_header(
            "Feature 4: Minimum Settlement Plan",
            "Greedy Cash-Flow Minimization: Settle maximum debtor with maximum creditor"
        )

        if not self.members:
            tui.warning("No members registered yet.")
            tui.pause()
            return

        if not self.expenses:
            tui.info("No expenses recorded yet. All accounts are currently at zero.")
            tui.pause()
            return

        tui.spinner("Optimizing cash flows with Greedy Minimization Algorithm...", 0.8)

        # 1. Calculate net balances
        net_balances = engine.calculate_net_balances(self.members, self.expenses)

        # 2. Run Greedy settlement algorithm
        transfers = engine.compute_min_settlements(net_balances)

        # 3. Render visual transfer routes
        tui.render_settlement_plan(transfers, net_balances)

        tui.pause()

    # -----------------------------------------------------------------------
    # Feature 5: Full Expense History
    # -----------------------------------------------------------------------
    def handle_expense_history(self):
        """Feature 5: Chronological log of all group payments."""
        tui.clear_screen()
        tui.render_banner()
        tui.section_header(
            "Feature 5: Expense History & Audit Log",
            "Complete chronological record of all bills paid within the group"
        )

        if not self.expenses:
            tui.warning("No expenses have been recorded yet.")
        else:
            tui.spinner("Loading transaction history...", 0.5)
            tui.render_expense_history(self.expenses)

        tui.pause()

    # -----------------------------------------------------------------------
    # Feature 6: Save / Reload Data (JSON)
    # -----------------------------------------------------------------------
    def handle_save_reload(self):
        """Feature 6: Persist state to data.json or reload from disk."""
        tui.clear_screen()
        tui.render_banner()
        tui.section_header(
            "Feature 6: Data Persistence (JSON)",
            "Save current session data to data.json or reload saved state from disk"
        )

        exists = data_manager.data_file_exists()
        print(f"  {tui.BOLD_WHITE}Persistence File:{tui.RESET} {data_manager.DEFAULT_FILEPATH}")
        print(f"  {tui.BOLD_WHITE}File on Disk:{tui.RESET}     {tui.BOLD_GREEN}Found{tui.RESET}" if exists else f"  {tui.BOLD_WHITE}File on Disk:{tui.RESET}     {tui.BOLD_AMBER}Not created yet{tui.RESET}")
        print(f"  {tui.BOLD_WHITE}Unsaved Changes:{tui.RESET}  {tui.BOLD_AMBER}Yes (dirty){tui.RESET}" if self.is_dirty else f"  {tui.BOLD_WHITE}Unsaved Changes:{tui.RESET}  {tui.BOLD_GREEN}None (clean){tui.RESET}")
        print()

        print(f"  {tui.BOLD_CYAN}[1]{tui.RESET} Save Current Data to {data_manager.DEFAULT_FILEPATH}")
        print(f"  {tui.BOLD_CYAN}[2]{tui.RESET} Reload Data from {data_manager.DEFAULT_FILEPATH}")
        print(f"  {tui.BOLD_CYAN}[0]{tui.RESET} Back to Main Menu")
        print()

        choice = tui.prompt_input("Select action (0-2)")

        if choice == "1":
            tui.spinner("Writing data to JSON file...", 0.8)
            success = data_manager.save_data(self.group_name, self.members, self.expenses)
            if success:
                self.is_dirty = False
                tui.success(f"Data saved successfully to '{data_manager.DEFAULT_FILEPATH}'!")
            else:
                tui.error("Failed to save data.")
            tui.pause()

        elif choice == "2":
            if self.is_dirty:
                warn_confirm = tui.prompt_input("You have unsaved changes. Overwrite with file data? (y/n)", default="n")
                if warn_confirm.lower() not in ("y", "yes"):
                    tui.warning("Reload aborted.")
                    tui.pause()
                    return

            tui.spinner("Loading data from JSON file...", 0.8)
            loaded_name, loaded_members, loaded_expenses = data_manager.load_data()
            self.group_name = loaded_name
            self.members = loaded_members
            self.expenses = loaded_expenses
            self.is_dirty = False
            tui.success(f"Successfully loaded '{self.group_name}' with {len(self.members)} members and {len(self.expenses)} expenses.")
            tui.pause()

    # -----------------------------------------------------------------------
    # Feature 0: Exit Application
    # -----------------------------------------------------------------------
    def handle_exit(self) -> bool:
        """Handles graceful exit with prompt for unsaved changes."""
        if self.is_dirty:
            print()
            tui.warning("You have unsaved changes in your current group session.")
            save_ans = tui.prompt_input("Would you like to save to data.json before exiting? (y/n)", default="y")
            if save_ans.lower() in ("y", "yes"):
                tui.spinner("Saving data...", 0.8)
                data_manager.save_data(self.group_name, self.members, self.expenses)
                tui.success("Session saved successfully.")

        print()
        lines = [
            f"{tui.BOLD_WHITE}Thank you for using EvenSplit!{tui.RESET}",
            f"{tui.DIM}All shared debts resolved cleanly and fairly.{tui.RESET}",
            f"{tui.BOLD_PURPLE}Capstone CP-007  •  EvenSplit Engine{tui.RESET}"
        ]
        tui.render_card("GOODBYE", lines, border_color=tui.PURPLE)
        print()
        return True


def main():
    """Application entrypoint."""
    app = EvenSplitApp()
    app.run()


if __name__ == "__main__":
    main()
