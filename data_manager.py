"""
data_manager.py - Persistence Manager for EvenSplit
===================================================
Capstone CP-007: Group Expense Settlement Optimizer

This module handles reading and writing the application state
(Group Name, Members, Expenses) to a local JSON file (`data.json`).
Pure Python standard library (json, os).
"""

import json
import os

DEFAULT_FILEPATH = "data.json"


def save_data(group_name: str, members: list, expenses: list, filepath: str = DEFAULT_FILEPATH) -> bool:
    """
    Saves current group name, members list, and expense history to a JSON file.

    Args:
        group_name (str): Name of the expense group.
        members (list): List of member names.
        expenses (list): List of expense dictionaries.
        filepath (str, optional): Target JSON file path. Defaults to "data.json".

    Returns:
        bool: True if saving succeeded, False otherwise.
    """
    payload = {
        "group_name": group_name,
        "members": members,
        "expenses": expenses
    }

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)
        return True
    except (OSError, IOError) as err:
        print(f"Error saving data to {filepath}: {err}")
        return False


def load_data(filepath: str = DEFAULT_FILEPATH) -> tuple:
    """
    Loads group data from a JSON file.

    If the file does not exist or contains invalid JSON,
    it returns safe default values without crashing.

    Args:
        filepath (str, optional): Source JSON file path. Defaults to "data.json".

    Returns:
        tuple: (group_name: str, members: list, expenses: list)
    """
    if not os.path.exists(filepath):
        return ("EvenSplit Group", [], [])

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        group_name = data.get("group_name", "EvenSplit Group")
        members = data.get("members", [])
        expenses = data.get("expenses", [])

        # Validate types
        if not isinstance(members, list):
            members = []
        if not isinstance(expenses, list):
            expenses = []
        if not isinstance(group_name, str):
            group_name = "EvenSplit Group"

        return (group_name, members, expenses)

    except (json.JSONDecodeError, OSError, IOError) as err:
        print(f"Error loading data from {filepath}: {err}")
        return ("EvenSplit Group", [], [])


def data_file_exists(filepath: str = DEFAULT_FILEPATH) -> bool:
    """
    Checks whether the data file currently exists on disk.

    Args:
        filepath (str, optional): Path to check. Defaults to "data.json".

    Returns:
        bool: True if file exists and is a file, False otherwise.
    """
    return os.path.isfile(filepath)
