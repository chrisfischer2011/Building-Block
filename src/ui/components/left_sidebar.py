"""
Left Sidebar Component

Generic reusable left sidebar panel. Typically used for navigation,
item lists, or selectors.

This is the generic version of what was previously the Rack & Amp selector.
"""

import flet as ft
import pandas as pd

from src.core.database import load_from_db, save_to_db
from src.core.models import (
    DataEntry,
    get_options_for_field,
    get_rack_template_defaults,
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

            if dtype == "Rack":
                loc = location_ref.current.value or ""
                num = rack_num_ref.current.value or ""
                import re
                m = re.search(r'\(([^)]+)\)', loc)
                pref = m.group(1) if m else "".join(c for c in loc if c.isupper())[:2] or "RACK"
                name = f"{pref}{num}"
            else:
                name = "New Amplifier"

            # Collect core + auto-fill fields (only meaningful for Rack)
            props = {
                "Rack Location": location_ref.current.value or "",
                "Rack #": rack_num_ref.current.value or "",
                "Template": template_ref.current.value or "",
                "Rack Type": rack_type_ref.current.value or "",
            }
            if dtype == "Rack":
                for f in auto_fill_fields:
                    if f in auto_fill_field_refs and auto_fill_field_refs[f].current:
                        props[f] = auto_fill_field_refs[f].current.value or ""

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

    dlg = ft.AlertDialog(
        title=ft.Text("Create New Device"),
        content=ft.Column(
            [
                ft.Dropdown(
                    ref=device_type_ref,
                    label="Device Type",
                    options=[
                        ft.dropdown.Option("Rack"),
                        ft.dropdown.Option("Amplifier"),
                    ],
                    value="Rack",
                    on_select=_auto_fill_from_template,
                ),
                # Only show these 4 for Rack (we can expand later)
                ft.Dropdown(ref=location_ref, label="Rack Location", options=[ft.dropdown.Option(o) for o in get_options_for_field("Rack Location")], height=50),
                ft.Dropdown(ref=rack_num_ref, label="Rack #", options=[ft.dropdown.Option(o) for o in get_options_for_field("Rack #")], height=50),
                ft.Dropdown(ref=template_ref, label="Template", options=[ft.dropdown.Option(o) for o in get_options_for_field("Template")], height=50, on_select=_auto_fill_from_template),
                ft.Dropdown(ref=rack_type_ref, label="Rack Type", options=[ft.dropdown.Option(o) for o in get_options_for_field("Rack Type")], height=50, on_select=_auto_fill_from_template),
                # Auto-fill fields (populated from Template + Rack Type)
                *[ft.Dropdown(
                    ref=auto_fill_field_refs[f],
                    label=f,
                    options=[ft.dropdown.Option(o) for o in get_options_for_field(f)],
                    height=50,
                ) for f in auto_fill_fields],
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

    # Trigger initial auto-fill if the dropdowns happen to have values already set
    _auto_fill_from_template()

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
):
    """Rebuild the list of selectable items. 
    Does NOT call .update() — caller is responsible after the control is mounted.
    """
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
            display_name = item.name or f"Rack {item.properties.get('rack_number', '')}".strip()
            icon = ft.Icons.SETTINGS
        else:
            display_name = item.name or item.properties.get("model", "Amplifier")
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
            on_click=lambda e, it=item: _on_item_clicked(
                it, page, app_state, column, on_selection_changed, text_color=text_color
            ),
        )
        column.controls.append(tile)


def _on_item_clicked(item, page: ft.Page, app_state, column: ft.Column, callback, text_color=None):
    """Handle clicking an item in the list.
    Keeps any active search filter (rebuilds only visible items under the filter).
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
    _rebuild_item_list(column, visible, page, app_state, callback, text_color=text_color)

    # Now safe to update because the column is already mounted on the page
    column.update()

    if callback:
        callback(item)


# _filter_list is now defined locally inside create_left_sidebar (with real implementation + closure over search_field/all_items).
# The previous placeholder has been replaced.
