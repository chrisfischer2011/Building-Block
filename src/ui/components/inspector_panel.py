"""
Inspector Panel Component

Generic reusable panel typically placed on the right side.
Used to display and edit properties/details of the currently selected item.

This replaces the previous "Edit Selected" panel with a more generic name.
"""

import flet as ft
import pandas as pd

from src.core.database import load_from_db, overwrite_data, save_to_db
from src.core.models import (
    AMPLIFIER_FIELDS,
    DataEntry,
    Device,
    RACK_FIELDS,
    get_fields_for_device,
    get_options_for_field,
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


def _attribute_tile(field_name: str, value: Any, color_scheme, on_value_changed=None) -> ft.Container:
    """Compact visual tile for a single Rack attribute (label on top, value below).
    Renders as Dropdown if the field has options in DEVICE_FIELD_OPTIONS, else TextField.
    Saves on blur / submit (enter/tab) via the provided callback.
    """
    display_value = str(value) if value is not None else ""

    label = ft.Text(
        field_name,
        size=9,
        weight=ft.FontWeight.BOLD,
        color=color_scheme.on_secondary_container,
        text_align=ft.TextAlign.CENTER,
    )

    options = get_options_for_field(field_name)

    if on_value_changed and options:
        # Dropdown for fields with predefined choices
        value_ctrl = ft.Dropdown(
            value=display_value if display_value else None,
            options=[ft.dropdown.Option(str(o)) for o in options],
            dense=True,
            text_size=11,
            height=32,
            on_select=lambda e, fn=field_name: on_value_changed(fn, getattr(e, 'data', None) or getattr(getattr(e, 'control', None), 'value', None)),
            border_color=color_scheme.outline,
            focused_border_color=color_scheme.primary,
            content_padding=ft.Padding.only(left=4, right=4, top=2, bottom=2),
        )
    elif on_value_changed:
        # Free text
        value_ctrl = ft.TextField(
            value=display_value,
            dense=True,
            text_size=11,
            height=28,
            on_submit=lambda e, fn=field_name: on_value_changed(fn, e.control.value),
            on_blur=lambda e, fn=field_name: on_value_changed(fn, e.control.value),
            border_color=color_scheme.outline,
            focused_border_color=color_scheme.primary,
            content_padding=ft.Padding.only(left=4, right=4, top=2, bottom=2),
        )
    else:
        value_ctrl = ft.Text(
            display_value,
            size=11,
            weight=ft.FontWeight.W_500,
            color=color_scheme.on_secondary_container,
            text_align=ft.TextAlign.CENTER,
        )

    return ft.Container(
        content=ft.Column(
            [
                label,
                value_ctrl,
            ],
            spacing=1,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True,
        ),
        width=110,
        padding=ft.Padding.symmetric(horizontal=4, vertical=3),
        border=ft.Border(
            left=ft.BorderSide(width=1, color=color_scheme.outline),
            top=ft.BorderSide(width=1, color=color_scheme.outline),
            right=ft.BorderSide(width=1, color=color_scheme.outline),
            bottom=ft.BorderSide(width=1, color=color_scheme.outline),
        ),
        border_radius=4,
        bgcolor=color_scheme.primary_container,
        alignment=ft.Alignment.CENTER,
    )


def _build_tab_content(field_names: list[str], props: dict, color_scheme, on_value_changed=None) -> ft.Container:
    """Builds scrollable tab content using compact tiles for the Rack inspector."""
    if not field_names:
        return ft.Container(
            content=ft.Text("No fields in this section.", italic=True, size=11),
            padding=10,
        )

    tiles = [_attribute_tile(name, props.get(name, ""), color_scheme, on_value_changed=on_value_changed) for name in field_names]

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

        # Holder (populated only for racks) so edits can refresh the tab contents list
        _rack_refresh_state = {"contents": None, "selected": [0], "area": None}

        def _save_field(field_name: str, new_value: str):
            """Update the selected item's property and persist to DB.
            Triggered on TextField blur or submit (enter/tab).
            """
            if not app_state.selected_item:
                return
            item = app_state.selected_item
            if item.properties is None:
                item.properties = {}
            if str(item.properties.get(field_name, "")) == str(new_value or ""):
                return  # no change
            item.properties[field_name] = new_value or ""

            try:
                # Load current state, replace this item, overwrite DB
                df = load_from_db("input_data")
                current_items = []
                replaced = False
                for _, row in df.iterrows():
                    # Do not do "if not row" — row is pandas Series (causes "truth value of a Series is ambiguous")
                    it = DataEntry.from_dict(row)
                    if it:
                        # Match by id if available, else by name + device_type
                        if (item.id is not None and it.id == item.id) or \
                           (item.id is None and it.name == item.name and it.device_type == item.device_type):
                            # mutate the freshly loaded it with the edit
                            it.properties = dict(item.properties) if item.properties else {}
                            current_items.append(it)
                            replaced = True
                        else:
                            current_items.append(it)
                if not replaced:
                    current_items.append(item)  # or a copy, but ok

                overwrite_data(current_items)

                # For rack inspectors: re-build the tab contents from the *current* props so that
                # switching tabs after an edit shows fresh data in the other tabs.
                if _rack_refresh_state.get("contents") and _rack_refresh_state.get("area"):
                    try:
                        c0 = _build_tab_content(RACK_TAB_CORE, item.properties or {}, color_scheme, on_value_changed=_save_field)
                        c1 = _build_tab_content(RACK_TAB_SIGNAL, item.properties or {}, color_scheme, on_value_changed=_save_field)
                        c2f = RACK_TAB_AMPS + RACK_TAB_1U
                        c2 = _build_tab_content(c2f, item.properties or {}, color_scheme, on_value_changed=_save_field)
                        _rack_refresh_state["contents"][:] = [c0, c1, c2]
                        _rack_refresh_state["area"].content = _rack_refresh_state["contents"][_rack_refresh_state["selected"][0]]
                        _rack_refresh_state["area"].update()
                    except Exception:
                        pass

                # Try to refresh sidebar list if callbacks registered (from AppState)
                # Pass False so it does NOT auto-select latest (we want to keep current selection)
                if hasattr(app_state, "_sidebar_refresh_callbacks"):
                    for cb in list(getattr(app_state, "_sidebar_refresh_callbacks", [])):
                        try:
                            cb(auto_select_latest=False)
                        except Exception:
                            pass
            except Exception as ex:
                print(f"Save failed for {field_name}: {ex}")

        # Icon for the header
        icon = ft.Icons.SETTINGS if device_type.lower() == "rack" else ft.Icons.SPEAKER

        inspector_body_children = []

        if device_type.lower() == "rack":
            # === Clean compact header with tabs integrated in the row + underline ===
            # Tabs: Core | Signal Routing | Amp Assignments (1U fields inline in 3rd tab)

            core_content = _build_tab_content(RACK_TAB_CORE, props, color_scheme, on_value_changed=_save_field)
            signal_content = _build_tab_content(RACK_TAB_SIGNAL, props, color_scheme, on_value_changed=_save_field)

            # 3rd tab: Amp Assignments + 1U Custom fields all in one flat wrapped grid
            # (so the 2 1U fields appear inline with the other Amp fields)
            third_tab_fields = RACK_TAB_AMPS + RACK_TAB_1U
            third_tab_content = _build_tab_content(third_tab_fields, props, color_scheme, on_value_changed=_save_field)

            tab_contents = [core_content, signal_content, third_tab_content]
            tab_labels = ["Core", "Signal Routing", "Amp Assignments"]  # 3rd tab includes 1U fields inline
            selected_tab = [0]   # mutable index for live switching

            # Content area (updated live on tab click)
            content_area = ft.Container(
                content=tab_contents[selected_tab[0]],
                expand=True,
                padding=ft.Padding.only(top=4, bottom=4),
            )

            # Populate holder so future saves can refresh the tab contents from updated props
            _rack_refresh_state["contents"] = tab_contents
            _rack_refresh_state["selected"] = selected_tab
            _rack_refresh_state["area"] = content_area

            # Build the header row with tab buttons that update in place
            tab_button_controls = []

            def make_switcher(idx):
                def _switch(e):
                    selected_tab[0] = idx
                    content_area.content = tab_contents[selected_tab[0]]
                    # Update button styles for highlight
                    for j, btn in enumerate(tab_button_controls):
                        is_sel = (j == selected_tab[0])
                        btn.bgcolor = color_scheme.primary_container if is_sel else ft.Colors.TRANSPARENT
                        txt = btn.content
                        if isinstance(txt, ft.Text):
                            txt.weight = ft.FontWeight.BOLD if is_sel else ft.FontWeight.W_600
                            txt.color = color_scheme.on_primary_container if is_sel else color_scheme.on_secondary_container
                        try:
                            btn.update()
                        except Exception:
                            pass
                    try:
                        content_area.update()
                    except Exception:
                        pass
                return _switch

            tab_buttons = []
            for i, label in enumerate(tab_labels):
                is_selected = (i == selected_tab[0])
                txt = ft.Text(
                    label,
                    size=13,
                    weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.W_600,
                    color=color_scheme.on_primary_container if is_selected else color_scheme.on_secondary_container,
                )
                btn = ft.Container(
                    content=txt,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=4),
                    bgcolor=color_scheme.primary_container if is_selected else ft.Colors.TRANSPARENT,
                    border_radius=4,
                    on_click=make_switcher(i),
                    tooltip=f"Show {label}",
                )
                tab_buttons.append(btn)
                tab_button_controls.append(btn)

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

            header_container = ft.Container(content=compact_header)

            # Underline for the entire header row
            header_underline = ft.Container(
                height=1,
                bgcolor=color_scheme.outline,
                margin=ft.margin.Margin(bottom=6),
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
            # Simple header for non-rack
            header_row = ft.Row(
                [
                    ft.Text(
                        "Inspector",
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color=color_scheme.on_secondary_container,
                    ),
                    ft.Container(width=12),
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

            fields = get_fields_for_device(item) or AMPLIFIER_FIELDS
            generic_fields = []
            for field_name in fields:
                value = props.get(field_name, "")
                tf = ft.TextField(
                    label=field_name,
                    value=str(value) if value is not None else "",
                    height=32,
                    text_size=11,
                    dense=True,
                    on_submit=lambda e, fn=field_name: _save_field(fn, e.control.value),
                    on_blur=lambda e, fn=field_name: _save_field(fn, e.control.value),
                )
                generic_fields.append(tf)

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
