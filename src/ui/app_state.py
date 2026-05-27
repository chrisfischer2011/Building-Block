"""
Lightweight application state for the Building Block app.

This is a simple shared state object (Option A from Phase 5 planning).
It is intentionally minimal at this stage. We can evolve it into a more
structured solution later if needed.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AppState:
    """Central place for UI-level state that multiple components need to share."""

    # Sidebar width (persisted in memory for now)
    sidebar_width: float = 280.0

    # Currently selected item (very basic for Phase 5)
    # In the future this can become a proper model / dataclass.
    selected_item: Optional[dict] = field(default=None)

    def select_item(self, item: dict) -> None:
        """Select an item (used by RackAmpSelector)."""
        self.selected_item = item

    def clear_selection(self) -> None:
        """Clear the current selection."""
        self.selected_item = None

    @property
    def has_selection(self) -> bool:
        return self.selected_item is not None
