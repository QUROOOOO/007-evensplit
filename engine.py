"""engine.py - Core calculation, settlement, and edit engine for EvenSplit (CP-007)."""

import math


def add_member(members: list, name: str) -> str:
    """Validate and register a unique member (case-insensitive)."""
    if not isinstance(name, str):
        raise ValueError("Member name must be a string.")

    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Member name cannot be empty.")

    clean_lower = clean_name.lower()
    for existing in members:
        if existing.lower() == clean_lower:
            raise ValueError(f"Member '{clean_name}' already exists.")

    members.append(clean_name)
    return clean_name


def rename_member(members: list, expenses: list, old_name: str, new_name: str) -> str:
    """Rename a member and cascade updates across all expense records."""
    clean_new = new_name.strip()
    if not clean_new:
        raise ValueError("New name cannot be empty.")

    clean_lower = clean_new.lower()
    if clean_lower != old_name.lower():
        for existing in members:
            if existing.lower() == clean_lower:
                raise ValueError(f"Member '{clean_new}' already exists.")

    # Update members list
    for i, m in enumerate(members):
        if m.lower() == old_name.lower():
            members[i] = clean_new
            break

    # Cascade to expenses
    for exp in expenses:
        if exp["payer"].lower() == old_name.lower():
            exp["payer"] = clean_new
        exp["participants"] = [
            clean_new if p.lower() == old_name.lower() else p
            for p in exp["participants"]
        ]

    return clean_new


def delete_member(members: list, expenses: list, member_name: str) -> bool:
    """Remove a member if they have not paid any bills, updating participant lists."""
    # Check if payer on any bill
    for exp in expenses:
        if exp["payer"].lower() == member_name.lower():
            raise ValueError(f"Cannot delete '{member_name}': payer of expense #{exp.get('id', '')}.")

    # Remove from member list
    members[:] = [m for m in members if m.lower() != member_name.lower()]

    # Remove from participants and recalculate split
    for exp in expenses:
        exp["participants"] = [p for p in exp["participants"] if p.lower() != member_name.lower()]
        if not exp["participants"]:
            raise ValueError(f"Deleting '{member_name}' leaves expense #{exp.get('id')} with 0 participants.")
        exp["split_amount"] = round(exp["amount"] / len(exp["participants"]), 2)

    return True


def record_expense(expenses: list, members: list, desc: str, amount: float, payer: str, participants: list) -> dict:
    """Validate and record a shared expense split equally among participants."""
    if not desc or not desc.strip():
        raise ValueError("Expense description cannot be empty.")
    clean_desc = desc.strip()

    try:
        val = float(amount)
    except (TypeError, ValueError):
        raise ValueError("Amount must be a valid number.")

    if val <= 0 or math.isnan(val) or math.isinf(val):
        raise ValueError("Amount must be greater than zero.")
    val = round(val, 2)

    def find_member(n):
        for m in members:
            if m.lower() == n.strip().lower():
                return m
        return None

    canonical_payer = find_member(payer)
    if not canonical_payer:
        raise ValueError(f"Payer '{payer}' is not in the group.")

    if not participants:
        raise ValueError("At least one participant must be selected.")

    canonical_participants = []
    seen = set()
    for p in participants:
        cp = find_member(p)
        if not cp:
            raise ValueError(f"Participant '{p}' is not in the group.")
        if cp.lower() not in seen:
            seen.add(cp.lower())
            canonical_participants.append(cp)

    if not canonical_participants:
        raise ValueError("No valid participants selected.")

    per_person_share = round(val / len(canonical_participants), 2)

    expense = {
        "id": len(expenses) + 1,
        "description": clean_desc,
        "amount": val,
        "payer": canonical_payer,
        "participants": canonical_participants,
        "split_amount": per_person_share
    }
    expenses.append(expense)
    return expense


def update_expense(expenses: list, members: list, expense_id: int, desc: str = None, amount: float = None, payer: str = None, participants: list = None) -> dict:
    """Update fields on an existing expense and recompute split amount."""
    target = None
    for exp in expenses:
        if exp.get("id") == expense_id:
            target = exp
            break

    if not target:
        raise ValueError(f"Expense #{expense_id} not found.")

    if desc is not None:
        if not desc.strip():
            raise ValueError("Description cannot be empty.")
        target["description"] = desc.strip()

    if amount is not None:
        val = float(amount)
        if val <= 0:
            raise ValueError("Amount must be positive.")
        target["amount"] = round(val, 2)

    if payer is not None:
        if payer not in members:
            raise ValueError(f"Payer '{payer}' not in members.")
        target["payer"] = payer

    if participants is not None:
        if not participants:
            raise ValueError("Participants list cannot be empty.")
        target["participants"] = list(participants)

    target["split_amount"] = round(target["amount"] / len(target["participants"]), 2)
    return target


def delete_expense(expenses: list, expense_id: int) -> bool:
    """Delete an expense record by its id."""
    idx = None
    for i, exp in enumerate(expenses):
        if exp.get("id") == expense_id:
            idx = i
            break
    if idx is None:
        return False
    expenses.pop(idx)
    return True


def calculate_net_balances(members: list, expenses: list) -> dict:
    """Calculate net balance for each member: total_paid - total_consumed."""
    balances = {m: 0.0 for m in members}

    for exp in expenses:
        payer = exp["payer"]
        amt = exp["amount"]
        parts = exp["participants"]

        if payer in balances:
            balances[payer] += amt

        if parts:
            share = amt / len(parts)
            for p in parts:
                if p in balances:
                    balances[p] -= share

    return {m: round(bal, 2) for m, bal in balances.items()}


def get_member_breakdown(members: list, expenses: list) -> dict:
    """Return detailed paid, consumed, and net values for all members."""
    breakdown = {m: {"paid": 0.0, "consumed": 0.0, "net": 0.0} for m in members}

    for exp in expenses:
        payer = exp["payer"]
        amt = exp["amount"]
        parts = exp["participants"]

        if payer in breakdown:
            breakdown[payer]["paid"] += amt

        if parts:
            share = amt / len(parts)
            for p in parts:
                if p in breakdown:
                    breakdown[p]["consumed"] += share

    for m, data in breakdown.items():
        data["paid"] = round(data["paid"], 2)
        data["consumed"] = round(data["consumed"], 2)
        data["net"] = round(data["paid"] - data["consumed"], 2)

    return breakdown


def compute_min_settlements(net_balances: dict) -> list:
    """
    Greedy cash-flow debt minimization.
    Matches largest debtor (bal < -0.01) with largest creditor (bal > 0.01).
    """
    balances = {m: round(bal, 2) for m, bal in net_balances.items()}
    transfers = []
    max_loops = len(balances) * 2

    for _ in range(max_loops):
        debtor = min(balances, key=balances.get)
        creditor = max(balances, key=balances.get)

        debtor_bal = balances[debtor]
        creditor_bal = balances[creditor]

        if debtor_bal >= -0.01 or creditor_bal <= 0.01:
            break

        settle_amt = round(min(abs(debtor_bal), creditor_bal), 2)
        if settle_amt <= 0:
            break

        transfers.append({
            "from": debtor,
            "to": creditor,
            "amount": settle_amt
        })

        balances[debtor] = round(balances[debtor] + settle_amt, 2)
        balances[creditor] = round(balances[creditor] - settle_amt, 2)

    return transfers
