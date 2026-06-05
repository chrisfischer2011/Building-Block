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
    get_rack_amp_slots,
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

            if dtype == "Rack":
                # Multi-rack batch collection
                if not rack_form_rows:
                    show_coming_soon(page, "No rack rows to create.")
                    return
                created_items = []
                batch_names = set()
                for idx, row in enumerate(rack_form_rows, 1):
                    loc = row["loc_dd"].value or ""
                    num = row["num_dd"].value or ""
                    t = row["template_dd"].value or ""
                    rt = row["racktype_dd"].value or ""
                    props = {
                        "Rack Location": loc,
                        "Rack #": num,
                        "Template": t,
                        "Rack Type": rt,
                    }
                    # auto filled values per row
                    for f, v in row.get("auto_values", {}).items():
                        props[f] = v
                    if "Amp Slots" not in props:
                        props["Amp Slots"] = str(get_rack_amp_slots(t, rt))
                    name = get_display_name("Rack", props)
                    if name in batch_names:
                        show_coming_soon(page, f"Duplicate rack name '{name}' within this batch (row {idx}).")
                        return
                    batch_names.add(name)
                    if is_rack_name_taken(name):
                        show_coming_soon(page, f"Rack name '{name}' is already in use (row {idx}).")
                        return
                    new_item = DataEntry(
                        name=name,
                        device_type="Rack",
                        properties=props,
                        notes=""
                    )
                    created_items.append(new_item)

                if created_items:
                    df = pd.DataFrame([it.to_dict() for it in created_items])
                    save_to_db(df, "input_data")
                    print(f"Save successful: {len(created_items)} rack(s)")
                    if on_created:
                        on_created()
                    # trigger inspector refresh (for amp dropdowns etc)
                    try:
                        if hasattr(page, "_app_state"):
                            as_ = page._app_state
                            if hasattr(as_, "_inspector_refresh_callbacks"):
                                for cb in list(getattr(as_, "_inspector_refresh_callbacks", [])):
                                    try:
                                        cb()
                                    except Exception:
                                        pass
                    except Exception:
                        pass
                    page.pop_dialog()
                    page.update()
                    print("=== CREATE MULTI-RACK SAVE FINISHED ===")
                    return
            else:
                # Multi-amp batch (analogous to multi-rack)
                if not amp_form_rows:
                    show_coming_soon(page, "No amp rows to create.")
                    return
                created_items = []
                batch_amp_ids = set()
                for idx, row in enumerate(amp_form_rows, 1):
                    loc = row["loc_dd"].value or ""
                    num = row["num_dd"].value or ""
                    amp_num = row.get("amp_num_dd").value or "" if row.get("amp_num_dd") else ""
                    amp_type = row.get("amp_type_dd").value or "" if row.get("amp_type_dd") else ""
                    amp_id = row.get("amp_id_tf").value or "" if row.get("amp_id_tf") else ""
                    amp_id = normalize_amp_id(amp_id)
                    mode = ""  # default; could add per-row mode_dd if desired

                    if amp_id:
                        try:
                            val = float(amp_id)
                            if not (0.01 <= val <= 99.99):
                                show_coming_soon(page, f"Amp ID must be a number between 0.01 and 99.99 (row {idx})")
                                return
                        except (ValueError, TypeError):
                            show_coming_soon(page, f"Amp ID must be numeric (e.g. 1.01) (row {idx})")
                            return

                        if amp_id in batch_amp_ids or is_amp_id_taken(amp_id):
                            show_coming_soon(page, f"Amp ID '{amp_id}' is already in use — must be unique (row {idx}).")
                            return
                    batch_amp_ids.add(amp_id)

                    props = {
                        "Rack Location": loc,
                        "Rack #": num,
                        "Amp #": amp_num,
                        "Amp Type": amp_type,
                        "Amp ID": amp_id,
                        "Mode": mode,
                    }
                    for f, v in row.get("extra_amp_values", {}).items():
                        props[f] = v

                    name = get_display_name("Amplifier", props)
                    new_item = DataEntry(
                        name=name,
                        device_type="Amplifier",
                        properties=props,
                        notes=""
                    )
                    created_items.append(new_item)

                if created_items:
                    df = pd.DataFrame([it.to_dict() for it in created_items])
                    save_to_db(df, "input_data")
                    print(f"Save successful: {len(created_items)} amp(s)")
                    if on_created:
                        on_created()
                    try:
                        if hasattr(page, "_app_state"):
                            as_ = page._app_state
                            if hasattr(as_, "_inspector_refresh_callbacks"):
                                for cb in list(getattr(as_, "_inspector_refresh_callbacks", [])):
                                    try:
                                        cb()
                                    except Exception:
                                        pass
                    except Exception:
                        pass
                    page.pop_dialog()
                    page.update()
                    print("=== CREATE MULTI-AMP SAVE FINISHED ===")
                    return

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
        dense=True,
        height=40,
        content_padding=ft.Padding.only(left=8, right=8, top=4, bottom=4),
        text_style=ft.TextStyle(color=ft.Colors.BLACK, size=10),
        label_style=ft.TextStyle(color=ft.Colors.BLACK, size=9),
        on_select=_update_rack_suggestion,
    )
    rack_dd = ft.Dropdown(
        ref=rack_num_ref,
        label="Rack #",
        options=[ft.dropdown.Option(o) for o in get_options_for_field("Rack #")],
        dense=True,
        height=40,
        content_padding=ft.Padding.only(left=8, right=8, top=4, bottom=4),
        text_style=ft.TextStyle(color=ft.Colors.BLACK, size=10),
        label_style=ft.TextStyle(color=ft.Colors.BLACK, size=9),
        on_select=_update_rack_suggestion,
    )

    # Bootstrap initial free rack name suggestion (so first open for rack also avoids duplicates)
    _update_rack_suggestion()

    # Rack-only controls (the original Template / Rack Type + 16 auto-fill signal fields)
    template_dd = ft.Dropdown(
        ref=template_ref,
        label="Template",
        options=[ft.dropdown.Option(o) for o in get_options_for_field("Template")],
        dense=True,
        height=40,
        content_padding=ft.Padding.only(left=8, right=8, top=4, bottom=4),
        text_style=ft.TextStyle(color=ft.Colors.BLACK, size=10),
        label_style=ft.TextStyle(color=ft.Colors.BLACK, size=9),
        on_select=_auto_fill_from_template,
    )
    racktype_dd = ft.Dropdown(
        ref=rack_type_ref,
        label="Rack Type",
        options=[ft.dropdown.Option(o) for o in get_options_for_field("Rack Type")],
        dense=True,
        height=40,
        content_padding=ft.Padding.only(left=8, right=8, top=4, bottom=4),
        text_style=ft.TextStyle(color=ft.Colors.BLACK, size=10),
        label_style=ft.TextStyle(color=ft.Colors.BLACK, size=9),
        on_select=_auto_fill_from_template,
    )

    # Info about taken rack names so user never creates duplicate like two "SL2"
    taken_rack_names = get_taken_rack_names()
    taken_rack_text = ft.Text(
        f"Taken Rack names (never duplicate e.g. 2 SL2): {', '.join(sorted(taken_rack_names)) if taken_rack_names else 'none yet'}",
        size=9,
        italic=True,
        color=ft.Colors.BLACK,
    )

    rack_auto_ctrls = [
        ft.Dropdown(
            ref=auto_fill_field_refs[f],
            label=f,
            options=[ft.dropdown.Option(o) for o in get_options_for_field(f)],
            dense=True,
            height=40,
            content_padding=ft.Padding.only(left=8, right=8, top=4, bottom=4),
            text_style=ft.TextStyle(color=ft.Colors.BLACK, size=10),
            label_style=ft.TextStyle(color=ft.Colors.BLACK, size=9),
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
        ft.Text("Amplifier Details", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK, visible=False),
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
                dense=True,
                height=40,
                content_padding=ft.Padding.only(left=8, right=8, top=4, bottom=4),
                text_style=ft.TextStyle(color=ft.Colors.BLACK, size=10),
                label_style=ft.TextStyle(color=ft.Colors.BLACK, size=9),
                visible=(f in amp_show_fields),
            )
        else:
            hint = "0.01-99.99 with 2 decimals (e.g. 1.00, 42.50)  (must be unique)" if f == "Amp ID" else None
            ctrl = ft.TextField(
                ref=ref,
                label=f,
                dense=True,
                height=40,
                hint_text=hint,
                content_padding=ft.Padding.only(left=8, right=8, top=4, bottom=4),
                text_style=ft.TextStyle(color=ft.Colors.BLACK, size=10),
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
        color=ft.Colors.BLACK,
    )
    amp_ctrls.append(taken_info)

    # === Multi-rack create support (Device Type=Rack) ===
    # Dynamic growing rows with + button. Each row: Loc, #, Template, Rack Type.
    # Per-row auto-suggest and template auto-fill (stored in auto_values dict, no extra visible UI for autos).
    # Batch create + validation (intra-batch + DB rack name uniqueness) handled in _save.
    rack_form_rows = []  # list of dicts: {'loc_dd':, 'num_dd':, 'template_dd':, 'racktype_dd':, 'auto_values':dict, 'ui':}
    # Using ListView (instead of Column+scroll) for more stable stacking of fixed-height row wrappers on dynamic + appends.
    # spacing=4 + faint purple viewport bg creates visible separator strips between the colored row slots (borders won't touch).
    # Inside each slot: inner Container(alignment=CENTER) + its padding for proper vertical centering of the row inside the fixed slot (no spacer clipping). Row vertical align only for internal items. Outer height=60 is the slot size.
    rack_rows_column = ft.ListView(controls=[], spacing=4, auto_scroll=True, expand=False)

    def _add_rack_row(e=None):
        """Add a new rack creation row."""
        row_idx = len(rack_form_rows) + 1

        row_loc = ft.Dropdown(
            options=[ft.dropdown.Option(o) for o in get_options_for_field("Rack Location")],
            dense=True,
            height=28,
            width=180,
            text_size=11,
            content_padding=ft.Padding.only(left=3, right=3, top=0, bottom=0),
            text_style=ft.TextStyle(color=ft.Colors.BLACK, size=11),
        )
        row_num = ft.Dropdown(
            options=[ft.dropdown.Option(o) for o in get_options_for_field("Rack #")],
            dense=True,
            height=28,
            width=120,
            text_size=11,
            content_padding=ft.Padding.only(left=3, right=3, top=0, bottom=0),
            text_style=ft.TextStyle(color=ft.Colors.BLACK, size=11),
        )
        row_t = ft.Dropdown(
            options=[ft.dropdown.Option(o) for o in get_options_for_field("Template")],
            dense=True,
            height=28,
            width=90,
            text_size=11,
            content_padding=ft.Padding.only(left=3, right=3, top=0, bottom=0),
            text_style=ft.TextStyle(color=ft.Colors.BLACK, size=11),
        )
        row_rt = ft.Dropdown(
            options=[ft.dropdown.Option(o) for o in get_options_for_field("Rack Type")],
            dense=True,
            height=28,
            width=100,
            text_size=11,
            content_padding=ft.Padding.only(left=3, right=3, top=0, bottom=0),
            text_style=ft.TextStyle(color=ft.Colors.BLACK, size=11),
        )

        row_auto_values = {}

        def _row_update_suggestion(e=None, rloc=row_loc, rnum=row_num):
            loc_val = rloc.value or ""
            try:
                current_num = int(rnum.value or 0)
            except (ValueError, TypeError):
                current_num = 0
            if current_num < 1:
                current_num = 1
                try:
                    rnum.value = "1"
                except Exception:
                    pass
            name = get_rack_name(loc_val, current_num)
            if is_rack_name_taken(name):
                for n in range(1, 11):
                    test_name = get_rack_name(loc_val, n)
                    if not is_rack_name_taken(test_name):
                        rnum.value = str(n)
                        break
            try:
                rnum.update()
            except Exception:
                pass

        row_loc.on_select = _row_update_suggestion
        row_num.on_select = _row_update_suggestion

        def _row_auto_fill(e=None, rtpl=row_t, rrt=row_rt, rauto=row_auto_values):
            t = rtpl.value
            rt = rrt.value
            if not t or not rt:
                rauto.clear()
                return
            defaults = get_rack_template_defaults(t, rt)
            rauto.clear()
            rauto.update(defaults)
            rauto["Amp Slots"] = str(get_rack_amp_slots(t, rt))

        row_t.on_select = _row_auto_fill
        row_rt.on_select = _row_auto_fill

        def _remove_row(e=None, rdata=None):
            if rdata in rack_form_rows and len(rack_form_rows) > 1:
                print(f"[DEBUG REMOVE RACK] removing, before len={len(rack_form_rows)}")
                rack_form_rows.remove(rdata)
                if rdata.get("ui") in rack_rows_column.controls:
                    rack_rows_column.controls.remove(rdata["ui"])
                try:
                    rack_rows_column.update()
                    rack_rows_viewport.update()
                except Exception:
                    pass
                print(f"[DEBUG REMOVE RACK] after len={len(rack_form_rows)}")

        rem_btn = ft.IconButton(
            icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
            icon_size=13,
            width=20,
            height=20,
            padding=0,
            tooltip="Remove row",
            on_click=lambda e, rd=None: _remove_row(e, rd),
        )

        row_ui = ft.Row(
            [
                ft.Text(f"R{row_idx}", size=8, width=16),
                row_loc,
                row_num,
                row_t,
                row_rt,
                rem_btn,
            ],
            spacing=2,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Removed vertical padding from row_content (as requested: no extra vertical padding/margins around the dropdowns).
        # The dropdown boxes size purely from height=28 + row_ui's vertical_alignment=CENTER (for prefix/rem_btn alignment).
        row_content = ft.Container(
            content=row_ui,
            padding=ft.Padding.symmetric(horizontal=2, vertical=0),
        )

        # Better centering inside the fixed-height colored slot (row_wrapper):
        # The inner Container uses alignment=ft.Alignment.CENTER so the row is vertically (and horizontally) centered
        # within the outer fixed height. The padding on this inner container creates the visible colored "gap"/margin
        # around the row *inside* the black border of the frame. Symmetric vertical padding gives even space top+bottom.
        # This avoids the old spacer overflow/clipping problem and ensures proper vertical centering inside the slot.
        # The outer height=60 (user's value) enforces consistent row slots so adding more rows via + doesn't cause overlap.
        # Tune the vertical padding value (currently 6) for more/less internal gap. Or change outer height if you want
        # denser or taller row slots overall.
        debug_colors = [ft.Colors.RED, ft.Colors.BLUE, ft.Colors.GREEN, ft.Colors.AMBER, ft.Colors.PURPLE, ft.Colors.CYAN]
        dbg_color = ft.Colors.with_opacity(0.22, debug_colors[(row_idx-1) % len(debug_colors)])
        row_wrapper = ft.Container(
            content=ft.Container(
                content=row_content,
                alignment=ft.Alignment.CENTER,
                padding=ft.Padding.symmetric(horizontal=2, vertical=6),
            ),
            height=60,
            bgcolor=dbg_color,
            border=ft.Border(
                left=ft.BorderSide(width=1, color=ft.Colors.BLACK),
                top=ft.BorderSide(width=1, color=ft.Colors.BLACK),
                right=ft.BorderSide(width=1, color=ft.Colors.BLACK),
                bottom=ft.BorderSide(width=1, color=ft.Colors.BLACK),
            ),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

        row_data = {
            "loc_dd": row_loc,
            "num_dd": row_num,
            "template_dd": row_t,
            "racktype_dd": row_rt,
            "auto_values": row_auto_values,
            "ui": row_wrapper,
        }
        rem_btn.on_click = lambda e, rd=row_data: _remove_row(e, rd)

        rack_form_rows.append(row_data)
        rack_rows_column.controls.append(row_wrapper)
        try:
            rack_rows_column.update()
            rack_rows_viewport.update()
        except Exception:
            pass

        print(f"[DEBUG ADD RACK] added row_idx={row_idx}, now total rack_form_rows={len(rack_form_rows)}")
        _row_update_suggestion()

    add_row_btn = ft.IconButton(
        icon=ft.Icons.ADD_CIRCLE,
        icon_size=15,
        width=22,
        height=22,
        padding=0,
        tooltip="Add another rack row",
        on_click=lambda e: _add_rack_row(),
    )
    # DEBUG wrapper: Row itself can't take bgcolor, so wrap for the subtle header tint.
    rack_header = ft.Container(
        content=ft.Row(
            [ft.Text("Create multiple racks at once", size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK), add_row_btn],
            spacing=3,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREY),
        padding=2,
    )

    # One-time compact labels row (no per-dd `label` on data rows to keep each row short/not tall)
    # DEBUG wrapper (Row can't take bgcolor/border directly)
    rack_labels_row = ft.Container(
        content=ft.Row(
            [
                ft.Text("", width=16),
                ft.Text("Loc", size=9, width=180, text_align=ft.TextAlign.CENTER, color=ft.Colors.BLACK),
                ft.Text("#", size=9, width=120, text_align=ft.TextAlign.CENTER, color=ft.Colors.BLACK),
                ft.Text("Template", size=9, width=90, text_align=ft.TextAlign.CENTER, color=ft.Colors.BLACK),
                ft.Text("Rack Type", size=9, width=100, text_align=ft.TextAlign.CENTER, color=ft.Colors.BLACK),
            ],
            spacing=1,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.YELLOW),
        border=ft.Border(
            left=ft.BorderSide(width=1, color=ft.Colors.ORANGE),
            top=ft.BorderSide(width=1, color=ft.Colors.ORANGE),
            right=ft.BorderSide(width=1, color=ft.Colors.ORANGE),
            bottom=ft.BorderSide(width=1, color=ft.Colors.ORANGE),
        ),
        padding=2,
    )

    # Fixed height viewport for the rows list. DEBUG border (purple) + faint purple bg frames the list of colored row slots.
    # The faint bg makes the 4px spacing gaps appear as clear tinted strips separating the red/blue/etc frames. (Debug only)
    # Each slot uses inner Container(alignment=CENTER) + padding for even vertical centering/gap inside the colored frame. Outer height=60 is the fixed slot.
    rack_rows_viewport = ft.Container(
        content=rack_rows_column,
        height=300,
        expand=False,
        border=ft.Border(
            left=ft.BorderSide(width=2, color=ft.Colors.PURPLE),
            top=ft.BorderSide(width=2, color=ft.Colors.PURPLE),
            right=ft.BorderSide(width=2, color=ft.Colors.PURPLE),
            bottom=ft.BorderSide(width=2, color=ft.Colors.PURPLE),
        ),
        padding=2,
        # Very faint purple bg so the spacing gaps between colored row frames are easy to see as separator strips.
        bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.PURPLE),
    )
    rack_multi = ft.Column(
        [rack_header, rack_labels_row, rack_rows_viewport, taken_rack_text],
        tight=True,
        spacing=2,
        visible=False,
        # (outer debug border removed — Row/Column don't accept it directly; the per-row colored bands + purple viewport border provide the visual)
    )

    # === Multi-amp create support (symmetric to multi-rack, for Device Type=Amplifier) ===
    # Rows with + . Per-row: Loc, Rack#, Amp#, Amp Type, Amp ID (visible key fields for initial amp create).
    # Other amp fields default to "" per row.
    # Per-row free Amp ID prefill (skipping db + current batch rows), normalize on blur.
    # Batch save with amp id range + uniqueness (batch + db) checks.
    amp_form_rows = []
    # Using ListView (instead of Column+scroll) for more stable stacking of fixed-height row wrappers on dynamic + appends.
    # spacing=4 + faint purple viewport bg creates visible separator strips between the colored row slots (borders won't touch).
    # Inside each slot: inner Container(alignment=CENTER) + its padding for proper vertical centering of the row inside the fixed slot (no spacer clipping). Row vertical align only for internal items. Outer height=60 is the slot size.
    amp_rows_column = ft.ListView(controls=[], spacing=4, auto_scroll=True, expand=False)

    def _add_amp_row(e=None):
        row_idx = len(amp_form_rows) + 1

        row_loc = ft.Dropdown(
            options=[ft.dropdown.Option(o) for o in get_options_for_field("Rack Location")],
            dense=True,
            height=28,
            width=180,
            text_size=11,
            content_padding=ft.Padding.only(left=3, right=3, top=0, bottom=0),
            text_style=ft.TextStyle(color=ft.Colors.BLACK, size=11),
        )
        row_num = ft.Dropdown(
            options=[ft.dropdown.Option(o) for o in get_options_for_field("Rack #")],
            dense=True,
            height=28,
            width=100,
            text_size=11,
            content_padding=ft.Padding.only(left=3, right=3, top=0, bottom=0),
            text_style=ft.TextStyle(color=ft.Colors.BLACK, size=11),
        )
        row_amp_num = ft.Dropdown(
            options=[ft.dropdown.Option(o) for o in get_options_for_field("Amp #")],
            dense=True,
            height=28,
            width=100,
            text_size=11,
            content_padding=ft.Padding.only(left=3, right=3, top=0, bottom=0),
            text_style=ft.TextStyle(color=ft.Colors.BLACK, size=11),
        )
        row_amp_type = ft.Dropdown(
            options=[ft.dropdown.Option(o) for o in get_options_for_field("Amp Type")],
            dense=True,
            height=28,
            width=85,
            text_size=11,
            content_padding=ft.Padding.only(left=3, right=3, top=0, bottom=0),
            text_style=ft.TextStyle(color=ft.Colors.BLACK, size=11),
        )
        row_amp_id = ft.TextField(
            dense=True,
            height=28,
            width=85,
            text_size=10,
            hint_text="e.g. 1.00 (unique)",
            content_padding=ft.Padding.only(left=3, right=3, top=0, bottom=0),
            text_style=ft.TextStyle(color=ft.Colors.BLACK, size=10),
        )

        row_extra = {f: "" for f in amp_fields if f not in ["Amp #", "Amp Type", "Amp ID"]}

        # include Mode if wanted, but default empty ok; can add row_mode if needed later

        def _normalize_amp_id(e=None, ctrl=row_amp_id):
            try:
                ctrl.value = normalize_amp_id(ctrl.value)
                ctrl.update()
            except Exception:
                pass
        row_amp_id.on_blur = _normalize_amp_id

        def _row_amp_suggest(e=None):
            # prefill/update free id considering db + other rows
            pass  # will prefill on add

        # for loc/num/amp_num changes, could re-suggest id, but simple for now

        def _remove_amp_row(e=None, rdata=None):
            if rdata in amp_form_rows and len(amp_form_rows) > 1:
                print(f"[DEBUG REMOVE AMP] removing, before len={len(amp_form_rows)}")
                amp_form_rows.remove(rdata)
                if rdata.get("ui") in amp_rows_column.controls:
                    amp_rows_column.controls.remove(rdata["ui"])
                try:
                    amp_rows_column.update()
                    amp_rows_viewport.update()
                except Exception:
                    pass
                print(f"[DEBUG REMOVE AMP] after len={len(amp_form_rows)}")

        rem_btn = ft.IconButton(
            icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
            icon_size=13,
            width=20,
            height=20,
            padding=0,
            tooltip="Remove row",
            on_click=lambda e, rd=None: _remove_amp_row(e, rd),
        )

        row_ui = ft.Row(
            [
                ft.Text(f"A{row_idx}", size=8, width=16),
                row_loc,
                row_num,
                row_amp_num,
                row_amp_type,
                row_amp_id,
                rem_btn,
            ],
            spacing=2,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Removed vertical padding from row_content (as requested: no extra padding/margins around the dropdowns vertically).
        # Removed vertical padding from row_content (as requested: no extra padding/margins around the dropdowns vertically).
        # The dropdown boxes are now sized purely by their height=28 + the Row's vertical_alignment=ft.CrossAxisAlignment.CENTER
        # (which aligns the prefix text and rem_btn vertically to the dropdowns with no extra vertical margin).
        row_content = ft.Container(
            content=row_ui,
            padding=ft.Padding.symmetric(horizontal=2, vertical=0),
        )

        # Better centering inside the fixed-height colored slot (row_wrapper):
        # The inner Container uses alignment=ft.Alignment.CENTER so the row is vertically (and horizontally) centered
        # within the outer fixed height. The padding on this inner container creates the visible colored "gap"/margin
        # around the row *inside* the black border of the frame. Symmetric vertical padding gives even space top+bottom.
        # This avoids the old spacer overflow/clipping problem and ensures proper vertical centering inside the slot.
        # The outer height=60 (user's value) enforces consistent row slots so adding more rows via + doesn't cause overlap.
        # Tune the vertical padding value (currently 6) for more/less internal gap. Or change outer height if you want
        # denser or taller row slots overall.
        debug_colors = [ft.Colors.RED, ft.Colors.BLUE, ft.Colors.GREEN, ft.Colors.AMBER, ft.Colors.PURPLE, ft.Colors.CYAN]
        dbg_color = ft.Colors.with_opacity(0.22, debug_colors[(row_idx-1) % len(debug_colors)])
        row_wrapper = ft.Container(
            content=ft.Container(
                content=row_content,
                alignment=ft.Alignment.CENTER,
                padding=ft.Padding.symmetric(horizontal=2, vertical=6),
            ),
            height=60,
            bgcolor=dbg_color,
            border=ft.Border(
                left=ft.BorderSide(width=1, color=ft.Colors.BLACK),
                top=ft.BorderSide(width=1, color=ft.Colors.BLACK),
                right=ft.BorderSide(width=1, color=ft.Colors.BLACK),
                bottom=ft.BorderSide(width=1, color=ft.Colors.BLACK),
            ),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

        row_data = {
            "loc_dd": row_loc,
            "num_dd": row_num,
            "amp_num_dd": row_amp_num,
            "amp_type_dd": row_amp_type,
            "amp_id_tf": row_amp_id,
            "extra_amp_values": row_extra,
            "ui": row_wrapper,
        }
        rem_btn.on_click = lambda e, rd=row_data: _remove_amp_row(e, rd)

        amp_form_rows.append(row_data)
        amp_rows_column.controls.append(row_wrapper)
        try:
            amp_rows_column.update()
            amp_rows_viewport.update()
        except Exception:
            pass

        print(f"[DEBUG ADD AMP] added row_idx={row_idx}, now total amp_form_rows={len(amp_form_rows)}")

        # prefill next free Amp ID, skipping db + current batch rows
        try:
            taken = set(get_taken_amp_ids())
            for r in amp_form_rows[:-1]:  # previous
                aid = r.get("amp_id_tf").value or ""
                if aid:
                    taken.add(normalize_amp_id(aid))
            free = get_next_free_amp_id()
            while free in taken:
                f = float(free) + 0.01
                free = f"{f:.2f}"
            row_amp_id.value = free
            row_amp_id.update()
        except Exception:
            pass

    add_amp_btn = ft.IconButton(
        icon=ft.Icons.ADD_CIRCLE,
        icon_size=15,
        width=22,
        height=22,
        padding=0,
        tooltip="Add another amp row",
        on_click=lambda e: _add_amp_row(),
    )
    # DEBUG wrapper: Row itself can't take bgcolor, so wrap for the subtle header tint.
    amp_header = ft.Container(
        content=ft.Row(
            [ft.Text("Create multiple amps at once", size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK), add_amp_btn],
            spacing=3,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREY),
        padding=2,
    )
    # reuse or recreate taken for amps
    taken_amp_text = ft.Text(
        f"Taken Amp IDs (avoid these): {', '.join(get_taken_amp_ids()) if get_taken_amp_ids() else 'none yet'}",
        size=9,
        italic=True,
        color=ft.Colors.BLACK,
    )

    # One-time compact labels row (no per-dd `label` on data rows to keep each row short/not tall)
    # DEBUG wrapper (Row can't take bgcolor/border directly)
    amp_labels_row = ft.Container(
        content=ft.Row(
            [
                ft.Text("", width=16),
                ft.Text("Loc", size=9, width=180, text_align=ft.TextAlign.CENTER, color=ft.Colors.BLACK),
                ft.Text("#", size=9, width=100, text_align=ft.TextAlign.CENTER, color=ft.Colors.BLACK),
                ft.Text("Amp #", size=9, width=100, text_align=ft.TextAlign.CENTER, color=ft.Colors.BLACK),
                ft.Text("Amp Type", size=9, width=85, text_align=ft.TextAlign.CENTER, color=ft.Colors.BLACK),
                ft.Text("Amp ID", size=9, width=85, text_align=ft.TextAlign.CENTER, color=ft.Colors.BLACK),
            ],
            spacing=1,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.YELLOW),
        border=ft.Border(
            left=ft.BorderSide(width=1, color=ft.Colors.ORANGE),
            top=ft.BorderSide(width=1, color=ft.Colors.ORANGE),
            right=ft.BorderSide(width=1, color=ft.Colors.ORANGE),
            bottom=ft.BorderSide(width=1, color=ft.Colors.ORANGE),
        ),
        padding=2,
    )

    # Fixed height viewport for the rows list. DEBUG border (purple) + faint purple bg frames the list of colored row slots.
    # The faint bg makes the 4px spacing gaps appear as clear tinted strips separating the red/blue/etc frames. (Debug only)
    # Each slot uses inner Container(alignment=CENTER) + padding for even vertical centering/gap inside the colored frame. Outer height=60 is the fixed slot.
    amp_rows_viewport = ft.Container(
        content=amp_rows_column,
        height=300,
        expand=False,
        border=ft.Border(
            left=ft.BorderSide(width=2, color=ft.Colors.PURPLE),
            top=ft.BorderSide(width=2, color=ft.Colors.PURPLE),
            right=ft.BorderSide(width=2, color=ft.Colors.PURPLE),
            bottom=ft.BorderSide(width=2, color=ft.Colors.PURPLE),
        ),
        padding=2,
        # Very faint purple bg so the spacing gaps between colored row frames are easy to see as separator strips.
        bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.PURPLE),
    )
    amp_multi = ft.Column(
        [amp_header, amp_labels_row, amp_rows_viewport, taken_amp_text],
        tight=True,
        spacing=2,
        visible=False,
        # (outer debug border removed — Row/Column don't accept it directly; the per-row colored bands + purple viewport border provide the visual)
    )

    # Visibility groups (toggled when Device Type changes)
    # rack_only / amp_only kept for fallback if needed; we use *multi for both now.
    rack_only = ft.Column(
        [template_dd, racktype_dd, taken_rack_text] + rack_auto_ctrls,
        tight=True,
        visible=True,
    )
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
        # For both: use respective multi-row areas. Top level loc/rack_dd hidden (now per-row).
        loc_dd.visible = False
        rack_dd.visible = False
        rack_multi.visible = is_rack
        amp_multi.visible = not is_rack

        if is_rack:
            if len(rack_form_rows) == 0:
                print("[DEBUG SWITCH] adding first RACK row")
                _add_rack_row()
        else:
            if len(amp_form_rows) == 0:
                print("[DEBUG SWITCH] adding first AMP row")
                _add_amp_row()
            # prefill logic for amp id already in _add_amp_row

        # Let auto-fill run for rack (harmless for amp)
        try:
            _auto_fill_from_template()
            rack_multi.update()
            amp_multi.update()
            print(f"[DEBUG SWITCH] after updates: rack_rows={len(rack_form_rows)}, amp_rows={len(amp_form_rows)}")
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
        dense=True,
        height=40,
        content_padding=ft.Padding.only(left=8, right=8, top=4, bottom=4),
        text_style=ft.TextStyle(color=ft.Colors.BLACK, size=10),
        label_style=ft.TextStyle(color=ft.Colors.BLACK, size=9),
        on_select=_switch_form,
    )

    dlg = ft.AlertDialog(
        title=ft.Text("Create New Device", color=ft.Colors.BLACK),
        content=ft.Container(
            width=780,  # wider for the multi-row fields + debug colored slot frames. Debug visuals are temporary.
            bgcolor=ft.Colors.WHITE,  # ensure light background for black text readability
            content=ft.Column(
                [
                    ft.Text("DEBUG MODE (temporary): Vertical padding removed from row_content (vert=0 per request). Dropdowns use only height=28 + Row vertical align. Proper centering inside colored slot: inner Container(alignment=ft.Alignment.CENTER) + its padding (vert=6 symmetric) creates even colored gap top+bottom *inside* the fixed 60px frame. Outer height enforces slot size to avoid overlap on +add. Tune inner vert padding or outer height. Purple separators unchanged. Report gap measurements inside frames after adding 2nd row. [DEBUG] in console. We strip debug when centering/gaps good.", size=8, color=ft.Colors.RED, italic=True),
                    device_type_dd,
                    rack_multi,   # multi-rack rows (visible when Device=Rack)
                    amp_multi,    # multi-amp rows (visible when Device=Amplifier)
                ],
                tight=True,
                spacing=4,
            ),
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
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
