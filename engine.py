"""
engine.py - Core Mathematical and Algorithmic Engine for EvenSplit
==================================================================
Capstone CP-007: Group Expense Settlement Optimizer

This module contains the core business logic, calculations, and the
Greedy Cash-Flow Minimization algorithm for settling group debts.

Functions:
  - add_member(members, name)
  - record_expense(expenses, members, desc, amount, payer, participants)
  - calculate_net_balances(members, expenses)
  - compute_min_settlements(net_balances)
  - get_member_breakdown(members, expenses)  (helper for detailed views)
"""

import math


def add_member(members: list, name: str) -> str:
    """
    Validates and registers a new member into the group.

    Validation rules:
      1. Name cannot be empty or just whitespace.
      2. Name must be unique within the group (case-insensitive check).

    Args:
        members (list): Current list of member names (strings).
        name (str): Proposed name for the new member.

    Returns:
        str: The clean, trimmed member name that was added.

    Raises:
        ValueError: If name is empty or already exists in the group.
    """
    if not isinstance(name, str):
        raise ValueError("Member name must be a string.")

    cleaned_name = name.strip()

    # Rule 1: Validate non-empty name
    if not cleaned_name:
        raise ValueError("Member name cannot be empty or blank.")

    # Rule 2: Case-insensitive uniqueness check
    cleaned_lower = cleaned_name.lower()
    for existing_member in members:
        if existing_member.lower() == cleaned_lower:
            raise ValueError(f"Member '{cleaned_name}' already exists (matches '{existing_member}').")

    # If valid, append to list and return the clean name
    members.append(cleaned_name)
    return cleaned_name


def record_expense(expenses: list, members: list, desc: str, amount: float, payer: str, participants: list) -> dict:
    """
    Validates and records a new shared expense among group members.

    Validation rules:
      1. Description must be non-empty.
      2. Amount must be a positive number (> 0).
      3. Payer must be an existing group member.
      4. Participants list must be non-empty and all participants must be valid members.

    Computation:
      - Divides the total bill equally among participants:
        share = amount / number_of_participants

    Args:
        expenses (list): Existing list of expense records.
        members (list): Current list of registered member names.
        desc (str): Brief description of the expense (e.g., 'Dinner', 'Groceries').
        amount (float or int): Total amount paid.
        payer (str): Name of the member who paid.
        participants (list): List of member names who share this expense.

    Returns:
        dict: The created expense record.

    Raises:
        ValueError: If any validation rule fails.
    """
    # 1. Validate description
    if not desc or not desc.strip():
        raise ValueError("Expense description cannot be empty.")
    clean_desc = desc.strip()

    # 2. Validate amount
    try:
        amount_val = float(amount)
    except (TypeError, ValueError):
        raise ValueError("Expense amount must be a valid number.")

    if amount_val <= 0 or math.isnan(amount_val) or math.isinf(amount_val):
        raise ValueError("Expense amount must be greater than zero.")
    amount_val = round(amount_val, 2)

    # Helper: case-insensitive member finder
    def find_member(name):
        for m in members:
            if m.lower() == name.strip().lower():
                return m
        return None

    # 3. Validate payer
    canonical_payer = find_member(payer)
    if not canonical_payer:
        raise ValueError(f"Payer '{payer}' is not a registered member of the group.")

    # 4. Validate participants
    if not participants:
        raise ValueError("At least one participant must be selected for the expense.")

    canonical_participants = []
    seen = set()
    for p in participants:
        canonical_p = find_member(p)
        if not canonical_p:
            raise ValueError(f"Participant '{p}' is not a registered member of the group.")
        if canonical_p.lower() not in seen:
            seen.add(canonical_p.lower())
            canonical_participants.append(canonical_p)

    if not canonical_participants:
        raise ValueError("No valid participants selected.")

    # 5. Compute per-person share
    num_participants = len(canonical_participants)
    per_person_share = round(amount_val / num_participants, 2)

    # 6. Build expense record
    expense_record = {
        "id": len(expenses) + 1,
        "description": clean_desc,
        "amount": amount_val,
        "payer": canonical_payer,
        "participants": canonical_participants,
        "split_amount": per_person_share
    }

    expenses.append(expense_record)
    return expense_record


def calculate_net_balances(members: list, expenses: list) -> dict:
    """
    Calculates the real-time net balance for each member in the group.

    Formula:
      Net Balance = Total Amount Paid - Total Share Consumed

    Interpretation:
      - Positive balance (+): Member paid more than their share; they are OWED money.
      - Negative balance (-): Member consumed more than they paid; they OWE money.
      - Zero balance (0.00): Member is completely settled.

    Args:
        members (list): List of registered group members.
        expenses (list): List of all recorded expense dictionaries.

    Returns:
        dict: Mapping of {member_name: net_balance_float} rounded to 2 decimals.
    """
    # Start everyone at 0.00 balance
    net_balances = {member: 0.0 for member in members}

    for exp in expenses:
        payer = exp["payer"]
        amount = exp["amount"]
        participants = exp["participants"]

        # The payer paid the entire amount upfront (+ credit)
        if payer in net_balances:
            net_balances[payer] += amount

        # Each participant owes their portion (- debit)
        if participants:
            share = amount / len(participants)
            for person in participants:
                if person in net_balances:
                    net_balances[person] -= share

    # Round all values to 2 decimal places to avoid floating point precision artifacts
    return {member: round(balance, 2) for member, balance in net_balances.items()}


def get_member_breakdown(members: list, expenses: list) -> dict:
    """
    Provides a detailed breakdown of total paid, total share consumed,
    and net balance for each member. Useful for tabular displays.

    Args:
        members (list): List of registered group members.
        expenses (list): List of all recorded expense dictionaries.

    Returns:
        dict: {
            member: {
                "paid": float,
                "consumed": float,
                "net": float
            }
        }
    """
    breakdown = {
        member: {"paid": 0.0, "consumed": 0.0, "net": 0.0}
        for member in members
    }

    for exp in expenses:
        payer = exp["payer"]
        amount = exp["amount"]
        participants = exp["participants"]

        if payer in breakdown:
            breakdown[payer]["paid"] += amount

        if participants:
            share = amount / len(participants)
            for person in participants:
                if person in breakdown:
                    breakdown[person]["consumed"] += share

    for member, data in breakdown.items():
        data["paid"] = round(data["paid"], 2)
        data["consumed"] = round(data["consumed"], 2)
        data["net"] = round(data["paid"] - data["consumed"], 2)

    return breakdown


def compute_min_settlements(net_balances: dict) -> list:
    """
    Greedy Cash-Flow Minimization Algorithm.

    Reduces complex group debts into the minimum possible number of
    direct peer-to-peer transfers.

    How it works:
      1. Identify the person with the largest negative balance (the biggest DEBTOR).
         A debtor has a balance < -0.01.
      2. Identify the person with the largest positive balance (the biggest CREDITOR).
         A creditor has a balance > 0.01.
      3. Settle an amount equal to min(abs(debtor_balance), creditor_balance).
      4. The debtor pays this amount directly to the creditor.
      5. Update both balances:
           debtor_balance += amount   (moves towards 0)
           creditor_balance -= amount (moves towards 0)
      6. At least one person's balance becomes 0 on every step!
      7. Repeat until all balances are within [-0.01, 0.01] (completely settled).

    Args:
        net_balances (dict): Mapping of {member: net_balance}.

    Returns:
        list of dict: List of recommended transfers:
            [{"from": debtor, "to": creditor, "amount": val}, ...]
    """
    # Make a working copy of balances so we don't mutate the original dictionary
    balances = {member: round(bal, 2) for member, bal in net_balances.items()}
    transfers = []

    # Safety limit to prevent any infinite loop (at most N-1 transactions are needed)
    max_iterations = len(balances) * 2
    iteration_count = 0

    while iteration_count < max_iterations:
        iteration_count += 1

        # Find the person who owes the most (smallest negative value)
        # and the person who is owed the most (largest positive value)
        debtor = min(balances, key=balances.get)
        creditor = max(balances, key=balances.get)

        debtor_balance = balances[debtor]
        creditor_balance = balances[creditor]

        # Stop when there is no significant debtor or creditor left
        # (threshold of 0.01 handles sub-cent fractional remainders)
        if debtor_balance >= -0.01 or creditor_balance <= 0.01:
            break

        # Calculate payment amount: the smaller of what debtor owes and creditor is owed
        amount_to_settle = min(abs(debtor_balance), creditor_balance)
        amount_to_settle = round(amount_to_settle, 2)

        # Skip negligible transfers
        if amount_to_settle <= 0:
            break

        # Record this direct transfer
        transfers.append({
            "from": debtor,
            "to": creditor,
            "amount": amount_to_settle
        })

        # Update the running balances
        balances[debtor] = round(balances[debtor] + amount_to_settle, 2)
        balances[creditor] = round(balances[creditor] - amount_to_settle, 2)

    return transfers
