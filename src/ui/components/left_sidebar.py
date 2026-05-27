"""
Left Sidebar Component

Generic reusable left sidebar panel. Typically used for navigation,
item lists, or selectors.

This is the generic version of what was previously the Rack & Amp selector.
"""

import flet as ft
from src.ui.theme import CARD_CONTENT_PADDING, CARD_ELEVATION, CARD_MARGIN


# Temporary sample data for Phase 5
# In real applications this would come from AppState or a data service.
SAMPLE_ITEMS = [
    {"id": 1, "name": "Rack A1", "type": "Rack"},
    {"id": 2, "name": "Rack B2", "type": "Rack"},
    {"id": 3, "name": "Amp X-500", "type": "Amplifier"},
    {"id": 4, "name": "Amp Pro-200", "type": "Amplifier"},
    {"id": 5, "name": "Rack C3", "type": "Rack"},
    {"id": 6, "name": "Amp Mini-100", "type": "Amplifier"},
]


def create_left_sidebar(
    page: ft.Page,
    app_state,
    on_selection_changed: callable = None,
) -> ft.Card:
    """
    Creates the left sidebar panel.

    Args:
        page: Current Flet page
        app_state: Shared AppState instance
        on_selection_changed: Optional callback after selection changes
    """
    color_scheme = page.theme.color_scheme

    search_field = ft.TextField(
        label="Search",
        prefix_icon=ft.Icons.SEARCH,
        height=40,
        text_size=14,
        on_change=lambda e: _filter_list(e, items_column, app_state),
    )

    items_column = ft.Column(
        spacing=4,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    _rebuild_item_list(items_column, SAMPLE_ITEMS, page, app_state, on_selection_changed)

    content = ft.Container(
        content=ft.Column(
            [
                ft.Text("Items", size=16, weight=ft.FontWeight.BOLD),
                search_field,
                ft.Container(
                    content=items_column,
                    expand=True,
                    padding=ft.Padding.only(top=8),
                ),
            ],
            expand=True,
        ),
        padding=CARD_CONTENT_PADDING,
    )

    return ft.Card(
        content=content,
        bgcolor=color_scheme.primary_container,
        elevation=CARD_ELEVATION,
        margin=CARD_MARGIN,
        expand=True,
    )


def _rebuild_item_list(
    column: ft.Column,
    items: list,
    page: ft.Page,
    app_state,
    on_selection_changed: callable,
):
    """Rebuild the list of selectable items. 
    Does NOT call .update() — caller is responsible after the control is mounted.
    """
    column.controls.clear()

    for item in items:
        is_selected = (
            app_state.selected_item
            and app_state.selected_item.get("id") == item["id"]
        )

        tile = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        ft.Icons.SETTINGS if item["type"] == "Rack" else ft.Icons.SPEAKER,
                        size=18,
                    ),
                    ft.Text(item["name"], expand=True),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.only(top=6, bottom=6, left=8, right=8),
            bgcolor=ft.Colors.BLUE_100 if is_selected else ft.Colors.TRANSPARENT,
            border_radius=6,
            on_click=lambda e, it=item: _on_item_clicked(
                it, page, app_state, column, on_selection_changed
            ),
        )
        column.controls.append(tile)


def _on_item_clicked(item: dict, page: ft.Page, app_state, column: ft.Column, callback):
    """Handle clicking an item in the list."""
    app_state.select_item(item)

    # Rebuild the list so the visual selection updates
    _rebuild_item_list(column, SAMPLE_ITEMS, page, app_state, callback)

    # Now safe to update because the column is already mounted on the page
    column.update()

    if callback:
        callback(item)


def _filter_list(e, column: ft.Column, app_state):
    """Basic filtering placeholder for Phase 5."""
    pass
