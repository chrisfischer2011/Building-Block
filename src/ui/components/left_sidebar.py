"""
Left Sidebar Component

Generic reusable left sidebar panel. Typically used for navigation,
item lists, or selectors.

This is the generic version of what was previously the Rack & Amp selector.
"""

import flet as ft
import pandas as pd

from src.core.database import get_next_free_amp_id, get_taken_amp_ids, get_taken_rack_names, is_amp_id_taken, is_rack_name_taken, load_from_db, save_to_db
from src.core.models import (
    DataEntry,
    get_display_name,
    get_options_for_field,
    get_rack_name,
    get_rack_template_defaults,
    normalize_amp_id,
)
from src.ui.theme import (
    CARD_CONTENT_PADDING,
    CARD_ELEVATION,
    CARD_MARGIN,
    LIST_ITEM_SPACING,
)
from src.utils.feedback import show_coming_soon


def _get_seed_data() -> list[DataEntry]:
    """Return some initial sample data when the database is empty."""
    return [
        DataEntry(
            id=1,
            name="Rack A1",
            device_type="Rack",
            properties={
                "rack_location": "Stage Left",
                "rack_number": 1,
                "rack_type": "Main",
            },
            notes="Main rack A1",
        ),
        DataEntry(
            id=2,
            name="Rack B2",
            device_type="Rack",
            properties={"rack_number": 2},
            notes="Rack B2",
        ),
        DataEntry(
            id=3,
            name="Amp X-500",
            device_type="Amplifier",
            properties={"model": "X-500"},
            notes="Amp X-500",
        ),
    ]


def _show_create_device_dialog(page: ft.Page, on_created=None):
    """Clean, reliable create dialog for testing."""
    device_type_ref = ft.Ref[ft.Dropdown]()
    location_ref = ft.Ref[ft.Dropdown]()
    rack_num_ref = ft.Ref[ft.Dropdown]()
    template_ref = ft.Ref[ft.Dropdown]()
    rack_type_ref = ft.Ref[ft.Dropdown]()

    # Refs for auto-fillable template fields (shown for Rack)
    auto_fill_field_refs = {}
    auto_fill_fields = [
        "Switch Config", "Off Ramp", "AES Input", "Analog Input",
        "Distro 1", "Distro 2",
        "Signal In", "Signal Thru", "Signal Out", "Signal Out 2",
        "Maps 1", "Maps 2", "Maps 3", "Maps 4", "Maps 5", "Maps 6",
    ]
    for f in auto_fill_fields:
        auto_fill_field_refs[f] = ft.Ref[ft.Dropdown]()

    # Refs for Amplifier fields (always created so we can toggle visibility on device type change)
    amp_field_refs = {}
    amp_fields = [
        "Amp #", "Amp Type", "Amp ID", "Mode",
        "Ch A", "Ch B", "Ch C", "Ch D",
        "Hang A", "Hang B", "Hang C", "Hang D",
        "Output Patch",
        "ANA 1", "ANA 2", "ANA 3",
        "AES 1/2", "AES 3/4",
    ]
    for f in amp_fields:
        if get_options_for_field(f):
            amp_field_refs[f] = ft.Ref[ft.Dropdown]()
        else:
            amp_field_refs[f] = ft.Ref[ft.TextField]()

    def _auto_fill_from_template(e=None):
        """Auto-fill the template-derived fields when Template + Rack Type are set.
        If device type is not Rack, clear the auto fields.
        Uses safe access because refs may not be populated until dialog is shown.
        """
        dtype_ctrl = device_type_ref.current
        dtype = getattr(dtype_ctrl, 'value', None) if dtype_ctrl else None
        if dtype != "Rack":
            for f in auto_fill_fields:
                ref = auto_fill_field_refs.get(f)
                if ref and ref.current:
                    try:
                        ref.current.value = ""
                        ref.current.update()
                    except Exception:
                        pass
            return
        t_ctrl = template_ref.current
        rt_ctrl = rack_type_ref.current
        t = getattr(t_ctrl, 'value', None) if t_ctrl else None
        rt = getattr(rt_ctrl, 'value', None) if rt_ctrl else None
        if not t or not rt:
            return
        defaults = get_rack_template_defaults(t, rt)
        for f, v in defaults.items():
            ref = auto_fill_field_refs.get(f)
            if ref and ref.current:
                try:
                    ref.current.value = v or ""
                    ref.current.update()
                except Exception:
                    pass

    def _save(e):
        print("=== CREATE SAVE STARTED ===")
        try:
            dtype = device_type_ref.current.value or "Rack"

            # Collect common fields first
            loc = location_ref.current.value or ""
            num = rack_num_ref.current.value or ""

            if dtype == "Rack":
                # Collect core + auto-fill fields (only meaningful for Rack)
                props = {
                    "Rack Location": loc,
                    "Rack #": num,
                    "Template": template_ref.current.value or "",
                    "Rack Type": rack_type_ref.current.value or "",
                }
                for f in auto_fill_fields:
                    if f in auto_fill_field_refs and auto_fill_field_refs[f].current:
                        props[f] = auto_fill_field_refs[f].current.value or ""
            else:
                # Amplifier
                amp_num = amp_field_refs["Amp #"].current.value or "" if amp_field_refs.get("Amp #") and amp_field_refs["Amp #"].current else ""
                amp_type = amp_field_refs["Amp Type"].current.value or "" if amp_field_refs.get("Amp Type") and amp_field_refs["Amp Type"].current else ""
                amp_id = amp_field_refs["Amp ID"].current.value or "" if amp_field_refs.get("Amp ID") and amp_field_refs["Amp ID"].current else ""
                mode = amp_field_refs["Mode"].current.value or "" if amp_field_refs.get("Mode") and amp_field_refs["Mode"].current else ""

                # Normalize Amp ID to always have exactly 2 decimal places (e.g. 1 -> 1.00, 1.1 -> 1.10)
                amp_id = normalize_amp_id(amp_id)
                amp_id_ref = amp_field_refs.get("Amp ID")
                if amp_id_ref and amp_id_ref.current:
                    try:
                        amp_id_ref.current.value = amp_id
                    except Exception:
                        pass

                props = {
                    "Rack Location": loc,
                    "Rack #": num,
                    "Amp #": amp_num,
                    "Amp Type": amp_type,
                    "Amp ID": amp_id,
                    "Mode": mode,
                }
                for f in amp_fields:
                    if f in amp_field_refs and amp_field_refs[f].current:
                        props[f] = amp_field_refs[f].current.value or ""

                # Validate Amp ID: numeric 0.01-99.99 and unique (better UX than before)
                if amp_id:
                    try:
                        val = float(amp_id)
                        if not (0.01 <= val <= 99.99):
                            show_coming_soon(page, "Amp ID must be a number between 0.01 and 99.99")
                            return
                    except (ValueError, TypeError):
                        show_coming_soon(page, "Amp ID must be numeric (e.g. 1.01 or 42.5)")
                        return

                    if is_amp_id_taken(amp_id):
                        show_coming_soon(page, f"Amp ID '{amp_id}' is already in use — must be unique.")
                        return

            # Central name generation (for amps this yields "AmpID AmpType" e.g. "1.01 D90";
            # for racks it yields the location-pref + rack#)
            name = get_display_name(dtype, props)

            # Prevent duplicate rack names (e.g. two SL2) - similar to amp ID uniqueness
            if dtype == "Rack" and is_rack_name_taken(name):
                show_coming_soon(page, f"Rack name '{name}' is already in use — must be unique (e.g. never two SL2).")
                return

            print("Generated name:", name)
            print("Properties being saved:", props)

            new_item = DataEntry(
                name=name,
                device_type=dtype,
                properties=props,
                notes=""
            )
            df = pd.DataFrame([new_item.to_dict()])
            save_to_db(df, "input_data")
            print("Save successful")

            if on_created:
                print("Calling refresh callback...")
                on_created()

            page.pop_dialog()
            page.update()
            print("=== CREATE SAVE FINISHED ===")

        except Exception as ex:
            import traceback
            traceback.print_exc()
            show_coming_soon(page, f"Create failed: {str(ex)}")

    def _update_rack_suggestion(e=None):
        """When Rack Location or Rack # changes in create form, if the would-be name
        (e.g. SL2) is already taken, automatically advance to the next free rack # for
        that location so user never creates a duplicate name like two SL2.
        Also handles initial/empty selection by picking first free.
        """
        if not location_ref.current or not rack_num_ref.current:
            return
        loc_val = location_ref.current.value or ""
        try:
            current_num = int(rack_num_ref.current.value or 0)
        except (ValueError, TypeError):
            current_num = 0
        if current_num < 1:
            current_num = 1
            try:
                rack_num_ref.current.value = "1"
            except Exception:
                pass
        name = get_rack_name(loc_val, current_num)
        if is_rack_name_taken(name):
            for n in range(1, 11):
                test_name = get_rack_name(loc_val, n)
                if not is_rack_name_taken(test_name):
                    rack_num_ref.current.value = str(n)
                    try:
                        rack_num_ref.current.update()
                    except Exception:
                        pass
                    break

    # --- Build the form controls (shared + type-specific groups for dynamic switching) ---

    # Shared fields (Rack Location + Rack # are used by both Racks and Amps for assignment)
    loc_dd = ft.Dropdown(
        ref=location_ref,
        label="Rack Location",
        options=[ft.dropdown.Option(o) for o in get_options_for_field("Rack Location")],
        height=50,
        on_select=_update_rack_suggestion,
    )
    rack_dd = ft.Dropdown(
        ref=rack_num_ref,
        label="Rack #",
        options=[ft.dropdown.Option(o) for o in get_options_for_field("Rack #")],
        height=50,
        on_select=_update_rack_suggestion,
    )

    # Bootstrap initial free rack name suggestion (so first open for rack also avoids duplicates)
    _update_rack_suggestion()

    # Rack-only controls (the original Template / Rack Type + 16 auto-fill signal fields)
    template_dd = ft.Dropdown(
        ref=template_ref,
        label="Template",
        options=[ft.dropdown.Option(o) for o in get_options_for_field("Template")],
        height=50,
        on_select=_auto_fill_from_template,
    )
    racktype_dd = ft.Dropdown(
        ref=rack_type_ref,
        label="Rack Type",
        options=[ft.dropdown.Option(o) for o in get_options_for_field("Rack Type")],
        height=50,
        on_select=_auto_fill_from_template,
    )

    # Info about taken rack names so user never creates duplicate like two "SL2"
    taken_rack_names = get_taken_rack_names()
    taken_rack_text = ft.Text(
        f"Taken Rack names (never duplicate e.g. 2 SL2): {', '.join(sorted(taken_rack_names)) if taken_rack_names else 'none yet'}",
        size=9,
        italic=True,
        color=ft.Colors.GREY_700,
    )

    rack_auto_ctrls = [
        ft.Dropdown(
            ref=auto_fill_field_refs[f],
            label=f,
            options=[ft.dropdown.Option(o) for o in get_options_for_field(f)],
            height=50,
        )
        for f in auto_fill_fields
    ]

    # Hide the auto-fill fields (they still get populated from the template when Template + Rack Type
    # are selected, and their values are collected on Create, but user doesn't need to see them
    # now that auto-populate works).
    for ctrl in rack_auto_ctrls:
        ctrl.visible = False

    # Amp-only controls (built according to the updated Amplifier field list)
    # Per request: only Amp Type and Amp ID are visible initially for create.
    # All others are hidden (still created so refs get mounted when group shown, values collected on Create as empty/defaults;
    # user fills the rest later in the Inspector).
    amp_ctrls = [
        ft.Text("Amplifier Details", size=11, weight=ft.FontWeight.BOLD, visible=False),
    ]
    amp_show_fields = {"Amp Type", "Amp ID"}
    for f in amp_fields:
        ref = amp_field_refs[f]
        opts = get_options_for_field(f)
        if opts:
            ctrl = ft.Dropdown(
                ref=ref,
                label=f,
                options=[ft.dropdown.Option(o) for o in opts],
                height=50,
                visible=(f in amp_show_fields),
            )
        else:
            hint = "0.01-99.99 with 2 decimals (e.g. 1.00, 42.50)  (must be unique)" if f == "Amp ID" else None
            ctrl = ft.TextField(
                ref=ref,
                label=f,
                height=50,
                hint_text=hint,
                visible=(f in amp_show_fields),
            )

        if f == "Amp ID":
            def _on_amp_id_blur(e, the_ref=ref):
                try:
                    if the_ref.current:
                        the_ref.current.value = normalize_amp_id(the_ref.current.value)
                except Exception:
                    pass
            ctrl.on_blur = _on_amp_id_blur

        amp_ctrls.append(ctrl)

    # Add info about taken IDs so user can easily pick a free one (avoids "duplicate" surprises on create)
    taken_list = get_taken_amp_ids()
    taken_info = ft.Text(
        f"Taken Amp IDs (avoid these): {', '.join(taken_list) if taken_list else 'none yet'}",
        size=9,
        italic=True,
        color=ft.Colors.GREY_700,
    )
    amp_ctrls.append(taken_info)

    # Visibility groups (toggled when Device Type changes)
    # rack_only contains template + racktype (visible) + taken info (visible) + autos (hidden but mounted for auto-populate + collect)
    rack_only = ft.Column(
        [template_dd, racktype_dd, taken_rack_text] + rack_auto_ctrls,
        tight=True,
        visible=True,
    )
    # amp_only contains all amp fields; only Amp Type + Amp ID have visible=True (others hidden but mounted)
    amp_only = ft.Column(
        amp_ctrls,
        tight=True,
        visible=False,
    )

    def _switch_form(e=None):
        """Dynamically show the correct set of fields when the user switches Device Type."""
        dtype_ctrl = device_type_ref.current
        dtype = getattr(dtype_ctrl, "value", None) if dtype_ctrl else "Rack"
        is_rack = (dtype == "Rack")
        # For Rack: show loc, rack#, template, rack type (autos after rack type are hidden individually but still mounted for auto-fill + save).
        # For Amplifier: show loc, rack# (for assignment) + only Amp Type and Amp ID (per request); hide all other amp fields.
        # Hidden controls are still mounted in the tree when their group is visible, so refs populate and
        # values (auto-filled for rack from template, defaults/empty for hidden amp) are collected on Create.
        rack_only.visible = is_rack
        amp_only.visible = not is_rack

        # For amp: if Amp ID field is empty, prefill with a free ID (computed from DB) so user
        # doesn't pick a taken one and get the "duplicate" error on Create.
        if not is_rack:
            amp_id_ctrl = amp_field_refs.get("Amp ID")
            if amp_id_ctrl and amp_id_ctrl.current:
                current = (amp_id_ctrl.current.value or "").strip()
                if not current:
                    try:
                        free_id = get_next_free_amp_id()
                        amp_id_ctrl.current.value = free_id
                    except Exception:
                        pass

        if is_rack:
            _update_rack_suggestion()

        # Let rack auto-fill logic run (it safely clears rack autos when switching to Amp)
        try:
            _auto_fill_from_template()
            rack_only.update()
            amp_only.update()
        except Exception:
            pass

    # Device Type dropdown (created after _switch_form so the handler is defined)
    device_type_dd = ft.Dropdown(
        ref=device_type_ref,
        label="Device Type",
        options=[
            ft.dropdown.Option("Rack"),
            ft.dropdown.Option("Amplifier"),
        ],
        value="Rack",
        on_select=_switch_form,
    )

    dlg = ft.AlertDialog(
        title=ft.Text("Create New Device"),
        content=ft.Column(
            [
                device_type_dd,
                loc_dd,
                rack_dd,
                rack_only,
                amp_only,
            ],
            tight=True,
            scroll=ft.ScrollMode.AUTO,
        ),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
            ft.ElevatedButton("Create", on_click=_save),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    # Set initial visibility for the default device type (Rack)
    _switch_form()

    page.show_dialog(dlg)



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

    # Load real data from database (fresh load on every sidebar creation / startup)
    def _load_items_from_db() -> list[DataEntry]:
        try:
            df = load_from_db("input_data")
            loaded = []
            for _, row in df.iterrows():
                # Avoid "if row:" — row is a pandas Series which causes "truth value of a Series is ambiguous".
                try:
                    item = DataEntry.from_dict(row)
                    loaded.append(item)
                except Exception:
                    pass  # skip bad rows silently

            return [item for item in loaded if item and getattr(item, 'device_type', None)]
        except Exception:
            return []

    # Master list of all items loaded from DB (used as source for filtering)
    all_items: list[DataEntry] = []

    def _get_visible_items() -> list[DataEntry]:
        """Return items filtered by the current search text (case-insensitive).
        Matches against name, device_type, and all property key/values.
        """
        query = (search_field.value or "").strip().lower()
        if not query:
            return list(all_items)
        visible = []
        for item in all_items:
            if not item:
                continue
            haystack_parts = [
                (item.name or ""),
                (item.device_type or ""),
            ]
            if getattr(item, "properties", None):
                for k, v in item.properties.items():
                    haystack_parts.append(str(k))
                    haystack_parts.append(str(v))
            haystack = " ".join(haystack_parts).lower()
            if query in haystack:
                visible.append(item)
        return visible

    def _on_item_clicked(item, page: ft.Page, app_state, column: ft.Column, callback, text_color=None):
        """Handle clicking an item in the list.
        Keeps any active search filter (rebuilds only visible items under the filter).
        This nested version closes over the sidebar-local all_items + _get_visible_items.
        """
        app_state.select_item(item)

        # Reload data from DB so the list stays in sync, then re-apply current filter
        try:
            df = load_from_db("input_data")
            fresh = []
            for _, row in df.iterrows():
                try:
                    it = DataEntry.from_dict(row)
                    if it is not None and getattr(it, 'device_type', None):
                        fresh.append(it)
                except Exception:
                    pass
            all_items.clear()
            all_items.extend(fresh)
        except Exception:
            # keep previous all_items on error; fall back to seed only if completely empty
            if not all_items:
                try:
                    fresh = _get_seed_data()
                    all_items.clear()
                    all_items.extend(fresh)
                except Exception:
                    pass

        visible = _get_visible_items()
        _rebuild_item_list(
            column, visible, page, app_state, callback, text_color=text_color,
            on_item_clicked=_on_item_clicked
        )

        # Now safe to update because the column is already mounted on the page
        column.update()

        if callback:
            callback(item)

    def _filter_list(e, column: ft.Column, app_state):
        """Live filter the sidebar list based on search text.
        Rebuilds only the visible items without changing selection or master data.
        """
        visible = _get_visible_items()
        _rebuild_item_list(
            column,
            visible,
            page,
            app_state,
            on_selection_changed,
            text_color=color_scheme.on_primary_container,
            on_item_clicked=_on_item_clicked,
        )
        column.update()

    # Placeholder seeding has been disabled per user request.
    # If you want sample data again, we can re-enable it later.
    # if not items:
    #     items = _get_seed_data()
    #     ...

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

    def refresh_list(auto_select_latest: bool = True):
        """Reload data from DB and refresh the sidebar list.
        auto_select_latest: only auto-select the newest item on create (True),
        pass False from edit saves to avoid deselecting current item.

        On auto-select paths (create + File > New global clear), we clear any active
        search text so the newly created item (or the empty state) is visible.
        """
        # On create / global reset paths, clear the search so the result is visible to the user.
        if auto_select_latest and search_field.value:
            search_field.value = ""
            try:
                search_field.update()
            except Exception:
                pass

        try:
            fdf = load_from_db("input_data")
            fresh = []
            for _, row in fdf.iterrows():
                try:
                    item = DataEntry.from_dict(row)
                    if item is not None and getattr(item, 'device_type', None):
                        fresh.append(item)
                except Exception:
                    pass
        except Exception:
            fresh = []

        # Update the master list used by search filtering
        all_items.clear()
        all_items.extend(fresh)

        # Apply current filter (usually empty after the clear above, or preserved for edit-refresh=False)
        visible = _get_visible_items()
        _rebuild_item_list(
            items_column,
            visible,
            page,
            app_state,
            on_selection_changed,
            text_color=color_scheme.on_primary_container,
            on_item_clicked=_on_item_clicked,
        )

        if fresh and auto_select_latest:
            latest = max(fresh, key=lambda x: x.id or 0)
            app_state.select_item(latest)

        # Extra updates to try to force redraw
        items_column.update()
        page.update()

    # Register so that File > New (and future global resets) can trigger this
    if hasattr(app_state, "register_sidebar_refresh"):
        app_state.register_sidebar_refresh(refresh_list)

    # Initial population — always do a fresh DB load + rebuild on startup.
    # This ensures all existing Racks/Amps from the DB appear immediately when the app opens.
    fresh_items = _load_items_from_db()
    all_items.clear()
    all_items.extend(fresh_items)
    _rebuild_item_list(
        items_column, 
        fresh_items, 
        page, 
        app_state, 
        on_selection_changed,
        text_color=color_scheme.on_primary_container,
        on_item_clicked=_on_item_clicked,
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
                            on_click=lambda e: _show_create_device_dialog(page, on_created=refresh_list),
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
    on_item_clicked: callable = None,
):
    """Rebuild the list of selectable items. 
    Does NOT call .update() — caller is responsible after the control is mounted.

    on_item_clicked: optional per-sidebar click handler (closes over search state).
                     Falls back to the module-level _on_item_clicked if not provided.
    """
    click_handler = on_item_clicked if on_item_clicked is not None else _on_item_clicked

    column.controls.clear()

    for item in items:
        if not item or not item.device_type:
            # Skip bad / incomplete data (can happen after schema migrations)
            continue

        is_selected = (
            app_state.selected_item is not None
            and app_state.selected_item.id == item.id
        )

        # Display based on device_type
        if item.device_type.lower() == "rack":
            display_name = item.name or f"Rack {item.properties.get('Rack #', item.properties.get('rack_number', ''))}".strip()
            icon = ft.Icons.SETTINGS
        else:
            display_name = item.name or get_display_name(item.device_type, item.properties or {})
            icon = ft.Icons.SPEAKER

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
            on_click=lambda e, it=item: click_handler(
                it, page, app_state, column, on_selection_changed, text_color=text_color
            ),
        )
        column.controls.append(tile)


def _on_item_clicked(item, page: ft.Page, app_state, column: ft.Column, callback, text_color=None):
    """Module-level fallback click handler (used only if no per-sidebar handler was passed to rebuild).

    Does a full reload (ignores any active search filter). The sidebar's nested version
    (which has access to all_items/_get_visible_items) is preferred and is passed explicitly.
    """
    app_state.select_item(item)

    # Reload full data from DB (no filtering in this fallback path)
    try:
        df = load_from_db("input_data")
        current_items = []
        for _, row in df.iterrows():
            try:
                it = DataEntry.from_dict(row)
                if it is not None and getattr(it, 'device_type', None):
                    current_items.append(it)
            except Exception:
                pass
    except Exception:
        current_items = []

    _rebuild_item_list(column, current_items, page, app_state, callback, text_color=text_color)

    # Now safe to update because the column is already mounted on the page
    column.update()

    if callback:
        callback(item)


# Note: _filter_list, _on_item_clicked (the filtering-aware one), refresh_list, etc. are
# defined locally inside create_left_sidebar so they can close over per-instance state
# (all_items, search_field, _get_visible_items). The module-level _on_item_clicked is only
# a safe fallback if a rebuild call ever omits the on_item_clicked= kwarg.
