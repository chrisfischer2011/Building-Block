"""
Inspector Panel Component

Generic reusable panel typically placed on the right side.
Used to display and edit properties/details of the currently selected item.

This replaces the previous "Edit Selected" panel with a more generic name.
"""

import flet as ft
import pandas as pd

from src.core.database import save_to_db
from src.core.models import DataEntry
from src.ui.theme import (
    CARD_CONTENT_PADDING,
    CARD_ELEVATION_LOW,
    CARD_MARGIN,
    EMPTY_STATE_PADDING,
    FORM_SPACING,
)
from src.utils.feedback import show_coming_soon


def create_inspector_panel(page: ft.Page, app_state) -> ft.Card:
    """Creates the inspector / properties panel.

    Supports three states:
    - Create mode (when app_state.is_creating is True)
    - Edit mode (when an item is selected)
    - Empty state (nothing selected)
    """
    color_scheme = page.theme.color_scheme

    # === CREATE MODE ===
    if app_state.is_creating:
        category_ref = ft.Ref[ft.TextField]()
        value_ref = ft.Ref[ft.TextField]()
        notes_ref = ft.Ref[ft.TextField]()

        def _create_entry(e):
            try:
                new_entry = DataEntry(
                    category=category_ref.current.value or "",
                    value=float(value_ref.current.value or 0),
                    notes=notes_ref.current.value or "",
                )
                # Save to database
                import pandas as pd
                df = pd.DataFrame([new_entry.to_dict()])
                save_to_db(df, "input_data")

                # Exit create mode and select the new item (approximate by clearing for now)
                app_state.finish_creating()
                # For better UX we would reload and select the new item.
                # For now we just refresh the UI.
                page.update()
            except Exception as ex:
                show_coming_soon(page, f"Create failed: {ex}")

        content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Create New Entry",
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color=color_scheme.on_secondary_container,
                    ),
                    ft.TextField(
                        label="Category",
                        ref=category_ref,
                        height=45,
                        text_size=14,
                    ),
                    ft.TextField(
                        label="Value",
                        ref=value_ref,
                        height=45,
                        text_size=14,
                    ),
                    ft.TextField(
                        label="Notes",
                        ref=notes_ref,
                        height=45,
                        text_size=14,
                        multiline=True,
                    ),
                    ft.ElevatedButton(
                        "Create Entry",
                        icon=ft.Icons.ADD,
                        on_click=_create_entry,
                    ),
                    ft.TextButton(
                        "Cancel",
                        on_click=lambda e: (app_state.finish_creating(), page.update()),
                    ),
                ],
                spacing=FORM_SPACING,
            ),
            padding=CARD_CONTENT_PADDING,
        )

        return ft.Card(
            content=content,
            bgcolor=color_scheme.secondary_container,
            elevation=CARD_ELEVATION_LOW,
            margin=CARD_MARGIN,
        )

    if not app_state.has_selection:
        content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Inspector", 
                        size=15, 
                        weight=ft.FontWeight.BOLD,
                        color=color_scheme.on_secondary_container,
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(
                                    ft.Icons.INFO_OUTLINE, 
                                    size=32, 
                                    color=color_scheme.on_secondary_container,
                                ),
                                ft.Text(
                                    "No item selected",
                                    size=14,
                                    color=color_scheme.on_secondary_container,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        padding=ft.Padding.only(top=EMPTY_STATE_PADDING, bottom=EMPTY_STATE_PADDING),
                        alignment=ft.Alignment.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=CARD_CONTENT_PADDING,
        )
    else:
        item = app_state.selected_item
        display_name = str(item) if item else "Unknown"
        content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Inspector", 
                        size=15, 
                        weight=ft.FontWeight.BOLD,
                        color=color_scheme.on_secondary_container,
                    ),
                    ft.Text(
                        f"Editing: {display_name}",
                        weight=ft.FontWeight.W_500,
                        color=color_scheme.on_secondary_container,
                    ),
                    ft.TextField(
                        label="Category",
                        value=item.category,
                        height=45,
                        text_size=14,
                    ),
                    ft.TextField(
                        label="Value",
                        value=str(item.value),
                        height=45,
                        text_size=14,
                    ),
                    ft.TextField(
                        label="Notes",
                        value=item.notes,
                        height=45,
                        text_size=14,
                        multiline=True,
                    ),
                    ft.ElevatedButton(
                        "Save Changes",
                        icon=ft.Icons.SAVE,
                        on_click=lambda e: show_coming_soon(page, "Save Changes"),
                    ),
                ],
                spacing=FORM_SPACING,
            ),
            padding=CARD_CONTENT_PADDING,
        )

    return ft.Card(
        content=content,
        bgcolor=color_scheme.secondary_container,
        elevation=CARD_ELEVATION_LOW,
        margin=CARD_MARGIN,
    )
