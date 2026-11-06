"""data_manager.py - Persistence module for EvenSplit (CP-007)."""

import json
import os

DEFAULT_FILEPATH = "data.json"


def save_data(group_name: str, members: list, expenses: list, filepath: str = DEFAULT_FILEPATH) -> bool:
    """Save group state to a JSON file."""
    payload = {
        "group_name": group_name,
        "members": members,
        "expenses": expenses
    }
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)
        return True
    except (OSError, IOError):
        return False


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


def data_file_exists(filepath: str = DEFAULT_FILEPATH) -> bool:
    """Check if the storage file exists on disk."""
    return os.path.isfile(filepath)
