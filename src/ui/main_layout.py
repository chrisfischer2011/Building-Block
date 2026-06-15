import flet as ft

from src.ui.app_state import AppState
from src.ui.components.inspector_panel import create_inspector_panel
from src.ui.components.left_sidebar import create_left_sidebar
from src.ui.components.main_content import create_main_content
from src.ui.components.rack_visual import create_rack_visual_panel
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

    # --- Visual (bottom) wrapper: 112 rack faceplate (now explicitly sized to 1/4 printable page
    # section for accurate print layout preview). Non-112 falls back to legacy main_content.
    # We use explicit height (supported in this Flet version) + dynamic adjustment in _rebuild_visual
    # so the 112 preview is strictly limited to ~1/4 page proportions, while fallback content isn't
    # artificially clipped.
    visual_wrapper = ft.Container()  # height will be set dynamically in _rebuild_visual

    def _rebuild_visual():
        """Rebuild the bottom visual area.
        For Rack + Rack Type in (112, 112(AIS)) we show the stylized visualization (capped at 1/4 page size).
        Everything else falls back to create_main_content (left untouched per request).
        """
        item = getattr(app_state, "selected_item", None)
        is_rack = bool(item) and (getattr(item, "device_type", "") or "").lower() == "rack"
        rack_type = ""
        if is_rack:
            props = getattr(item, "properties", {}) or {}
            if isinstance(props, str):
                try:
                    import json
                    props = json.loads(props)
                except Exception:
                    props = {}
            rack_type = (props.get("Rack Type") or "").strip()

        is_112 = rack_type in ("112", "112(AIS)")

        try:
            if is_rack and is_112:
                new_content = create_rack_visual_panel(page, app_state)
                visual_wrapper.height = 530  # enforce 1/4 page limit for the 112 preview
            else:
                new_content = create_main_content(page, app_state)
                visual_wrapper.height = None  # let fallback use available space (no artificial cap)
            visual_wrapper.content = new_content
            visual_wrapper.update()
        except Exception as ex:
            print(f"[Visual] Failed to rebuild bottom visual: {ex}")
            try:
                visual_wrapper.update()
            except Exception:
                pass

    # Initial content for the bottom visual slot
    _rebuild_visual()

    # Allow AppState.clear() (File > New) and explicit visual refreshes to reset the bottom area
    if hasattr(app_state, "register_visual_refresh"):
        app_state.register_visual_refresh(_rebuild_visual)

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

        # Rebuild the bottom visual (will show 112 faceplate only for qualifying racks,
        # otherwise falls back to the legacy main_content placeholder/behavior).
        _rebuild_visual()

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

    # The inspector_wrapper and visual_wrapper (and their rebuild functions) were already
    # created earlier so that both File > New and normal selection changes can
    # refresh them. The visual_wrapper internally shows the 112 rack visualization for
    # qualifying racks or falls back to the legacy main_content for everything else.
    right_panel = ft.Column(
        [
            inspector_wrapper,
            visual_wrapper,
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
