"""
Lightweight application state for the Building Block app.

This is a simple shared state object (Option A from Phase 5 planning).
It is intentionally minimal at this stage. We can evolve it into a more
structured solution later if needed.
"""

from dataclasses import dataclass, field
from typing import Optional

from src.core.models import DataEntry


@dataclass
class AppState:
    """Central place for UI-level state that multiple components need to share."""

    # Sidebar width (persisted in memory for now)
    sidebar_width: float = 280.0

    # Currently selected item (now using proper DataEntry model)
    selected_item: Optional[DataEntry] = field(default=None)

    # Whether the Inspector is in "Create New" mode
    is_creating: bool = False

    def select_item(self, item: DataEntry) -> None:
        """Select an item and exit create mode."""
        self.selected_item = item
        self.is_creating = False

    def clear_selection(self) -> None:
        """Clear the current selection."""
        self.selected_item = None

    def start_creating(self) -> None:
        """Switch the Inspector into Create mode."""
        self.is_creating = True
        self.selected_item = None

    def finish_creating(self) -> None:
        """Exit create mode."""
        self.is_creating = False

    @property
    def has_selection(self) -> bool:
        return self.selected_item is not None
