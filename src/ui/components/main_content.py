"""
Main Content Component

Generic reusable main working area, usually taking the majority of the screen.
This is where the primary editing, viewing, or interaction happens.

Replaces the previous "Editable Area".
"""

import flet as ft
from src.ui.theme import CARD_CONTENT_PADDING, CARD_ELEVATION_LOW, CARD_MARGIN
from src.utils.feedback import show_coming_soon


def create_main_content(page: ft.Page, app_state) -> ft.Card:
    """Creates the main content / workspace area."""
    color_scheme = page.theme.color_scheme

    if not app_state.has_selection:
        inner_content = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.INBOX, size=48, color=ft.Colors.GREY_400),
                    ft.Text(
                        "Select an item from the sidebar",
                        size=14,
                        color=ft.Colors.GREY_600,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
        )
    else:
        item = app_state.selected_item
        inner_content = ft.Column(
            [
                ft.Text(f"Details for {item.get('name')}", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(
                    "This area will contain configuration, measurements, "
                    "notes, and other editable content.",
                    size=13,
                ),
                ft.ElevatedButton(
                    "Open Advanced Editor",
                    icon=ft.Icons.OPEN_IN_NEW,
                    on_click=lambda e: show_coming_soon(page, "Advanced Editor"),
                ),
            ],
            spacing=10,
        )

    return ft.Card(
        content=ft.Container(
            content=inner_content,
            padding=CARD_CONTENT_PADDING,
            expand=True,
        ),
        bgcolor=color_scheme.tertiary_container,
        elevation=CARD_ELEVATION_LOW,
        margin=CARD_MARGIN,
        expand=True,
    )
