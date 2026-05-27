"""
Inspector Panel Component

Generic reusable panel typically placed on the right side.
Used to display and edit properties/details of the currently selected item.

This replaces the previous "Edit Selected" panel with a more generic name.
"""

import flet as ft
from src.ui.theme import CARD_CONTENT_PADDING, CARD_ELEVATION_LOW, CARD_MARGIN
from src.utils.feedback import show_coming_soon


def create_inspector_panel(page: ft.Page, app_state) -> ft.Card:
    """Creates the inspector / properties panel."""
    color_scheme = page.theme.color_scheme

    if not app_state.has_selection:
        content = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Inspector", size=15, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.Text(
                            "No item selected",
                            italic=True,
                            color=ft.Colors.GREY_600,
                        ),
                        padding=ft.Padding.only(top=30, bottom=30),
                        alignment=ft.Alignment.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=CARD_CONTENT_PADDING,
        )
    else:
        item = app_state.selected_item
        content = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Inspector", size=15, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        f"Editing: {item.get('name', 'Unknown')}",
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.TextField(
                        label="Name",
                        value=item.get("name", ""),
                        height=45,
                        text_size=14,
                    ),
                    ft.TextField(
                        label="Type",
                        value=item.get("type", ""),
                        height=45,
                        text_size=14,
                    ),
                    ft.ElevatedButton(
                        "Save Changes",
                        icon=ft.Icons.SAVE,
                        on_click=lambda e: show_coming_soon(page, "Save Changes"),
                    ),
                ],
                spacing=8,
            ),
            padding=CARD_CONTENT_PADDING,
        )

    return ft.Card(
        content=content,
        bgcolor=color_scheme.secondary_container,
        elevation=CARD_ELEVATION_LOW,
        margin=CARD_MARGIN,
    )
