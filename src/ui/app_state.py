"""
Lightweight application state for the Building Block app.

This is a simple shared state object (Option A from Phase 5 planning).
It is intentionally minimal at this stage. We can evolve it into a more
structured solution later if needed.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

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

    # Callbacks registered by UI components (sidebar, inspector, rack visual) so that
    # "File > New" can trigger live refresh/rebuild of those panels.
    _sidebar_refresh_callbacks: List[Callable[[], None]] = field(
        default_factory=list, init=False, repr=False
    )
    _inspector_refresh_callbacks: List[Callable[[], None]] = field(
        default_factory=list, init=False, repr=False
    )
    _visual_refresh_callbacks: List[Callable[[], None]] = field(
        default_factory=list, init=False, repr=False
    )

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

    def clear(self) -> None:
        """Full reset for File > New: clears selection/create mode and notifies
        registered UI components (sidebar list + inspector) to refresh to empty state.
        """
        self.selected_item = None
        self.is_creating = False

        # Notify listeners (best-effort)
        for cb in list(self._sidebar_refresh_callbacks):
            try:
                cb()
            except Exception as ex:
                print(f"[AppState] sidebar refresh callback error: {ex}")

        for cb in list(self._inspector_refresh_callbacks):
            try:
                cb()
            except Exception as ex:
                print(f"[AppState] inspector refresh callback error: {ex}")

        for cb in list(self._visual_refresh_callbacks):
            try:
                cb()
            except Exception as ex:
                print(f"[AppState] visual refresh callback error: {ex}")

    def register_sidebar_refresh(self, callback: Callable[[], None]) -> None:
        """Register a function that can be called to force the left sidebar to reload/rebuild."""
        if callback and callback not in self._sidebar_refresh_callbacks:
            self._sidebar_refresh_callbacks.append(callback)

    def register_inspector_refresh(self, callback: Callable[[], None]) -> None:
        """Register a function that can be called to force the inspector panel to rebuild."""
        if callback and callback not in self._inspector_refresh_callbacks:
            self._inspector_refresh_callbacks.append(callback)

    def register_visual_refresh(self, callback: Callable[[], None]) -> None:
        """Register a function that can be called to force the bottom rack visual panel to rebuild."""
        if callback and callback not in self._visual_refresh_callbacks:
            self._visual_refresh_callbacks.append(callback)
