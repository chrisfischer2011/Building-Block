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

    TEMP DEBUG VERSION: Large text, fixed width, no expand to avoid layout collapse in tabs.
    """
    display_value = str(value) if value not in (None, "", "nan") else "—"

    label_color = ft.Colors.BLACK
    value_color = ft.Colors.DARK_BLUE

    return ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    field_name,
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=label_color,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    display_value,
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=value_color,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True,
        ),
        width=110,                    # Fixed width instead of expand
        padding=ft.Padding.symmetric(horizontal=6, vertical=5),
        border=ft.Border(
            left=ft.BorderSide(width=2, color=ft.Colors.BLACK),
            top=ft.BorderSide(width=2, color=ft.Colors.BLACK),
            right=ft.BorderSide(width=2, color=ft.Colors.BLACK),
            bottom=ft.BorderSide(width=2, color=ft.Colors.BLACK),
        ),
        border_radius=6,
        bgcolor=ft.Colors.YELLOW_100,
        alignment=ft.Alignment.CENTER,
    )


def _build_tab_content(field_names: list[str], props: dict, color_scheme) -> ft.Container:
    """Builds scrollable tab content using compact tiles for the Rack inspector."""
    if not field_names:
        return ft.Container(
            content=ft.Text("No fields in this section.", italic=True, size=11),
            padding=10,
        )

    tiles = [_attribute_tile(name, props.get(name, ""), color_scheme) for name in field_names]
    print(f"[INSPECTOR DEBUG]   Created {len(tiles)} tiles for section")

    # Wrap the tiles row in a scrollable Column for better behavior inside Tabs
    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    tiles,
                    spacing=3,
                    wrap=True,
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
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
        # Compact header: "Inspector" + selected item info on the same row
        header_row = ft.Row(
            [
                ft.Text(
                    "Inspector",
                    size=15,
                    weight=ft.FontWeight.BOLD,
                    color=color_scheme.on_secondary_container,
                ),
                ft.Container(width=12),  # small spacer
                ft.Icon(icon, size=16, color=color_scheme.on_secondary_container),
                ft.Text(
                    f"{device_type}: {display_name}",
                    weight=ft.FontWeight.W_500,
                    color=color_scheme.on_secondary_container,
                ),
            ],
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        inspector_body_children = [header_row]

        if device_type.lower() == "rack":
            # === New compact header with tabs integrated + underlined ===
            # Tabs: Core | Signal Routing | Amp Assignments (1U merged in)

            core_content = _build_tab_content(RACK_TAB_CORE, props, color_scheme)
            signal_content = _build_tab_content(RACK_TAB_SIGNAL, props, color_scheme)

            # Combine Amp Assignments + 1U Custom into one tab
            amps_content = _build_tab_content(RACK_TAB_AMPS, props, color_scheme)
            oneu_content = _build_tab_content(RACK_TAB_1U, props, color_scheme)

            print(f"[INSPECTOR DEBUG] Building tab contents for {display_name}")
            # Better counting: look inside the debug wrappers
            def count_tiles(c):
                if not c: return 0
                inner = getattr(c, 'content', c)
                if hasattr(inner, 'controls'):
                    for child in inner.controls:
                        if hasattr(child, 'controls'):
                            return len(child.controls)
                return 0
            print(f"  Core tiles:     {count_tiles(core_content)}")
            print(f"  Signal tiles:   {count_tiles(signal_content)}")
            print(f"  Amp tiles:      {count_tiles(amps_content)}")
            print(f"  1U tiles:       {count_tiles(oneu_content)}")

            # TEMP: Give each tab content a different light background so we can see them clearly
            core_debug = ft.Container(
                content=core_content,
                bgcolor=ft.Colors.GREEN_50,
                padding=4,
                expand=True,
            )
            signal_debug = ft.Container(
                content=signal_content,
                bgcolor=ft.Colors.ORANGE_50,
                padding=4,
                expand=True,
            )
            amp_plus_1u_content = ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Amp Assignments", size=10, weight=ft.FontWeight.W_600,
                                color=color_scheme.on_secondary_container),
                        amps_content,
                        ft.Text("1U Custom", size=10, weight=ft.FontWeight.W_600,
                                color=color_scheme.on_secondary_container),
                        oneu_content,
                    ],
                    spacing=6,
                    scroll=ft.ScrollMode.AUTO,
                ),
                bgcolor=ft.Colors.PURPLE_50,
                padding=4,
                expand=True,
            )

            tab_contents = [core_debug, signal_debug, amp_plus_1u_content]
            tab_labels = ["Core", "Signal Routing", "Amp Assignments"]
            selected_tab = [0]   # mutable index for live switching

            # Content area must be created BEFORE the buttons (closure safety)
            # TEMP DEBUG WRAPPER - bright background + border so we can see the real content bounds
            content_area = ft.Container(
                content=tab_contents[selected_tab[0]],
                expand=True,
                padding=ft.Padding.only(top=4, bottom=4),
                bgcolor=ft.Colors.LIGHT_BLUE_100,
                border=ft.Border(
                    left=ft.BorderSide(width=3, color=ft.Colors.BLUE),
                    right=ft.BorderSide(width=3, color=ft.Colors.BLUE),
                    top=ft.BorderSide(width=3, color=ft.Colors.BLUE),
                    bottom=ft.BorderSide(width=3, color=ft.Colors.BLUE),
                ),
            )

            # We need a container for the header so we can rebuild it when tabs change
            header_container = ft.Container()

            def rebuild_header():
                """Rebuilds the header row with correct tab button states."""
                tab_buttons = []
                for i, label in enumerate(tab_labels):
                    is_selected = (i == selected_tab[0])

                    def make_switcher(idx):
                        def _switch(e):
                            selected_tab[0] = idx
                            content_area.content = tab_contents[selected_tab[0]]
                            rebuild_header()           # refresh tab highlights
                            try:
                                header_container.update()
                                content_area.update()
                            except Exception:
                                pass
                        return _switch

                    btn = ft.Container(
                        content=ft.Text(
                            label,
                            size=13,
                            weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.W_600,
                            color=color_scheme.on_primary_container if is_selected else color_scheme.on_secondary_container,
                        ),
                        padding=ft.Padding.symmetric(horizontal=12, vertical=4),
                        bgcolor=color_scheme.primary_container if is_selected else ft.Colors.TRANSPARENT,
                        border_radius=4,
                        on_click=make_switcher(i),
                        tooltip=f"Show {label}",
                    )
                    tab_buttons.append(btn)

                compact_header = ft.Row(
                    [
                        ft.Text(
                            "Inspector",
                            size=15,
                            weight=ft.FontWeight.BOLD,
                            color=color_scheme.on_secondary_container,
                        ),
                        ft.Container(width=8),
                        ft.Icon(icon, size=15, color=color_scheme.on_secondary_container),
                        ft.Text(
                            f"{device_type}: {display_name}",
                            weight=ft.FontWeight.W_500,
                            color=color_scheme.on_secondary_container,
                        ),
                        ft.Container(expand=True),
                        *tab_buttons,
                    ],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )

                header_container.content = compact_header

            # Initial header build
            rebuild_header()

            # Underline for the entire header row
            header_underline = ft.Container(
                height=1,
                bgcolor=color_scheme.outline,
                margin=ft.Padding.only(bottom=6),
            )

            inspector_body_children = [
                header_container,
                header_underline,
                content_area,
            ]

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

        inspector_body = ft.Column(
            inspector_body_children,
            spacing=FORM_SPACING,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,   # Critical: makes children fill full width
        )

        content = ft.Container(
            content=inspector_body,
            padding=CARD_CONTENT_PADDING,
            expand=True,   # Help the content fill the Card width
        )

    return ft.Card(
        content=content,
        bgcolor=color_scheme.secondary_container,
        elevation=CARD_ELEVATION_LOW,
        margin=CARD_MARGIN,
    )
