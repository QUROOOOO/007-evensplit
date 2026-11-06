"""data_manager.py - Persistence module for EvenSplit (CP-007)."""

import json
import os
import re

DEFAULT_FILEPATH = "data.json"
SAVED_BILLS_DIR = "saved_bills"


def slugify(text: str) -> str:
    """Generate a clean filesystem slug from a string."""
    clean = re.sub(r"[^\w\s-]", "", text.strip().lower())
    slug = re.sub(r"[-\s]+", "_", clean)
    return slug or "untitled_group"


def save_data(group_name: str, members: list, expenses: list, filepath: str = DEFAULT_FILEPATH, old_group_name: str = "") -> tuple[bool, str]:
    """Save group state to JSON files (saved_bills/ and primary data.json)."""
    payload = {
        "group_name": group_name,
        "members": members,
        "expenses": expenses
    }
    saved_path = filepath
    try:
        # Save to primary filepath
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)

        # Also save to saved_bills/ directory if group_name exists
        if group_name and group_name.strip():
            os.makedirs(SAVED_BILLS_DIR, exist_ok=True)
            slug = slugify(group_name)
            named_path = os.path.join(SAVED_BILLS_DIR, f"{slug}.json")
            with open(named_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4, ensure_ascii=False)
            saved_path = named_path

            # Clean up old slug file if renamed
            if old_group_name and old_group_name.strip():
                old_slug = slugify(old_group_name)
                if old_slug != slug:
                    old_path = os.path.join(SAVED_BILLS_DIR, f"{old_slug}.json")
                    if os.path.isfile(old_path):
                        try:
                            os.remove(old_path)
                        except OSError:
                            pass

        return True, saved_path
    except (OSError, IOError):
        return False, ""


def load_data(filepath: str = DEFAULT_FILEPATH) -> tuple:
    """Load group state from a JSON file, returning safe defaults on failure."""
    if not os.path.exists(filepath):
        return ("", [], [])

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        group_name = data.get("group_name", "")
        members = data.get("members", [])
        expenses = data.get("expenses", [])

        if not isinstance(group_name, str):
            group_name = ""
        if not isinstance(members, list):
            members = []
        if not isinstance(expenses, list):
            expenses = []

        return (group_name, members, expenses)
    except (json.JSONDecodeError, OSError, IOError):
        return ("", [], [])


def list_saved_bills() -> list[dict]:
    """Return summary list of all JSON bills stored in saved_bills/."""
    if not os.path.exists(SAVED_BILLS_DIR):
        return []

    bills = []
    for fname in sorted(os.listdir(SAVED_BILLS_DIR)):
        if fname.endswith(".json"):
            path = os.path.join(SAVED_BILLS_DIR, fname)
            name, members, expenses = load_data(path)
            total = sum(e.get("amount", 0.0) for e in expenses)
            bills.append({
                "filename": fname,
                "filepath": path,
                "group_name": name or fname[:-5],
                "members_count": len(members),
                "total_spend": total
            })
    return bills


def data_file_exists(filepath: str = DEFAULT_FILEPATH) -> bool:
    """Check if storage file exists on disk."""
    return os.path.isfile(filepath)
