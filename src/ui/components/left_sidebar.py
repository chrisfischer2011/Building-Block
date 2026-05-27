"""
Left Sidebar Component

Generic reusable left sidebar panel. Typically used for navigation,
item lists, or selectors.

This is the generic version of what was previously the Rack & Amp selector.
"""

import flet as ft
import pandas as pd

from src.core.database import load_from_db, save_to_db
from src.core.models import DataEntry
from src.ui.theme import (
    CARD_CONTENT_PADDING,
    CARD_ELEVATION,
    CARD_MARGIN,
    LIST_ITEM_SPACING,
)


def _get_seed_data() -> list[DataEntry]:
    """Return some initial sample data when the database is empty."""
    return [
        DataEntry(id=1, category="Rack", value=1200, notes="Main rack A1"),
        DataEntry(id=2, category="Rack", value=950, notes="Rack B2"),
        DataEntry(id=3, category="Amplifier", value=450, notes="Amp X-500"),
        DataEntry(id=4, category="Amplifier", value=780, notes="Amp Pro-200"),
        DataEntry(id=5, category="Rack", value=1100, notes="Rack C3"),
        DataEntry(id=6, category="Amplifier", value=320, notes="Amp Mini-100"),
    ]


def create_left_sidebar(
    page: ft.Page,
    app_state,
    on_selection_changed: callable = None,
) -> ft.Card:
    """
    Creates the left sidebar panel.

    Loads data directly from the database (Phase 6).
    """
    color_scheme = page.theme.color_scheme

    # Load real data from database
    try:
        df = load_from_db("input_data")
        items: list[DataEntry] = [DataEntry.from_dict(row) for _, row in df.iterrows()]
    except Exception:
        items = []

    # If database is empty, seed some sample data for first run (and save it)
    if not items:
        items = _get_seed_data()
        try:
            seed_df = pd.DataFrame([item.to_dict() for item in items])
            save_to_db(seed_df, "input_data")
        except Exception:
            pass  # Seeding failed, but we still show the items in memory

    search_field = ft.TextField(
        label="Search",
        prefix_icon=ft.Icons.SEARCH,
        height=40,
        text_size=14,
        on_change=lambda e: _filter_list(e, items_column, app_state),
    )

    items_column = ft.Column(
        spacing=LIST_ITEM_SPACING,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    _rebuild_item_list(
        items_column, 
        items, 
        page, 
        app_state, 
        on_selection_changed,
        text_color=color_scheme.on_primary_container,
    )

    content = ft.Container(
        content=ft.Column(
            [
                # Header with title + Add button
                ft.Row(
                    [
                        ft.Text(
                            "Items",
                            size=15,
                            weight=ft.FontWeight.BOLD,
                            color=color_scheme.on_primary_container,
                            expand=True,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.ADD,
                            icon_size=20,
                            tooltip="Add New Entry",
                            on_click=lambda e: (app_state.start_creating(), page.update()),
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                search_field,
                ft.Container(
                    content=items_column,
                    expand=True,
                    padding=ft.Padding.only(top=10),  # Better spacing after search field
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
    text_color: str = None,
):
    """Rebuild the list of selectable items. 
    Does NOT call .update() — caller is responsible after the control is mounted.
    """
    column.controls.clear()

    for item in items:
        is_selected = (
            app_state.selected_item is not None
            and app_state.selected_item.id == item.id
        )

        display_name = f"{item.category} - {item.value}"
        icon = ft.Icons.SETTINGS if item.category.lower() == "rack" else ft.Icons.SPEAKER

        tile = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, size=18, color=text_color),
                    ft.Text(display_name, expand=True, color=text_color),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.only(top=8, bottom=8, left=10, right=10),
            bgcolor=ft.Colors.BLUE_100 if is_selected else ft.Colors.TRANSPARENT,
            border_radius=6,
            on_click=lambda e, it=item: _on_item_clicked(
                it, page, app_state, column, on_selection_changed, text_color=text_color
            ),
        )
        column.controls.append(tile)


def _on_item_clicked(item, page: ft.Page, app_state, column: ft.Column, callback, text_color=None):
    """Handle clicking an item in the list."""
    app_state.select_item(item)

    # Reload data from DB so the list stays in sync
    try:
        df = load_from_db("input_data")
        current_items = [DataEntry.from_dict(row) for _, row in df.iterrows()]
    except Exception:
        current_items = _get_seed_data()

    # Rebuild the list so the visual selection updates
    _rebuild_item_list(column, current_items, page, app_state, callback, text_color=text_color)

    # Now safe to update because the column is already mounted on the page
    column.update()

    if callback:
        callback(item)


def _filter_list(e, column: ft.Column, app_state):
    """Basic filtering placeholder for Phase 5."""
    pass
