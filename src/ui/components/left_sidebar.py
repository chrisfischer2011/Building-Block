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
    CORE_RACK_FIELDS,
    DataEntry,
    get_fields_for_device,
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

            # Collect the 4 core fields into properties for now
            props = {
                "Rack Location": location_ref.current.value or "",
                "Rack #": rack_num_ref.current.value or "",
                "Template": template_ref.current.value or "",
                "Rack Type": rack_type_ref.current.value or "",
            }

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
                ),
                # Only show these 4 for Rack (we can expand later)
                ft.Dropdown(ref=location_ref, label="Rack Location", options=[ft.dropdown.Option(o) for o in get_options_for_field("Rack Location")], height=50),
                ft.Dropdown(ref=rack_num_ref, label="Rack #", options=[ft.dropdown.Option(o) for o in get_options_for_field("Rack #")], height=50),
                ft.Dropdown(ref=template_ref, label="Template", options=[ft.dropdown.Option(o) for o in get_options_for_field("Template")], height=50),
                ft.Dropdown(ref=rack_type_ref, label="Rack Type", options=[ft.dropdown.Option(o) for o in get_options_for_field("Rack Type")], height=50),
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
            raw_count = len(df)
            print(f"[SIDEBAR] load_from_db returned {raw_count} raw rows")

            loaded = []
            for _, row in df.iterrows():
                # Do NOT do "if row:" or "if not row:" here — row is a pandas Series
                # and that causes "truth value of a Series is ambiguous".
                try:
                    item = DataEntry.from_dict(row)
                    loaded.append(item)
                except Exception as conv_err:
                    print(f"[SIDEBAR]   Skipped row during from_dict: {conv_err}")

            filtered = [item for item in loaded if item and getattr(item, 'device_type', None)]
            print(f"[SIDEBAR] After conversion & filter: {len(filtered)} items (from {raw_count} raw)")
            for it in filtered[:5]:  # show first few for debugging
                print(f"    - {it.name} | type: {it.device_type}")
            if len(filtered) > 5:
                print(f"    ... and {len(filtered)-5} more")
            return filtered
        except Exception as ex:
            print(f"[SIDEBAR] ERROR loading items from DB: {ex}")
            return []

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

    def refresh_list():
        """Reload data from DB and refresh the sidebar list + auto-select latest."""
        print("[SIDEBAR] === REFRESH_LIST CALLED (e.g. after create or New) ===")
        try:
            fdf = load_from_db("input_data")
            print("Loaded rows from DB:", len(fdf))
            fresh = []
            for _, row in fdf.iterrows():
                try:
                    item = DataEntry.from_dict(row)
                    if item is not None and getattr(item, 'device_type', None):
                        fresh.append(item)
                except Exception as row_err:
                    print("  Skipping bad row:", row_err)
            print("Converted to valid DataEntry objects:", len(fresh))
            print("After device_type filter:", len(fresh))
            for it in fresh:
                print("  - Loaded item:", it.name, "| type:", it.device_type)
        except Exception as ex:
            print("Error loading from DB in refresh_list:", ex)
            fresh = []

        _rebuild_item_list(
            items_column,
            fresh,
            page,
            app_state,
            on_selection_changed,
            text_color=color_scheme.on_primary_container,
        )

        if fresh:
            latest = max(fresh, key=lambda x: x.id or 0)
            app_state.select_item(latest)
            print("Auto-selected latest item:", latest.name)

        # Extra updates to try to force redraw
        items_column.update()
        page.update()
        print("=== REFRESH_LIST FINISHED ===")

    # Register so that File > New (and future global resets) can trigger this
    if hasattr(app_state, "register_sidebar_refresh"):
        app_state.register_sidebar_refresh(refresh_list)

    # Initial population — always do a fresh DB load + rebuild on startup.
    # This is what makes all existing Racks appear immediately when you open the app.
    print("[SIDEBAR] Performing initial load for sidebar on startup...")
    fresh_items = _load_items_from_db()
    print(f"[SIDEBAR] Passing {len(fresh_items)} items to initial _rebuild_item_list")
    _rebuild_item_list(
        items_column, 
        fresh_items, 
        page, 
        app_state, 
        on_selection_changed,
        text_color=color_scheme.on_primary_container,
    )
    print("[SIDEBAR] Initial sidebar build complete")

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
    print(f"[SIDEBAR] _rebuild_item_list called with {len(items)} items")
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
    """Handle clicking an item in the list."""
    app_state.select_item(item)

    # Reload data from DB so the list stays in sync
    try:
        df = load_from_db("input_data")
        current_items = [DataEntry.from_dict(row) for _, row in df.iterrows()]
    except Exception:
        current_items = _get_seed_data()

    # Rebuild the list so the visual selection updates
    _rebuild_item_list(column, current_items, page, app_state, callback, text_color=text_color)

    # Now safe to update because the column is already mounted on the page
    column.update()

    if callback:
        callback(item)


def _filter_list(e, column: ft.Column, app_state):
    """Basic filtering placeholder for Phase 5."""
    pass
