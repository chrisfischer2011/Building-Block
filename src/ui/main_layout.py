import flet as ft

from src.ui.app_state import AppState
from src.ui.components.inspector_panel import create_inspector_panel
from src.ui.components.left_sidebar import create_left_sidebar
from src.ui.components.main_content import create_main_content
from src.ui.theme import (
    CARD_CONTENT_PADDING,
    CARD_ELEVATION,
    CARD_ELEVATION_LOW,
    CARD_MARGIN,
    PANEL_SPACING,
)


def create_main_layout(page: ft.Page, app_state: AppState) -> ft.Row:
    """
    Main content area with a resizable left sidebar.

    This is now a thin orchestrator that composes the three main panels
    and handles the horizontal resizing behavior.
    """
    color_scheme = page.theme.color_scheme

    # --- Inspector wrapper (supports both "New" reset and normal item selection) ---
    # We keep the inspector inside a Container so we can completely replace its
    # content when the selection changes or when the user does File > New.
    inspector_wrapper = ft.Container(expand=True)

    def _rebuild_inspector():
        """Rebuild the inspector card from scratch using current app_state.
        Used for both normal selection changes and File > New.
        """
        try:
            new_content = create_inspector_panel(page, app_state)
            inspector_wrapper.content = new_content
            inspector_wrapper.update()
        except Exception as ex:
            # Log but do not let the exception bubble up and break the UI click
            print(f"[Inspector] Failed to rebuild inspector: {ex}")
            try:
                inspector_wrapper.update()
            except Exception:
                pass

    # Initial content
    inspector_wrapper.content = create_inspector_panel(page, app_state)

    # Allow AppState.clear() (triggered by File > New) to reset this panel
    if hasattr(app_state, "register_inspector_refresh"):
        app_state.register_inspector_refresh(_rebuild_inspector)

    # --- Selection change handler (wired to left sidebar) ---
    # When the user clicks an item, this forces the inspector (and any other
    # dependent panels) to rebuild with the newly selected data.
    def on_selection_changed(item):
        # The sidebar click handler already called app_state.select_item(item),
        # but we ensure it here for safety / future callers.
        if item is not None:
            app_state.select_item(item)

        # Rebuild the inspector to reflect the current selection (or empty state)
        _rebuild_inspector()

        # Belt-and-suspenders top-level refresh
        try:
            page.update()
        except Exception:
            pass

    # Use AppState as the single source of truth for sidebar width
    left_container = ft.Container(
        content=create_left_sidebar(
            page,
            app_state,
            on_selection_changed=on_selection_changed,
        ),
        width=app_state.sidebar_width,
    )

    divider_handle = ft.Container(
        width=10,
        bgcolor=ft.Colors.GREY_400,
    )

    def on_divider_hover(e: ft.HoverEvent):
        divider_handle.bgcolor = (
            ft.Colors.GREY_600 if e.data == "true" else ft.Colors.GREY_400
        )
        divider_handle.update()

    def on_pan_start(e: ft.DragStartEvent):
        app_state.sidebar_width = left_container.width or app_state.sidebar_width
        divider_handle.bgcolor = ft.Colors.BLUE_GREY_600
        divider_handle.update()

    def on_pan_update(e: ft.DragUpdateEvent):
        if e.local_delta is None:
            return

        current = left_container.width or app_state.sidebar_width
        new_width = current + e.local_delta.x
        new_width = max(180, min(500, new_width))

        app_state.sidebar_width = new_width
        left_container.width = new_width
        left_container.update()

    def on_pan_end(e: ft.DragEndEvent):
        left_container.width = app_state.sidebar_width
        divider_handle.bgcolor = ft.Colors.GREY_400
        page.update()

    divider = ft.GestureDetector(
        content=divider_handle,
        drag_interval=8,
        on_pan_start=on_pan_start,
        on_pan_update=on_pan_update,
        on_pan_end=on_pan_end,
        on_hover=on_divider_hover,
        mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
    )

    # The inspector_wrapper (and its _rebuild_inspector function) were already
    # created earlier so that both File > New and normal selection changes can
    # refresh it. We simply reference the existing wrapper here.
    right_panel = ft.Column(
        [
            inspector_wrapper,
            create_main_content(page, app_state),
        ],
        spacing=PANEL_SPACING,
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        margin=CARD_MARGIN,
    )

    return ft.Row(
        [left_container, divider, right_panel],
        spacing=0,
        expand=True,
        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
    )
