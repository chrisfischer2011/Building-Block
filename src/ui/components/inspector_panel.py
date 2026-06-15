"""
Inspector Panel Component

Generic reusable panel typically placed on the right side.
Used to display and edit properties/details of the currently selected item.

This replaces the previous "Edit Selected" panel with a more generic name.
"""

import flet as ft
import pandas as pd

from src.core.database import is_amp_id_taken, is_rack_name_taken, load_from_db, overwrite_data, save_to_db
from src.core.models import (
    AMPLIFIER_FIELDS,
    DataEntry,
    Device,
    RACK_FIELDS,
    get_display_name,
    get_fields_for_device,
    get_options_for_field,
    get_rack_amp_slots,
    get_rack_name,
    get_rack_template_defaults,
    normalize_amp_id,
)
from typing import Any
from src.ui.theme import (
    CARD_CONTENT_PADDING,
    CARD_ELEVATION_LOW,
    CARD_MARGIN,
    EMPTY_STATE_PADDING,
    FORM_CONTENT_PADDING,
    FORM_CONTROL_HEIGHT,
    FORM_DENSE,
    FORM_SPACING,
    FORM_TEXT_SIZE,
    FORM_TEXT_STYLE,
)
from src.utils.feedback import show_coming_soon, show_success


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

RACK_TAB_AMPS = [f"Amp # {i}" for i in range(1, 17)]  # maximum; per-rack visible count is dynamic (see get_rack_amp_slots + _get_rack_amp_assignment_fields) based on Template + Rack Type "Amp Slots" from the templates table

RACK_TAB_1U = ["1u A", "1u B"]


def _get_amp_options() -> list[str]:
    """Dynamically fetch current amplifiers from the database to use as dropdown options
    for the Amp assignment fields (Amp # 1..16) in the rack inspector's Amp Assignments tab.
    Returns list of amp display names (e.g. "1.00 D90").
    """
    try:
        df = load_from_db("input_data")
        options = []
        for _, row in df.iterrows():
            if str(row.get("device_type", "")).lower() != "amplifier":
                continue
            it = DataEntry.from_dict(row)
            if it and it.name:
                options.append(it.name)
        return sorted(options)
    except Exception:
        return []


def _get_rack_amp_assignment_fields(props: dict) -> list[str]:
    """Return the list of Amp # slots to show for this rack (e.g. Amp # 1 .. Amp # 6),
    based on its current Template + Rack Type lookup. Always <= 16.
    Used to dynamically limit the Amp Assignments tab UI.
    """
    template = props.get("Template", "") or ""
    rack_type = props.get("Rack Type", "") or ""
    n = get_rack_amp_slots(template, rack_type)
    return [f"Amp # {i}" for i in range(1, n + 1)]


def _get_available_rack_locations() -> list[str]:
    """Return Rack Location values that actually exist for at least one Rack in the DB.
    Used to filter the dropdown when editing an Amplifier's Rack Location.
    """
    try:
        df = load_from_db("input_data")
        locs = set()
        for _, row in df.iterrows():
            if str(row.get("device_type", "")).lower() != "rack":
                continue
            it = DataEntry.from_dict(row)
            if it and it.properties:
                loc = (it.properties.get("Rack Location", "") or "").strip()
                if loc:
                    locs.add(loc)
        if locs:
            # Try to keep preferred order from static options
            preferred = get_options_for_field("Rack Location")
            ordered = [p for p in preferred if p in locs]
            ordered += [l for l in sorted(locs) if l not in ordered]
            return ordered
        return get_options_for_field("Rack Location")
    except Exception:
        return get_options_for_field("Rack Location")


def _get_available_rack_numbers(location: str = None) -> list[str]:
    """Return Rack # values for existing racks. If location is given, only those for that location.
    Used to filter the dropdown when editing an Amplifier's Rack # (cascading on current Rack Location).
    """
    try:
        df = load_from_db("input_data")
        nums = set()
        for _, row in df.iterrows():
            if str(row.get("device_type", "")).lower() != "rack":
                continue
            it = DataEntry.from_dict(row)
            if it and it.properties:
                if location and (it.properties.get("Rack Location", "") or "").strip() != location.strip():
                    continue
                num = (it.properties.get("Rack #", "") or "").strip()
                if num:
                    nums.add(num)
        if nums:
            preferred = get_options_for_field("Rack #")
            ordered = [p for p in preferred if p in nums]
            ordered += [n for n in sorted(nums, key=lambda x: int(x) if str(x).isdigit() else 999) if n not in ordered]
            return ordered
        return get_options_for_field("Rack #")
    except Exception:
        return get_options_for_field("Rack #")


def _get_available_amp_slots_for_rack(location: str, rack_number: str) -> list[str]:
    """For the rack identified by Rack Location + Rack # (if it exists), return Amp # 1 .. N
    where N comes from that rack's Template + Rack Type (Amp Slots in the template table).
    If no matching rack or unknown, falls back to 1-16.
    Used to filter the Amp # dropdown on an Amplifier to only the slots the target rack supports.
    """
    if not location or not rack_number:
        return [f"Amp # {i}" for i in range(1, 17)]
    try:
        df = load_from_db("input_data")
        for _, row in df.iterrows():
            if str(row.get("device_type", "")).lower() != "rack":
                continue
            it = DataEntry.from_dict(row)
            if it and it.properties:
                if (it.properties.get("Rack Location", "") or "").strip() == location.strip() and \
                   (it.properties.get("Rack #", "") or "").strip() == str(rack_number).strip():
                    t = it.properties.get("Template", "") or ""
                    rt = it.properties.get("Rack Type", "") or ""
                    n = get_rack_amp_slots(t, rt)
                    return [f"Amp # {i}" for i in range(1, n + 1)]
        return [f"Amp # {i}" for i in range(1, 17)]
    except Exception:
        return [f"Amp # {i}" for i in range(1, 17)]

# =============================================================================
# Tab definitions for Amplifier Inspector (user-specified grouping)
# =============================================================================

AMP_TAB_CORE = [
    "Rack Location",
    "Rack #",
    "Amp #",
    "Amp Type",
    "Amp ID",
    "Mode",
]

AMP_TAB_OUTPUT = [
    "Output Patch",
    "Ch A",
    "Ch B",
    "Ch C",
    "Ch D",
    "Hang A",
    "Hang B",
    "Hang C",
    "Hang D",
]

AMP_TAB_INPUT = [
    "ANA 1",
    "ANA 2",
    "ANA 3",
    "AES 1/2",
    "AES 3/4",
]


def _attribute_tile(field_name: str, value: Any, all_props: dict, color_scheme, on_value_changed=None, device_type: str = None) -> ft.Container:
    """Compact visual tile for a single Rack attribute (label on top, value below).
    Renders as Dropdown if the field has options in DEVICE_FIELD_OPTIONS, else TextField.
    Saves on blur / submit (enter/tab) via the provided callback.
    """
    # Debug coloring disabled for clean layout.
    DEBUG_FORM_CONTROLS = False
    # Always display Amp IDs with exactly 2 decimal places for consistency (even legacy data)
    if field_name == "Amp ID":
        value = normalize_amp_id(value)
    display_value = str(value) if value is not None else ""

    label = ft.Text(
        field_name,
        size=10,
        weight=ft.FontWeight.BOLD,
        color=color_scheme.on_secondary_container,
        text_align=ft.TextAlign.CENTER,
    )

    options = get_options_for_field(field_name)
    # Special case for rack Amp assignment slots: ALWAYS fetch fresh list of amps from DB
    # so the dropdown is dynamic and immediately includes newly added amps (no stale list).
    # Prepend "" so user can manually clear a single slot via dropdown if desired (primary unassign is rack-level + global).
    if field_name.startswith("Amp # "):
        options = [""] + _get_amp_options()

    # Special dynamic filtering for *Amplifier* assignment fields (Rack Location, Rack #, Amp #).
    # Only offer values corresponding to real existing Racks, and for Amp # only the number of
    # slots supported by the specific target rack (per its Template + Rack Type "Amp Slots").
    # This is computed from current props at render time so lists are "available" and cascading.
    if device_type and str(device_type).lower() == "amplifier" and field_name in ("Rack Location", "Rack #", "Amp #"):
        if field_name == "Rack Location":
            options = _get_available_rack_locations()
        elif field_name == "Rack #":
            cur_loc = (all_props or {}).get("Rack Location", "") if all_props else ""
            options = _get_available_rack_numbers(cur_loc)
        elif field_name == "Amp #":
            cur_loc = (all_props or {}).get("Rack Location", "") if all_props else ""
            cur_num = (all_props or {}).get("Rack #", "") if all_props else ""
            options = _get_available_amp_slots_for_rack(cur_loc, cur_num)

    if on_value_changed and options:
        if field_name.startswith("Amp # "):
            # Dropdown for rack amp assignment slots (includes blank first option to allow manual unassign of a single slot).
            # Main unassign is now via the rack-level "Unassign all" button in the tab and the global File menu item.
            value_ctrl = ft.Dropdown(
                value=display_value if display_value else None,
                options=[ft.dropdown.Option(str(o)) for o in options],
                dense=FORM_DENSE,
                text_size=FORM_TEXT_SIZE,
                height=50,
                width=130,  # adjusted wider to fit text without cutoff, allows multiple tiles per row
                on_select=lambda e, fn=field_name: on_value_changed(fn, getattr(e, 'data', None) or getattr(getattr(e, 'control', None), 'value', None)),
                border_color=color_scheme.outline,
                focused_border_color=color_scheme.primary,
                content_padding=FORM_CONTENT_PADDING,
            )
        else:
            # Dropdown for fields with predefined choices
            value_ctrl = ft.Dropdown(
                value=display_value if display_value else None,
                options=[ft.dropdown.Option(str(o)) for o in options],
                dense=FORM_DENSE,
                text_size=FORM_TEXT_SIZE,
                height=50,
                width=130,  # adjusted wider to fit text without cutoff, allows multiple tiles per row
                on_select=lambda e, fn=field_name: on_value_changed(fn, getattr(e, 'data', None) or getattr(getattr(e, 'control', None), 'value', None)),
                border_color=color_scheme.outline,
                focused_border_color=color_scheme.primary,
                content_padding=FORM_CONTENT_PADDING,
            )
    elif on_value_changed:
        # Free text
        value_ctrl = ft.TextField(
            value=display_value,
            dense=FORM_DENSE,
            text_size=FORM_TEXT_SIZE,
            height=50,
            width=130,  # adjusted wider to fit text without cutoff, allows multiple tiles per row
            on_submit=lambda e, fn=field_name: on_value_changed(fn, e.control.value),
            on_blur=lambda e, fn=field_name: on_value_changed(fn, e.control.value),
            border_color=color_scheme.outline,
            focused_border_color=color_scheme.primary,
            content_padding=FORM_CONTENT_PADDING,
        )

        if field_name == "Amp ID":
            # Auto-normalize to 2 decimals on leave (before the save handler runs)
            def _wrap_norm(handler):
                def _wrapped(e):
                    try:
                        e.control.value = normalize_amp_id(e.control.value)
                    except Exception:
                        pass
                    if handler:
                        handler(e)
                return _wrapped
            if value_ctrl.on_blur:
                value_ctrl.on_blur = _wrap_norm(value_ctrl.on_blur)
            if value_ctrl.on_submit:
                value_ctrl.on_submit = _wrap_norm(value_ctrl.on_submit)
    else:
        value_ctrl = ft.Text(
            display_value,
            size=10,
            weight=ft.FontWeight.W_500,
            color=color_scheme.on_secondary_container,
            text_align=ft.TextAlign.CENTER,
        )

    # Apply debug coloring (if enabled) to the actual editable controls.
    # This uses the same three colors as the Add popup so you can visually compare
    # the internal layout (text / padding / margins) between Inspector tiles and the popup.
    if DEBUG_FORM_CONTROLS and on_value_changed:
        if isinstance(value_ctrl, (ft.Dropdown, ft.TextField)):
            value_ctrl.bgcolor = ft.Colors.with_opacity(0.45, ft.Colors.AMBER)   # Padding area
            value_ctrl.border_color = ft.Colors.RED                               # Margins / box
            value_ctrl.focused_border_color = ft.Colors.DEEP_ORANGE
            value_ctrl.text_style = ft.TextStyle(color=ft.Colors.BLUE, size=FORM_TEXT_SIZE)  # Text part
            # Extra nudge for Dropdown text color
            try:
                value_ctrl.color = ft.Colors.BLUE
            except Exception:
                pass

    tile_width = 140  # adjusted to allow several tiles per row (wrap) without text cutoff in dropdowns; wider than previous 100
    return ft.Container(
        content=ft.Column(
            [
                label,
                value_ctrl,
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True,
        ),
        width=tile_width,
        padding=ft.Padding.symmetric(horizontal=3, vertical=1),
        border=ft.Border(
            left=ft.BorderSide(width=1, color=color_scheme.outline),
            top=ft.BorderSide(width=1, color=color_scheme.outline),
            right=ft.BorderSide(width=1, color=color_scheme.outline),
            bottom=ft.BorderSide(width=1, color=color_scheme.outline),
        ),
        border_radius=3,
        bgcolor=color_scheme.primary_container,
        alignment=ft.Alignment.CENTER,
    )


def _build_tab_content(field_names: list[str], props: dict, color_scheme, on_value_changed=None, device_type: str = None) -> ft.Container:
    """Builds scrollable tab content using compact tiles for the Rack inspector."""
    if not field_names:
        return ft.Container(
            content=ft.Text("No fields in this section.", italic=True, size=11),
            padding=10,
        )

    tiles = [_attribute_tile(name, props.get(name, ""), props, color_scheme, on_value_changed=on_value_changed, device_type=device_type) for name in field_names]

    # Wrap the tiles row in a scrollable Column for better behavior inside Tabs
    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    tiles,
                    spacing=2,
                    wrap=True,
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        padding=ft.Padding.only(top=4, bottom=6, left=2, right=2),
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
                        dense=FORM_DENSE,
                        height=50,
                        content_padding=FORM_CONTENT_PADDING,
                        text_style=FORM_TEXT_STYLE,
                    ),
                    ft.TextField(
                        ref=name_ref,
                        label="Name / Identifier",
                        dense=FORM_DENSE,
                        height=50,
                        text_size=FORM_TEXT_SIZE,
                        content_padding=FORM_CONTENT_PADDING,
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

        # Holder for tabbed inspector (rack or amp) so edits can refresh the tab contents list
        # (cross-tab updates after save, without losing current tab)
        _tab_state = {"contents": None, "selected": [0], "area": None, "is_rack": device_type.lower() == "rack"}

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

            old_value = str(item.properties.get(field_name, ""))
            new_value = new_value or ""

            # Always normalize Amp ID to 2 decimal places before any comparison or storage.
            # This ensures legacy data like "1" or "1.1" gets canonical "1.00"/"1.10" on next edit,
            # and user input is always stored consistently.
            if field_name == "Amp ID" and (getattr(item, "device_type", "") or "").lower() == "amplifier":
                new_value = normalize_amp_id(new_value)

            if str(item.properties.get(field_name, "")) == new_value:
                return  # no change (after normalization)

            item.properties[field_name] = new_value

            # Special validation for Amp ID (unique + range), applies on inspector edits too.
            # This prevents duplicates that the create dialog blocked but edits previously allowed.
            if field_name == "Amp ID" and (getattr(item, "device_type", "") or "").lower() == "amplifier":
                amp_id = new_value
                if amp_id:
                    try:
                        val = float(amp_id)
                        if not (0.01 <= val <= 99.99):
                            item.properties[field_name] = old_value
                            show_coming_soon(page, "Amp ID must be a number between 0.01 and 99.99")
                            _refresh_inspector(app_state)
                            return
                    except (ValueError, TypeError):
                        item.properties[field_name] = old_value
                        show_coming_soon(page, "Amp ID must be numeric (e.g. 1.01)")
                        _refresh_inspector(app_state)
                        return

                    if is_amp_id_taken(amp_id, exclude_id=getattr(item, "id", None)):
                        item.properties[field_name] = old_value
                        show_coming_soon(page, f"Amp ID '{amp_id}' is already in use — must be unique.")
                        _refresh_inspector(app_state)
                        return

            # Capture identity *before* any name change (for the case of naming fields like Amp ID)
            match_id = getattr(item, 'id', None)
            match_name = getattr(item, 'name', None)
            match_dtype = getattr(item, 'device_type', None)

            # Recompute the display name if a naming field was edited.
            # For Amplifiers: Amp ID + Amp Type (e.g. "1.01 D90")
            # For Racks: location prefix + Rack #
            try:
                computed_name = get_display_name(item.device_type, item.properties or {})
                if computed_name and computed_name != (item.name or ""):
                    item.name = computed_name
            except Exception:
                pass

            # For racks, after name recompute from naming fields (loc or #), ensure no duplicate name.
            # Only check for actual naming field edits to avoid false positives on other fields like Amp assignments.
            if (getattr(item, "device_type", "") or "").lower() == "rack" and field_name in ["Rack Location", "Rack #"]:
                proposed_name = item.name
                if proposed_name and is_rack_name_taken(proposed_name, exclude_id=getattr(item, "id", None)):
                    item.properties[field_name] = old_value
                    try:
                        item.name = get_display_name(item.device_type, item.properties or {})
                    except Exception:
                        pass
                    show_coming_soon(page, f"Cannot use this — it would create duplicate rack name '{proposed_name}' (e.g. never two SL2).")
                    _refresh_inspector(app_state)
                    return

            # If this was an amp *naming* change (Amp ID or Amp Type), propagate the *new* display name
            # into any rack slots that were pointing at the old name string. Keeps assignments consistent.
            name_changed = False
            if (getattr(item, "device_type", "") or "").lower() == "amplifier" and match_name and item.name and match_name != item.name:
                name_changed = True

            is_rack_edit = (getattr(item, "device_type", "") or "").lower() == "rack"
            is_amp_edit = (getattr(item, "device_type", "") or "").lower() == "amplifier"

            # Auto-apply template defaults (signal routing etc.) + reduce amp slots when Template or Rack Type changed on a rack.
            # This makes the Amp Assignments tab (and other fields) update automatically.
            # Excess Amp # slots beyond the new count are cleared on the rack and their amps are unassigned.
            pre_higher_amp_slots: dict[str, str] = {}
            if is_rack_edit and field_name in ["Template", "Rack Type"]:
                t = item.properties.get("Template", "") or ""
                rt = item.properties.get("Rack Type", "") or ""
                defaults = get_rack_template_defaults(t, rt)
                for k, v in defaults.items():
                    if k != "Amp Slots":
                        item.properties[k] = v
                n = get_rack_amp_slots(t, rt)
                for i in range(n + 1, 17):
                    sl = f"Amp # {i}"
                    val = (item.properties.get(sl, "") or "").strip()
                    if val:
                        pre_higher_amp_slots[sl] = val
                        item.properties[sl] = ""
                item.properties["Amp Slots"] = str(n)
                print(f"[DEBUG] Template/Rack Type changed -> auto-filled signals, amp slots now {n}, cleared {len(pre_higher_amp_slots)} excess slot(s)")

            # For Amplifier: when changing Rack Location or Rack #, auto-clear dependent fields
            # if they are no longer valid for the new choice (keeps data consistent, and next render
            # of the other dropdowns will offer only available options).
            if is_amp_edit and field_name in ("Rack Location", "Rack #"):
                if field_name == "Rack Location":
                    new_loc = item.properties.get("Rack Location", "")
                    cur_num = item.properties.get("Rack #", "")
                    avail_nums = _get_available_rack_numbers(new_loc)
                    if cur_num and cur_num not in [str(x) for x in avail_nums]:
                        item.properties["Rack #"] = ""
                        item.properties["Amp #"] = ""
                        print(f"[DEBUG] Amp: cleared Rack # / Amp # because '{cur_num}' not available for new loc '{new_loc}'")
                elif field_name == "Rack #":
                    cur_loc = item.properties.get("Rack Location", "")
                    new_num = item.properties.get("Rack #", "")
                    avail_slots = _get_available_amp_slots_for_rack(cur_loc, new_num)
                    cur_slot = item.properties.get("Amp #", "")
                    if cur_slot and cur_slot not in avail_slots:
                        item.properties["Amp #"] = ""
                        print(f"[DEBUG] Amp: cleared Amp # because '{cur_slot}' not available for rack {cur_loc} / {new_num}")

            try:
                # Load current state from DB, find the matching item by id (preferred) or name+type,
                # update it in place (including recomputed name), then overwrite the whole table.
                # This prevents accidental duplicate "new" entries on edit.
                df = load_from_db("input_data")
                items = []
                replaced = False
                for _, row in df.iterrows():
                    # Avoid truthy test on Series
                    it = DataEntry.from_dict(row)
                    if it:
                        # Robust match: prefer id (coerce numeric), fall back to name+type.
                        # Use the *pre-edit* identity (match_id / match_name / match_dtype) so that
                        # changing a naming field (which updates .name) still finds the original row.
                        match = False
                        if match_id is not None and it.id is not None:
                            try:
                                if int(it.id) == int(match_id):
                                    match = True
                            except (ValueError, TypeError):
                                if it.id == match_id:
                                    match = True
                        if not match:
                            if (it.name or "") == (match_name or "") and it.device_type == match_dtype:
                                match = True

                        if match:
                            it.properties = dict(item.properties) if item.properties else {}
                            if getattr(item, "name", None):
                                it.name = item.name
                            items.append(it)
                            replaced = True
                        else:
                            items.append(it)
                if not replaced:
                    # Fallback: keep the live item (it already has updated props + name)
                    items.append(item)

                # === RELATIONSHIP SYNC: rack <-> amp (forward assign/move/unassign + reverse + rack-level unassign) ===
                # We operate on the already-loaded `items` list (primary edited item already synced in).
                # All cross updates (rack slots + amp props) happen here, then a *single* overwrite_data.
                # Rack assignment now moves an amp if it's assigned elsewhere (instead of blocking).
                # This keeps rack slots and amp "Rack Location/Rack #/Amp #" in sync in both directions.

                amp_slots = RACK_TAB_AMPS

                # --- Name propagation for amps (if Amp ID/Type changed, update rack slot strings) ---
                if name_changed and match_name and item.name:
                    for r in items:
                        if (getattr(r, "device_type", "") or "").lower() != "rack":
                            continue
                        for sl in amp_slots:
                            if (r.properties.get(sl, "") or "").strip() == (match_name or "").strip():
                                r.properties[sl] = item.name
                                print(f"[DEBUG] Propagated amp name change in rack slot {sl}: '{match_name}' -> '{item.name}'")

                # --- Forward: rack Amp # slot edited (assign, move amp from elsewhere, change occupant, or unassign/clear) ---
                if is_rack_edit and field_name.startswith("Amp # "):
                    new_amp = (new_value or "").strip()
                    old_amp_in_slot = (old_value or "").strip()
                    rack_loc = item.properties.get("Rack Location", "") or ""
                    rack_num = item.properties.get("Rack #", "") or ""
                    amp_slot = field_name

                    # Support moving an amp that is already assigned elsewhere (user request).
                    # Instead of preventing, clear it from its old rack/slot (anywhere), then assign here.
                    # This updates the amp to the *new* position (rack loc/# + this slot).
                    if new_amp:
                        old_r = None
                        old_sl = None
                        for r in items:
                            if (getattr(r, "device_type", "") or "").lower() != "rack":
                                continue
                            for sl in amp_slots:
                                if (r.properties.get(sl, "") or "").strip() == new_amp:
                                    rloc = (r.properties.get("Rack Location", "") or "").strip()
                                    rnum = (r.properties.get("Rack #", "") or "").strip()
                                    this_loc = (item.properties.get("Rack Location", "") or "").strip()
                                    this_num = (item.properties.get("Rack #", "") or "").strip()
                                    if rloc == this_loc and rnum == this_num and sl == field_name:
                                        old_r = None
                                        old_sl = None  # already correctly here
                                        break
                                    old_r = r
                                    old_sl = sl
                                    break
                            if old_sl:
                                break
                        if old_r and old_sl:
                            old_r.properties[old_sl] = ""
                            print(f"[DEBUG] Relocate (rack assign): amp '{new_amp}' was in {old_sl} — cleared old slot to move it here")

                    # Unassign previous occupant of *this* slot (if changing or clearing)
                    if old_amp_in_slot and old_amp_in_slot != new_amp:
                        for it in items:
                            if it and (getattr(it, "device_type", "") or "").lower() == "amplifier":
                                if (getattr(it, "name", "") or "").strip() == old_amp_in_slot:
                                    it.properties = it.properties or {}
                                    it.properties["Rack Location"] = ""
                                    it.properties["Rack #"] = ""
                                    it.properties["Amp #"] = ""
                                    print(f"[DEBUG] Unassigned previous occupant '{old_amp_in_slot}' from {field_name} (cleared its rack info)")
                                    break

                    # Assign (or re-assign) the new amp to this rack/slot (also handles clear when new_amp=="")
                    if new_amp:
                        print(f"[DEBUG] Amp assignment save (forward): rack assigning '{new_amp}' to {field_name}")
                        print(f"[DEBUG] Using rack_loc={rack_loc!r} rack_num={rack_num!r}")
                        found_amp = None
                        amp_names_seen = []
                        target_name = new_amp
                        for it in items:
                            if it and (getattr(it, "device_type", "") or "").lower() == "amplifier":
                                nm = (getattr(it, "name", "") or "").strip()
                                amp_names_seen.append(nm)
                                if nm == target_name:
                                    found_amp = it
                                    break
                                try:
                                    comp = get_display_name(it.device_type, it.properties or {})
                                    if comp.strip() == target_name:
                                        found_amp = it
                                        if getattr(it, "name", None) != comp:
                                            it.name = comp
                                        break
                                except Exception:
                                    pass
                        if found_amp:
                            found_amp.properties = found_amp.properties or {}
                            found_amp.properties["Rack Location"] = rack_loc
                            found_amp.properties["Rack #"] = rack_num
                            found_amp.properties["Amp #"] = amp_slot
                            print(f"[DEBUG] Found amp, set its props -> Rack Location={rack_loc!r} etc.")
                        else:
                            print(f"[DEBUG] WARNING: target amp '{new_amp}' not found among loaded items")
                            print(f"[DEBUG] Amp names seen: {amp_names_seen}")
                    else:
                        # Clearing this slot (new_amp == ""): the old occupant unassign above already did the work.
                        print(f"[DEBUG] Amp slot {field_name} cleared on rack (unassign propagated if there was an occupant)")

                # Handle excess amp slot unassigns when Template or Rack Type changed (reduces visible assignments)
                if is_rack_edit and field_name in ["Template", "Rack Type"] and pre_higher_amp_slots:
                    for sl, amp_name in pre_higher_amp_slots.items():
                        for it in items:
                            if it and (getattr(it, "device_type", "") or "").lower() == "amplifier" and (getattr(it, "name", "") or "").strip() == amp_name:
                                it.properties = it.properties or {}
                                it.properties["Rack Location"] = ""
                                it.properties["Rack #"] = ""
                                it.properties["Amp #"] = ""
                                print(f"[DEBUG] Template/Rack Type change: unassigned '{amp_name}' from now-excess {sl}")
                                break

                # --- Reverse: amp's Rack Location / Rack # / Amp # edited ---
                # The amp declares where it belongs. Make rack side(s) match: clear from old location(s),
                # set the (possibly new) slot on the target rack if loc+#+slot are all provided.
                # This also supports "unassign" by clearing the three fields on the amp.
                if is_amp_edit and field_name in ["Rack Location", "Rack #", "Amp #"]:
                    current_amp_name = (item.name or match_name or "").strip()
                    aloc = (item.properties.get("Rack Location", "") or "").strip()
                    anum = (item.properties.get("Rack #", "") or "").strip()
                    aslot = (item.properties.get("Amp #", "") or "").strip()

                    # 1. Remove this amp (by its pre-edit name to be robust) from *any* rack slots that reference it.
                    #    (handles move, unassign, or even name change side-effect)
                    cleared_from = []
                    for r in items:
                        if (getattr(r, "device_type", "") or "").lower() != "rack":
                            continue
                        for sl in amp_slots:
                            if (r.properties.get(sl, "") or "").strip() == (match_name or current_amp_name):
                                r.properties[sl] = ""
                                cleared_from.append(f"{sl} on rack {r.name or '(unnamed)'}")
                    if cleared_from:
                        print(f"[DEBUG] Reverse: cleared amp '{match_name or current_amp_name}' from rack slot(s): {cleared_from}")

                    # 2. If the amp now fully declares an assignment, find the target rack by loc + # and set its slot.
                    if aloc and anum and aslot:
                        target_found = False
                        for r in items:
                            if (getattr(r, "device_type", "") or "").lower() != "rack":
                                continue
                            rloc = (r.properties.get("Rack Location", "") or "").strip()
                            rnum = (r.properties.get("Rack #", "") or "").strip()
                            if rloc == aloc and rnum == anum:
                                # Target rack found. If the slot is occupied by a *different* amp, unassign that one first (claim the slot).
                                current_in_slot = (r.properties.get(aslot, "") or "").strip()
                                if current_in_slot and current_in_slot != current_amp_name:
                                    for oa in items:
                                        if (getattr(oa, "device_type", "") or "").lower() == "amplifier" and (getattr(oa, "name", "") or "").strip() == current_in_slot:
                                            oa.properties = oa.properties or {}
                                            oa.properties["Rack Location"] = ""
                                            oa.properties["Rack #"] = ""
                                            oa.properties["Amp #"] = ""
                                            print(f"[DEBUG] Reverse: displaced previous amp '{current_in_slot}' from {aslot} to make room")
                                            break
                                r.properties[aslot] = current_amp_name
                                target_found = True
                                print(f"[DEBUG] Reverse: amp '{current_amp_name}' now assigned via rack edit -> set {aslot} on matching rack (loc={aloc}, #={anum})")
                                break
                        if not target_found:
                            print(f"[DEBUG] Reverse: amp claims loc={aloc} #={anum} slot={aslot}, but no matching rack found (dangling claim kept on amp)")

                overwrite_data(items)

                # Post-write verification / debug for assignment changes (forward or reverse)
                if is_rack_edit and field_name.startswith("Amp # "):
                    try:
                        verify_df = load_from_db("input_data")
                        for _, r in verify_df.iterrows():
                            v = DataEntry.from_dict(r)
                            if v and (getattr(v, "device_type", "") or "").lower() == "amplifier":
                                vname = (getattr(v, "name", "") or "").strip()
                                if new_value and vname == (new_value or "").strip():
                                    vp = v.properties or {}
                                    print(f"[DEBUG] VERIFIED (forward): amp '{vname}' now has Rack Location={vp.get('Rack Location')!r} Rack#={vp.get('Rack #')!r} Amp#={vp.get('Amp #')!r}")
                                if old_value and vname == (old_value or "").strip() and not new_value:
                                    vp = v.properties or {}
                                    print(f"[DEBUG] VERIFIED (unassign): previous amp '{vname}' now cleared (Rack Location={vp.get('Rack Location')!r} etc.)")
                    except Exception as ex:
                        print(f"[DEBUG] VERIFICATION load failed: {ex}")

                if is_amp_edit and field_name in ["Rack Location", "Rack #", "Amp #"]:
                    print(f"[DEBUG] Reverse sync complete for amp edit of {field_name}. Current amp claim: loc={aloc!r} #={anum!r} slot={aslot!r}")

                # Re-build the tab contents from the *current* props so that
                # switching tabs after an edit shows fresh data in the other tabs.
                # Works for both Rack (3 tabs) and Amplifier (Core/Output/Input tabs).
                if _tab_state.get("contents") and _tab_state.get("area"):
                    try:
                        if _tab_state.get("is_rack"):
                            c0 = _build_tab_content(RACK_TAB_CORE, item.properties or {}, color_scheme, on_value_changed=_save_field, device_type="Rack")
                            c1 = _build_tab_content(RACK_TAB_SIGNAL, item.properties or {}, color_scheme, on_value_changed=_save_field, device_type="Rack")
                            c2f = _get_rack_amp_assignment_fields(item.properties or {}) + RACK_TAB_1U
                            c2 = _build_tab_content(c2f, item.properties or {}, color_scheme, on_value_changed=_save_field, device_type="Rack")
                            _tab_state["contents"][:] = [c0, c1, c2]
                        else:
                            c0 = _build_tab_content(AMP_TAB_CORE, item.properties or {}, color_scheme, on_value_changed=_save_field, device_type="Amplifier")
                            c1 = _build_tab_content(AMP_TAB_OUTPUT, item.properties or {}, color_scheme, on_value_changed=_save_field, device_type="Amplifier")
                            c2 = _build_tab_content(AMP_TAB_INPUT, item.properties or {}, color_scheme, on_value_changed=_save_field, device_type="Amplifier")
                            _tab_state["contents"][:] = [c0, c1, c2]
                        _tab_state["area"].content = _tab_state["contents"][_tab_state["selected"][0]]
                        _tab_state["area"].update()
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

                # Refresh the inspector too. This makes the header (device: name) update
                # immediately when a naming field (e.g. Amp ID, Amp Type, Rack Location, Rack #) changes,
                # and ensures the tab contents reflect the latest data.
                _refresh_inspector(app_state)
            except Exception as ex:
                print(f"Save failed for {field_name}: {ex}")

        def _refresh_inspector(app_state):
            """Rebuild the inspector panel (used after validation errors to revert bad values in UI controls,
            and on success to update header/name etc.)."""
            if hasattr(app_state, "_inspector_refresh_callbacks"):
                for cb in list(getattr(app_state, "_inspector_refresh_callbacks", [])):
                    try:
                        cb()
                    except Exception:
                        pass

        # Icon for the header
        icon = ft.Icons.SETTINGS if device_type.lower() == "rack" else ft.Icons.SPEAKER

        def _build_tabbed_inspector_body(tab_contents, tab_labels, color_scheme, icon, device_type, display_name):
            """Shared helper to build the compact header+tab-buttons+underline+swappable content
            used by both Rack (Core/Signal/Amp Assignments) and Amplifier (Core/Output/Input) inspectors.
            Returns (inspector_body_children_list, content_area, selected_tab, tab_contents) so caller
            can wire into _tab_state for cross-tab refresh on edits.
            """
            selected_tab = [0]
            content_area = ft.Container(
                content=tab_contents[selected_tab[0]],
                expand=True,
                padding=ft.Padding.only(top=4, bottom=4),
            )

            tab_button_controls = []

            def make_switcher(idx):
                def _switch(e):
                    selected_tab[0] = idx
                    content_area.content = tab_contents[selected_tab[0]]
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

            header_underline = ft.Container(
                height=1,
                bgcolor=color_scheme.outline,
                margin=ft.margin.Margin(bottom=6),
            )

            children = [
                header_container,
                header_underline,
                content_area,
            ]
            return children, content_area, selected_tab, tab_contents

        inspector_body_children = []

        if device_type.lower() == "rack":
            # === Clean compact header with tabs integrated in the row + underline ===
            # Tabs: Core | Signal Routing | Amp Assignments (1U fields inline in 3rd tab)
            core_content = _build_tab_content(RACK_TAB_CORE, props, color_scheme, on_value_changed=_save_field, device_type="Rack")
            signal_content = _build_tab_content(RACK_TAB_SIGNAL, props, color_scheme, on_value_changed=_save_field, device_type="Rack")

            # 3rd tab: Amp Assignments + 1U Custom fields all in one flat wrapped grid
            # (so the 2 1U fields appear inline with the other Amp fields)
            # Number of Amp # slots is dynamic based on Template + Rack Type (from amp rack templates table).
            # Unassign button for the entire rack (not per-slot) as requested.
            third_tab_fields = _get_rack_amp_assignment_fields(props) + RACK_TAB_1U

            def _unassign_all_for_this_rack(e):
                """Clear all Amp # 1..16 slots on the current rack and sync-unassign the amps (clear their 3 fields).
                Uses one atomic load/mutate/overwrite + refreshes so sidebar + inspector update.
                """
                if not app_state.selected_item or (getattr(app_state.selected_item, "device_type", "") or "").lower() != "rack":
                    return
                rk = app_state.selected_item
                # Only unassign the slots that are currently active for this rack's template (plus any legacy higher just in case)
                n = get_rack_amp_slots(rk.properties.get("Template", ""), rk.properties.get("Rack Type", ""))
                slots_to_clear = [f"Amp # {i}" for i in range(1, n + 1)] + [f"Amp # {i}" for i in range(n + 1, 17)]
                assigned = []
                for sl in slots_to_clear:
                    val = (rk.properties.get(sl, "") or "").strip()
                    if val:
                        assigned.append(val)
                        rk.properties[sl] = ""
                if not assigned:
                    return
                try:
                    df = load_from_db("input_data")
                    items = []
                    for _, row in df.iterrows():
                        it = DataEntry.from_dict(row)
                        if it:
                            # Update the rack copy from live (slots cleared on rk)
                            if it.name == rk.name and it.device_type == rk.device_type:
                                it.properties = dict(rk.properties or {})
                                if getattr(rk, "name", None):
                                    it.name = rk.name
                            items.append(it)
                    # Clear the amps that were in the slots
                    for amp_name in assigned:
                        for it in items:
                            if it and (getattr(it, "device_type", "") or "").lower() == "amplifier":
                                if (getattr(it, "name", "") or "").strip() == amp_name:
                                    it.properties = it.properties or {}
                                    it.properties["Rack Location"] = ""
                                    it.properties["Rack #"] = ""
                                    it.properties["Amp #"] = ""
                                    print(f"[DEBUG] Unassign all (this rack): cleared {amp_name}")
                                    break
                    overwrite_data(items)
                    # Refresh UI (keep current selection)
                    if hasattr(app_state, "_sidebar_refresh_callbacks"):
                        for cb in list(getattr(app_state, "_sidebar_refresh_callbacks", [])):
                            try:
                                cb(auto_select_latest=False)
                            except Exception:
                                pass
                    _refresh_inspector(app_state)
                    try:
                        show_success(page, f"Unassigned {len(assigned)} amp(s) from this rack")
                    except Exception:
                        pass
                except Exception as ex:
                    print(f"[Unassign all for rack] failed: {ex}")
                    show_coming_soon(page, f"Unassign all failed: {ex}")

            unassign_header = ft.Row(
                [
                    ft.Text("Amp Assignments", size=10, weight=ft.FontWeight.BOLD, color=color_scheme.on_secondary_container),
                    ft.Container(expand=True),
                    ft.TextButton(
                        "Unassign all amps from this rack",
                        icon=ft.Icons.CLEAR_ALL,
                        tooltip="Clear every Amp # slot on this rack and remove the assignments from the amps",
                        on_click=_unassign_all_for_this_rack,
                        style=ft.ButtonStyle(
                            padding=ft.Padding.only(left=6, right=6, top=1, bottom=1),
                            text_style=ft.TextStyle(size=9),
                        ),
                    ),
                ],
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

            base_tiles = _build_tab_content(third_tab_fields, props, color_scheme, on_value_changed=_save_field, device_type="Rack")
            third_tab_content = ft.Container(
                content=ft.Column(
                    [
                        unassign_header,
                        base_tiles,
                    ],
                    spacing=4,
                    expand=True,
                ),
                expand=True,
            )

            tab_contents = [core_content, signal_content, third_tab_content]
            tab_labels = ["Core", "Signal Routing", "Amp Assignments"]  # 3rd tab includes 1U fields inline

            tab_children, content_area, selected_tab, tab_c = _build_tabbed_inspector_body(
                tab_contents, tab_labels, color_scheme, icon, device_type, display_name
            )
            _tab_state["contents"] = tab_c
            _tab_state["selected"] = selected_tab
            _tab_state["area"] = content_area
            _tab_state["is_rack"] = True
            inspector_body_children = tab_children

        else:
            # === Amplifier inspector: 3 tabs as requested ===
            # Core: assignment + identity + mode
            # Output: patching + channels + hangs
            # Input: analog + aes
            core_content = _build_tab_content(AMP_TAB_CORE, props, color_scheme, on_value_changed=_save_field, device_type="Amplifier")
            output_content = _build_tab_content(AMP_TAB_OUTPUT, props, color_scheme, on_value_changed=_save_field, device_type="Amplifier")
            input_content = _build_tab_content(AMP_TAB_INPUT, props, color_scheme, on_value_changed=_save_field, device_type="Amplifier")

            tab_contents = [core_content, output_content, input_content]
            tab_labels = ["Core", "Output", "Input"]

            tab_children, content_area, selected_tab, tab_c = _build_tabbed_inspector_body(
                tab_contents, tab_labels, color_scheme, icon, device_type, display_name
            )
            _tab_state["contents"] = tab_c
            _tab_state["selected"] = selected_tab
            _tab_state["area"] = content_area
            _tab_state["is_rack"] = False
            inspector_body_children = tab_children

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
