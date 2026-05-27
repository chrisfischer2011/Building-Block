"""
Data models for the Building Block application.

This module defines the core domain models used across the UI and data layers.
Using proper dataclasses instead of raw dictionaries improves type safety,
readability, and makes future refactoring easier.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class DataEntry:
    """
    Represents a single data entry in the application.

    This is the primary model that will be used throughout the UI
    (left sidebar selection, inspector editing, main content display).
    """

    id: Optional[int] = None
    date: Optional[date] = None
    category: str = ""
    value: float = 0.0
    notes: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary (useful for database operations)."""
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "category": self.category,
            "value": self.value,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DataEntry":
        """Create a DataEntry from a dictionary (e.g. from database)."""
        entry_date = None
        if data.get("date"):
            if isinstance(data["date"], str):
                entry_date = date.fromisoformat(data["date"])
            else:
                entry_date = data["date"]

        return cls(
            id=data.get("id"),
            date=entry_date,
            category=data.get("category", ""),
            value=data.get("value", 0.0),
            notes=data.get("notes", ""),
        )

    def __str__(self) -> str:
        return f"{self.category} - {self.value}" if self.category else "Unnamed Entry"


# Example of a Reference item (for future use with reference_data table)
@dataclass
class ReferenceItem:
    id: Optional[int] = None
    name: str = ""
    type: str = ""
    default_value: float = 0.0
