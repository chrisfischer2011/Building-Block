import flet as ft
from src.ui.theme import (
    CARD_CONTENT_PADDING,
    CARD_ELEVATION,
    CARD_ELEVATION_LOW,
    CARD_MARGIN,
    MAIN_CONTENT_SPACING,
    PANEL_SPACING,
)
from src.utils.helpers import show_coming_soon


def _create_left_panel(color_scheme) -> ft.Card:
    """Builds the left sidebar panel (Rack & Amp Selection)."""
    return ft.Card(
        content=ft.Container(
            content=ft.Text("Rack & Amp Selection", size=16, weight=ft.FontWeight.BOLD),
            padding=CARD_CONTENT_PADDING,
        ),
        bgcolor=color_scheme.primary_container,
        elevation=CARD_ELEVATION,
        margin=CARD_MARGIN,
    )


def _create_edit_selected_panel(color_scheme) -> ft.Card:
    """Builds the top-right panel for editing the currently selected item.

    Uses a fixed height as a placeholder sized for ~3 rows of editable fields.
    """
    return ft.Card(
        content=ft.Container(
            content=ft.Text("Edit Selected", size=15, weight=ft.FontWeight.BOLD),
            padding=CARD_CONTENT_PADDING,
            height=160,   # Placeholder height for ~3 rows of form fields + labels
        ),
        bgcolor=color_scheme.secondary_container,
        elevation=CARD_ELEVATION_LOW,
        margin=CARD_MARGIN,
    )


def _create_editable_area_panel(color_scheme) -> ft.Card:
    """Builds the main bottom-right editable content area."""
    return ft.Card(
        content=ft.Container(
            content=ft.Text("Editable Area", size=16, weight=ft.FontWeight.BOLD),
            padding=CARD_CONTENT_PADDING,
        ),
        bgcolor=color_scheme.tertiary_container,
        elevation=CARD_ELEVATION_LOW,
        margin=CARD_MARGIN,
        expand=True,
    )


def _create_right_panel(color_scheme) -> ft.Column:
    """Builds the combined right-side column (Edit Selected + Editable Area)."""
    return ft.Column(
        [
            _create_edit_selected_panel(color_scheme),
            _create_editable_area_panel(color_scheme),
        ],
        spacing=PANEL_SPACING,
        expand=True,   # Right side takes remaining space
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        margin=CARD_MARGIN,
    )


def create_main_layout(page: ft.Page) -> ft.Row:
    """Returns the main content area layout with a resizable left sidebar.

    The left panel ("Rack & Amp Selection") can now be resized horizontally
    by dragging the divider between it and the right panels.
    """
    color_scheme = page.theme.color_scheme

    # Initial width of the left sidebar
    left_width = 280

    # Container that will hold the left panel and control its width
    left_container = ft.Container(
        content=_create_left_panel(color_scheme),
        width=left_width,
    )

    # Track starting position for drag calculations (Flet 0.85 compatible)
    drag_start_x = 0

    def on_pan_start(e):
        """Record the starting position when drag begins."""
        nonlocal drag_start_x
        drag_start_x = e.global_x

    def on_pan_update(e):
        """Handle horizontal dragging of the splitter."""
        nonlocal left_width, drag_start_x
        # Calculate delta using global position (compatible with Flet 0.85)
        delta = e.global_x - drag_start_x
        drag_start_x = e.global_x

        # Constrain the left panel between 180px and 500px
        new_width = left_width + delta
        left_width = max(180, min(500, new_width))
        left_container.width = left_width
        page.update()

    # Thin vertical divider that acts as the splitter
    divider = ft.GestureDetector(
        content=ft.Container(
            width=8,
            bgcolor=ft.Colors.GREY_400,
        ),
        drag_interval=10,
        on_pan_start=on_pan_start,
        on_pan_update=on_pan_update,
        mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
    )

    right_panel = _create_right_panel(color_scheme)

    return ft.Row(
        [left_container, divider, right_panel],
        spacing=0,  # We control spacing via the divider
        expand=True,
        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
    )