"""
Inspector Panel Component

Generic reusable panel typically placed on the right side.
Used to display and edit properties/details of the currently selected item.

This replaces the previous "Edit Selected" panel with a more generic name.
"""

import flet as ft
import pandas as pd

from src.core.database import save_to_db
from src.core.models import (
    CORE_RACK_FIELDS,
    Device,
    RACK_FIELDS,
    get_fields_for_device,
    get_options_for_field,
)
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

    # === CREATE MODE (Simplified for testing) ===
    if app_state.is_creating:
        device_type_ref = ft.Ref[ft.Dropdown]()
        name_ref = ft.Ref[ft.TextField]()

        # Simple storage for field values during create
        create_values: dict[str, str] = {}

        def _create_entry(e):
            try:
                dev_type = device_type_ref.current.value or "Rack"
                name = name_ref.current.value or "New Device"

                new_device = Device(
                    name=name,
                    device_type=dev_type,
                    properties=create_values.copy(),
                    notes="",
                )

                df = pd.DataFrame([new_device.to_dict()])
                save_to_db(df, "input_data")

                app_state.finish_creating()
                page.update()
            except Exception as ex:
                show_coming_soon(page, f"Create failed: {ex}")

        # Basic fields for now (we'll refine this in the testing phase)
        content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Create New Device",
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color=color_scheme.on_secondary_container,
                    ),
                    ft.Dropdown(
                        ref=device_type_ref,
                        label="Device Type",
                        options=[
                            ft.dropdown.Option("Rack"),
                            ft.dropdown.Option("Amplifier"),
                        ],
                        value="Rack",
                        height=50,
                    ),
                    ft.TextField(
                        ref=name_ref,
                        label="Name / Identifier",
                        height=45,
                        text_size=14,
                    ),
                    # Placeholder note for now
                    ft.Text(
                        "(Full type-specific fields coming in next refinements)",
                        size=12,
                        italic=True,
                        color=ft.Colors.GREY_500,
                    ),
                    ft.ElevatedButton(
                        "Create Device",
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

        if item and getattr(item, 'device_type', None) == "Rack":
            # Rich Rack view
            field_controls = []
            props = item.properties or {}

            # Handle case where properties might be a JSON string
            if isinstance(props, str):
                try:
                    import json
                    props = json.loads(props)
                except Exception:
                    props = {}

            for field_name in RACK_FIELDS:
                value = props.get(field_name, "")
                field_controls.append(
                    ft.TextField(
                        label=field_name,
                        value=str(value) if value is not None else "",
                        height=40,
                        text_size=13,
                        read_only=True,
                    )
                )

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
                            f"Rack: {display_name}",
                            weight=ft.FontWeight.W_500,
                            color=color_scheme.on_secondary_container,
                        ),
                        ft.Column(field_controls, spacing=4, scroll=ft.ScrollMode.AUTO),
                    ],
                    spacing=FORM_SPACING,
                ),
                padding=CARD_CONTENT_PADDING,
            )
        else:
            # Fallback / generic view
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
                            f"Editing {getattr(item, 'device_type', 'Unknown')}: {display_name}",
                            weight=ft.FontWeight.W_500,
                            color=color_scheme.on_secondary_container,
                        ),
                        ft.TextField(label="Category", value=getattr(item, 'category', ''), height=45, text_size=14, read_only=True),
                        ft.TextField(label="Value", value=str(getattr(item, 'value', '')), height=45, text_size=14, read_only=True),
                        ft.TextField(label="Notes", value=getattr(item, 'notes', ''), height=45, text_size=14, multiline=True, read_only=True),
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
