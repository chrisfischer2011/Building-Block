"""
Inspector Panel Component

Generic reusable panel typically placed on the right side.
Used to display and edit properties/details of the currently selected item.

This replaces the previous "Edit Selected" panel with a more generic name.
"""

import flet as ft
import pandas as pd

from src.core.database import save_to_db
from src.core.models import Device, get_fields_for_device, get_options_for_field
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
        device_type_ref = ft.Ref[ft.Dropdown]()
        name_ref = ft.Ref[ft.TextField]()
        dynamic_fields_container = ft.Ref[ft.Container]()

        # We will store values in this dict instead of relying only on refs
        # because some fields are Dropdowns (which don't use the same ref pattern easily)
        dynamic_field_values: dict[str, str] = {}

        def _update_field_value(field_name: str, value: str):
            dynamic_field_values[field_name] = value or ""

        def _rebuild_dynamic_fields(device_type: str):
            """Rebuild the list of fields based on the selected device type."""
            fields = get_fields_for_device(device_type)
            controls = []
            dynamic_field_values.clear()

            for field_name in fields:
                options = get_options_for_field(field_name)

                if options:
                    # Dropdown
                    dropdown = ft.Dropdown(
                        label=field_name,
                        options=[ft.dropdown.Option(o) for o in options],
                        height=50,
                        on_change=lambda e, fname=field_name: _update_field_value(fname, e.control.value),
                    )
                    controls.append(dropdown)
                else:
                    # Free text
                    ref = ft.Ref[ft.TextField]()
                    dynamic_field_values[field_name] = ""

                    def make_on_change(fname, r):
                        def handler(e):
                            if r.current:
                                _update_field_value(fname, r.current.value)
                        return handler

                    controls.append(
                        ft.TextField(
                            ref=ref,
                            label=field_name,
                            height=45,
                            text_size=14,
                            on_change=make_on_change(field_name, ref),
                        )
                    )

            if dynamic_fields_container.current:
                dynamic_fields_container.current.content = ft.Column(controls, spacing=6)
                dynamic_fields_container.current.update()

        def _on_device_type_change(e):
            _rebuild_dynamic_fields(device_type_ref.current.value or "Rack")

        def _create_entry(e):
            try:
                dev_type = device_type_ref.current.value or "Rack"
                name = name_ref.current.value or ""

                # Capture any remaining TextField values
                for fname, ref in list(dynamic_field_values.items()):
                    # This is a bit hacky but works for mixed controls
                    pass

                new_device = Device(
                    name=name,
                    device_type=dev_type,
                    properties=dynamic_field_values.copy(),
                    notes="",
                )

                df = pd.DataFrame([new_device.to_dict()])
                save_to_db(df, "input_data")

                app_state.finish_creating()
                page.update()
            except Exception as ex:
                show_coming_soon(page, f"Create failed: {ex}")

        # Initial fields for default selection ("Rack")
        initial_fields = get_fields_for_device("Rack")
        initial_controls = []
        for field_name in initial_fields:
            options = get_options_for_field(field_name)
            if options:
                initial_controls.append(ft.Dropdown(
                    label=field_name,
                    options=[ft.dropdown.Option(o) for o in options],
                    height=50,
                    on_change=lambda e, fname=field_name: _update_field_value(fname, e.control.value),
                ))
            else:
                ref = ft.Ref[ft.TextField]()
                dynamic_field_values[field_name] = ""

                def make_handler(fname, r):
                    def handler(e):
                        if r.current:
                            _update_field_value(fname, r.current.value)
                    return handler

                initial_controls.append(ft.TextField(
                    ref=ref,
                    label=field_name,
                    height=45,
                    text_size=14,
                    on_change=make_handler(field_name, ref),
                ))

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
                        on_change=_on_device_type_change,
                    ),
                    ft.TextField(
                        ref=name_ref,
                        label="Name / Identifier",
                        height=45,
                        text_size=14,
                    ),
                    ft.Container(
                        ref=dynamic_fields_container,
                        content=ft.Column(initial_controls, spacing=6),
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
                        f"Editing {item.device_type}: {display_name}",
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
