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
    AMPLIFIER_FIELDS,
    Device,
    RACK_FIELDS,
    get_fields_for_device,
)
from typing import Any
from src.ui.theme import (
    CARD_CONTENT_PADDING,
    CARD_ELEVATION_LOW,
    CARD_MARGIN,
    EMPTY_STATE_PADDING,
    FORM_SPACING,
)
from src.utils.feedback import show_coming_soon


# =============================================================================
# Special layout groups for Rack "Template / Signal" section
# Exactly as requested by the user for the 3-row compact grid
# =============================================================================

# Amp assignment slots (shown after the signal grid)
RACK_AMP_SLOTS = [f"Amp # {i}" for i in range(1, 17)]

# 1U custom fields
RACK_1U_FIELDS = ["1u A", "1u B"]


# =============================================================================
# Tab definitions for Rack Inspector
# These group all RACK_FIELDS into logical sections with tabs
# =============================================================================

RACK_TAB_CORE = ["Rack Location", "Rack #", "Template", "Rack Type"]

RACK_TAB_SIGNAL = [
    "Switch Config", "Off Ramp", "AES Input", "Analog Input",
    "Distro 1", "Distro 2",
    "Signal In", "Signal Thru", "Signal Out", "Signal Out 2",
    "Maps 1", "Maps 2", "Maps 3", "Maps 4", "Maps 5", "Maps 6",
]

RACK_TAB_AMPS = [f"Amp # {i}" for i in range(1, 17)]

RACK_TAB_1U = ["1u A", "1u B"]


def _attribute_tile(field_name: str, value: Any, color_scheme) -> ft.Container:
    """Compact visual tile for a single Rack attribute.

    Uses only color attributes that are known to exist reliably in Flet 0.85.x.
    """
    display_value = str(value) if value not in (None, "", "nan") else "—"

    # Safe color choices that work in their current Flet version
    label_color = getattr(color_scheme, "on_primary_container", None) or color_scheme.on_secondary_container
    value_color = getattr(color_scheme, "on_surface", None) or color_scheme.on_primary_container
    bg_color = getattr(color_scheme, "primary_container", None) or ft.Colors.GREY_100
    border_color = getattr(color_scheme, "outline", None) or ft.Colors.GREY_400

    return ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    field_name,
                    size=9,
                    weight=ft.FontWeight.W_600,
                    color=label_color,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    display_value,
                    size=11,
                    weight=ft.FontWeight.W_500,
                    color=value_color,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            spacing=1,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True,
        ),
        padding=ft.Padding.symmetric(horizontal=6, vertical=4),
        border=ft.Border(
            left=ft.BorderSide(width=1, color=border_color),
            top=ft.BorderSide(width=1, color=border_color),
            right=ft.BorderSide(width=1, color=border_color),
            bottom=ft.BorderSide(width=1, color=border_color),
        ),
        border_radius=4,
        bgcolor=bg_color,
        expand=True,
        alignment=ft.Alignment.CENTER,
    )


def _build_tab_content(field_names: list[str], props: dict, color_scheme) -> ft.Container:
    """Builds a scrollable, wrapped grid of attribute tiles for a tab section."""
    if not field_names:
        return ft.Container(
            content=ft.Text("No fields in this section.", italic=True, size=11),
            padding=10,
        )

    tiles = [_attribute_tile(name, props.get(name, ""), color_scheme) for name in field_names]

    return ft.Container(
        content=ft.Row(
            tiles,
            spacing=3,
            wrap=True,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        padding=ft.Padding.only(top=6, bottom=8, left=2, right=2),
        expand=True,
    )


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
        # Empty state
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
        # === Selected item display (Rack or Amplifier) ===
        item = app_state.selected_item
        display_name = str(item) if item else "Unknown"
        device_type = getattr(item, "device_type", "") or "Unknown"
        notes = getattr(item, "notes", "") or ""

        # Load properties (handle both dict and JSON string from DB)
        props = item.properties or {}
        if isinstance(props, str):
            try:
                import json
                props = json.loads(props)
            except Exception:
                props = {}

        # Icon for the header
        icon = ft.Icons.SETTINGS if device_type.lower() == "rack" else ft.Icons.SPEAKER

        # Assemble the inspector body
        inspector_body_children = [
            # Always show Inspector header + type/name
            ft.Text(
                "Inspector",
                size=15,
                weight=ft.FontWeight.BOLD,
                color=color_scheme.on_secondary_container,
            ),
            ft.Row(
                [
                    ft.Icon(icon, size=18, color=color_scheme.on_secondary_container),
                    ft.Text(
                        f"{device_type}: {display_name}",
                        weight=ft.FontWeight.W_500,
                        color=color_scheme.on_secondary_container,
                        expand=True,
                    ),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ]

        if device_type.lower() == "rack":
            # ============================================================
            # TABBED RACK INSPECTOR - All fields accessible via tabs
            # ============================================================

            # Build tab contents using compact tiles
            core_content = _build_tab_content(RACK_TAB_CORE, props, color_scheme)
            signal_content = _build_tab_content(RACK_TAB_SIGNAL, props, color_scheme)
            amps_content = _build_tab_content(RACK_TAB_AMPS, props, color_scheme)
            oneu_content = _build_tab_content(RACK_TAB_1U, props, color_scheme)

            tabs = ft.Tabs(
                selected_index=0,
                tabs=[
                    ft.Tab(
                        text="Core",
                        content=core_content,
                    ),
                    ft.Tab(
                        text="Signal Routing",
                        content=signal_content,
                    ),
                    ft.Tab(
                        text="Amp Assignments",
                        content=amps_content,
                    ),
                    ft.Tab(
                        text="1U Custom",
                        content=oneu_content,
                    ),
                ],
                expand=True,
                divider_color=color_scheme.outline,
            )

            # Wrap tabs so it can scroll and size correctly inside the inspector
            inspector_body_children.append(
                ft.Container(
                    content=tabs,
                    expand=True,
                    padding=ft.Padding.only(top=4),
                )
            )

        else:
            # ============================================================
            # GENERIC / AMPLIFIER LAYOUT (vertical list is still fine)
            # ============================================================
            fields = get_fields_for_device(item) or AMPLIFIER_FIELDS
            generic_fields = []
            for field_name in fields:
                value = props.get(field_name, "")
                generic_fields.append(
                    ft.TextField(
                        label=field_name,
                        value=str(value) if value is not None else "",
                        height=32,
                        text_size=11,
                        read_only=True,
                        dense=True,
                    )
                )

            inspector_body_children.append(
                ft.Container(
                    content=ft.Column(generic_fields, spacing=2, scroll=ft.ScrollMode.AUTO),
                    expand=True,
                    padding=ft.Padding.only(top=4, bottom=4),
                )
            )

        # Notes is always last for every device type
        inspector_body_children.append(
            ft.TextField(
                label="Notes",
                value=notes,
                height=60,
                text_size=11,
                multiline=True,
                read_only=True,
                dense=True,
            )
        )

        inspector_body = ft.Column(
            inspector_body_children,
            spacing=FORM_SPACING,
            expand=True,
        )

        content = ft.Container(
            content=inspector_body,
            padding=CARD_CONTENT_PADDING,
        )

    return ft.Card(
        content=content,
        bgcolor=color_scheme.secondary_container,
        elevation=CARD_ELEVATION_LOW,
        margin=CARD_MARGIN,
    )
