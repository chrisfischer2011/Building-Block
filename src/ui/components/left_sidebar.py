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
    FORM_CONTENT_PADDING,
    FORM_CONTROL_HEIGHT,
    FORM_DENSE,
    FORM_TEXT_SIZE,
    FORM_TEXT_STYLE,
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
    """Show the multi-create AlertDialog for Racks or Amplifiers.
    Supports adding multiple rows dynamically (+ button), per-row auto-suggest / template fill,
    batch uniqueness checks, and shared styling via the _make_* helpers + ROW_* constants.
    Clean production layout only (no debug scaffolding).
    """

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

    # Shared styling + factories for the dynamic multi-create rows (racks and amps).
    # These now come from the central FORM_* tokens in theme.py so the Add popup matches
    # the Inspector editable fields (and any future form controls).
    # See _make_row_dropdown, _make_row_textfield, _make_row_frame, RACK_ROW_SPECS, AMP_ROW_SPECS.
    #
    # In clean mode raw controls are placed directly into the row_ui Row (no per-field height wrapper).
    # The row_content wrapper is minimal (just horizontal padding + auto height).
    # The outer row_wrapper (_make_row_frame, 60px in clean) provides the slot + vertical gaps via centering.
    ROW_CONTROL_HEIGHT = FORM_CONTROL_HEIGHT
    ROW_TEXT_SIZE = FORM_TEXT_SIZE
    ROW_CONTENT_PADDING = FORM_CONTENT_PADDING
    ROW_TEXT_STYLE = FORM_TEXT_STYLE
    ROW_DENSE = FORM_DENSE

    # ROW_CONTENT_HEIGHT is no longer used for a fixed strip height (we simplified row_content
    # to a thin horizontal-padding wrapper only, to reduce redundant height layers).
    # The outer _make_row_frame (60px in clean) now directly provides the slot + gaps via centering.
    # Kept for reference / possible future use.
    ROW_CONTENT_HEIGHT = ROW_CONTROL_HEIGHT + 8

    def _make_row_dropdown(options, width, **overrides):
        """Create a styled dropdown for use in multi-create rows.
        All visual properties (dense, padding, text color/size) come from the
        shared ROW_* constants so racks and amps render identically.
        In clean mode raw controls go directly into the Row (height determined by layout + frame).
        """
        params = {
            "options": [ft.dropdown.Option(o) for o in options],
            "dense": ROW_DENSE,
            # Height is intentionally never set on the raw control here.
            # In clean mode raw control goes directly into the Row (height from parent layout + 60px frame).
            "width": width,
            "text_size": ROW_TEXT_SIZE,
            "content_padding": ROW_CONTENT_PADDING,
            "text_style": ROW_TEXT_STYLE,
        }

        params.update(overrides)
        ctrl = ft.Dropdown(**params)

        return ctrl

    def _make_row_textfield(width, hint_text=None, **overrides):
        """Create a styled TextField (used for the Amp ID column in amp rows).
        Shares the same padding/text style as _make_row_dropdown for consistent row height.
        In clean mode raw control goes directly into the Row (height from parent layout + 60px frame).
        """
        params = {
            "dense": ROW_DENSE,
            # Height is intentionally never set on the raw control here (same as Dropdown).
            # In clean mode raw control goes directly into the Row (height from parent layout + 60px frame).
            "width": width,
            "text_size": ROW_TEXT_SIZE,
            "content_padding": ROW_CONTENT_PADDING,
            "text_style": ROW_TEXT_STYLE,
        }
        if hint_text:
            params["hint_text"] = hint_text
        params.update(overrides)
        ctrl = ft.TextField(**params)

        return ctrl

    def _make_remove_button(on_click):
        """Create the small remove (X) icon button shown at the end of each dynamic row.
        Used by both _add_rack_row and _add_amp_row via a small closure wrapper.
        """
        return ft.IconButton(
            icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
            icon_size=26,
            width=40,
            height=40,
            padding=0,
            tooltip="Remove row",
            on_click=on_click,
        )

    def _make_row_frame(row_idx, row_content):
        """Wrap a row's inner content in a fixed-height slot (60px) with vertical centering.
        Plain production layout only.
        The inner Column(MAIN_CENTER) + row_content produces the gap above/below the field strip.

        row_content is a minimal horizontal-padding wrapper (auto-sizes to the Row of raw fields).
        The 60px frame + centering provides the visual slot and symmetric space above/below.
        """
        return ft.Container(
            content=ft.Column(
                [row_content],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                spacing=0,
            ),
            height=60,
        )

    def _make_debug_header(title, add_btn):
        """Header row for a multi-create section (title + the + add-row button). Plain clean version."""
        return ft.Container(
            content=ft.Row(
                [ft.Text(title, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK), add_btn],
                spacing=3,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=2,
        )

    def _make_labels_row(label_texts, widths):
        """Compact column header labels shown above the list of dynamic rows. Plain clean version."""
        texts = [ft.Text("", width=16)] + [
            ft.Text(txt, size=13, width=w, text_align=ft.TextAlign.CENTER, color=ft.Colors.BLACK)
            for txt, w in zip(label_texts, widths)
        ]
        return ft.Container(
            content=ft.Row(
                texts,
                spacing=1,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=2,
        )

    def _make_row_viewport(list_view):
        """Fixed-height scrollable viewport (ListView host) for the dynamic rows. Plain clean version."""
        return ft.Container(
            content=list_view,
            height=300,
            expand=False,
        )

    # Clean production layout only (debug scaffolding removed).

    # Declarative specs for the controls that appear in each dynamic row.
    # (key, "dropdown"|"textfield", options_label, width_px)
    # These drive the loops inside _add_rack_row and _add_amp_row using the _make_* factories.
    # Adding or reordering a column only requires touching the spec list + the row_ui Row + the row_data dict.
    RACK_ROW_SPECS = [
        ("loc", "dropdown", "Rack Location", 180),
        ("num", "dropdown", "Rack #", 120),
        ("template", "dropdown", "Template", 90),
        ("racktype", "dropdown", "Rack Type", 100),
    ]
    AMP_ROW_SPECS = [
        ("loc", "dropdown", "Rack Location", 180),
        ("num", "dropdown", "Rack #", 100),
        ("amp_num", "dropdown", "Amp #", 100),
        ("amp_type", "dropdown", "Amp Type", 85),
        ("amp_id", "textfield", None, 85),  # special hint + blur handling
    ]

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

    def _finish_create(created_items, on_created, page, count_label, finish_print):
        """Common save + post-create path used by _save for both multi-rack and multi-amp.
        - Converts items to DataFrame and calls save_to_db
        - Invokes the on_created callback (usually the sidebar refresh_list)
        - Triggers any registered inspector refresh callbacks (so Amp dropdowns etc. update)
        - Closes the dialog and does page.update()
        Returns True on success (used to early-return from the two branches in _save).
        """
        if created_items:
            df = pd.DataFrame([it.to_dict() for it in created_items])
            save_to_db(df, "input_data")
            print(f"Save successful: {len(created_items)} {count_label}")
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
            print(finish_print)
            return True
        return False

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

                _finish_create(created_items, on_created, page, "rack(s)", "=== CREATE MULTI-RACK SAVE FINISHED ===")
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

                _finish_create(created_items, on_created, page, "amp(s)", "=== CREATE MULTI-AMP SAVE FINISHED ===")
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

    # Legacy single-row form controls (still constructed for the original create flow but forced .visible=False
    # once we switched to the multi-row UI). Rack Location / Rack # are shared between racks and amps.
    loc_dd = ft.Dropdown(
        ref=location_ref,
        label="Rack Location",
        options=[ft.dropdown.Option(o) for o in get_options_for_field("Rack Location")],
        dense=FORM_DENSE,
        height=FORM_CONTROL_HEIGHT,
        content_padding=FORM_CONTENT_PADDING,
        text_style=FORM_TEXT_STYLE,
        label_style=ft.TextStyle(color=ft.Colors.BLACK, size=9),
        on_select=_update_rack_suggestion,
    )
    rack_dd = ft.Dropdown(
        ref=rack_num_ref,
        label="Rack #",
        options=[ft.dropdown.Option(o) for o in get_options_for_field("Rack #")],
        dense=FORM_DENSE,
        height=FORM_CONTROL_HEIGHT,
        content_padding=FORM_CONTENT_PADDING,
        text_style=FORM_TEXT_STYLE,
        label_style=ft.TextStyle(color=ft.Colors.BLACK, size=9),
        on_select=_update_rack_suggestion,
    )

    # Bootstrap initial free rack name suggestion (so first open for rack also avoids duplicates)
    _update_rack_suggestion()

    # Rack-only controls: Template + Rack Type (drive auto-fill) + the 16 hidden auto-fill fields.
    template_dd = ft.Dropdown(
        ref=template_ref,
        label="Template",
        options=[ft.dropdown.Option(o) for o in get_options_for_field("Template")],
        dense=FORM_DENSE,
        height=FORM_CONTROL_HEIGHT,
        content_padding=FORM_CONTENT_PADDING,
        text_style=FORM_TEXT_STYLE,
        label_style=ft.TextStyle(color=ft.Colors.BLACK, size=9),
        on_select=_auto_fill_from_template,
    )
    racktype_dd = ft.Dropdown(
        ref=rack_type_ref,
        label="Rack Type",
        options=[ft.dropdown.Option(o) for o in get_options_for_field("Rack Type")],
        dense=FORM_DENSE,
        height=FORM_CONTROL_HEIGHT,
        content_padding=FORM_CONTENT_PADDING,
        text_style=FORM_TEXT_STYLE,
        label_style=ft.TextStyle(color=ft.Colors.BLACK, size=9),
        on_select=_auto_fill_from_template,
    )

    # Taken rack names (shown to help user avoid duplicates such as two "SL2")
    taken_rack_names = get_taken_rack_names()
    taken_rack_text = ft.Text(
        f"Taken Rack names (never duplicate e.g. 2 SL2): {', '.join(sorted(taken_rack_names)) if taken_rack_names else 'none yet'}",
        size=10,
        italic=True,
        color=ft.Colors.BLACK,
    )

    rack_auto_ctrls = [
        ft.Dropdown(
            ref=auto_fill_field_refs[f],
            label=f,
            options=[ft.dropdown.Option(o) for o in get_options_for_field(f)],
            dense=FORM_DENSE,
            height=FORM_CONTROL_HEIGHT,
            content_padding=FORM_CONTENT_PADDING,
            text_style=FORM_TEXT_STYLE,
            label_style=ft.TextStyle(color=ft.Colors.BLACK, size=9),
        )
        for f in auto_fill_fields
    ]

    # Auto-fill fields are hidden (populated by template when Template+Rack Type chosen; values still captured on Create).
    for ctrl in rack_auto_ctrls:
        ctrl.visible = False

    # Amp-only initial controls. Only "Amp Type" + "Amp ID" shown at create time (per original spec).
    # The rest of amp_fields are still built (hidden) so their refs exist and values are captured on batch Create.
    # User completes the other fields later via the Inspector.
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
                dense=FORM_DENSE,
                height=FORM_CONTROL_HEIGHT,
                content_padding=FORM_CONTENT_PADDING,
                text_style=FORM_TEXT_STYLE,
                label_style=ft.TextStyle(color=ft.Colors.BLACK, size=9),
                visible=(f in amp_show_fields),
            )
        else:
            hint = "0.01-99.99 with 2 decimals (e.g. 1.00, 42.50)  (must be unique)" if f == "Amp ID" else None
            ctrl = ft.TextField(
                ref=ref,
                label=f,
                dense=FORM_DENSE,
                height=FORM_CONTROL_HEIGHT,
                hint_text=hint,
                content_padding=FORM_CONTENT_PADDING,
                text_style=FORM_TEXT_STYLE,
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

    # Taken Amp IDs (shown so the user can pick a free one and avoid duplicate-ID errors on create)
    taken_list = get_taken_amp_ids()
    taken_info = ft.Text(
        f"Taken Amp IDs (avoid these): {', '.join(taken_list) if taken_list else 'none yet'}",
        size=9,
        italic=True,
        color=ft.Colors.BLACK,
    )
    amp_ctrls.append(taken_info)

    # Multi-rack rows (Device Type = Rack). See RACK_ROW_SPECS + _add_rack_row for the implementation.
    rack_form_rows = []
    rack_rows_column = ft.ListView(controls=[], spacing=4, auto_scroll=True, expand=False)

    def _add_rack_row(e=None):
        """Add a new rack creation row."""
        row_idx = len(rack_form_rows) + 1

        # Build row using the declarative RACK_ROW_SPECS + shared _make_* factories.
        controls = {}
        for key, ctype, label, width in RACK_ROW_SPECS:
            controls[key] = _make_row_dropdown(get_options_for_field(label), width)
        row_loc = controls["loc"]
        row_num = controls["num"]
        row_t = controls["template"]
        row_rt = controls["racktype"]

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
                rack_form_rows.remove(rdata)
                if rdata.get("ui") in rack_rows_column.controls:
                    rack_rows_column.controls.remove(rdata["ui"])
                try:
                    rack_rows_column.update()
                    rack_rows_viewport.update()
                except Exception:
                    pass

        # Build row_data first (without ui), create rem_btn capturing it so remove works,
        # then build ui, set ui, append.
        row_data = {
            "loc_dd": row_loc,
            "num_dd": row_num,
            "template_dd": row_t,
            "racktype_dd": row_rt,
            "auto_values": row_auto_values,
            # "ui" set below
        }
        rem_btn = _make_remove_button(lambda e, rdata=row_data: _remove_row(e, rdata))

        # Visual versions for the Row (clean only).
        loc_ui = row_loc
        num_ui = row_num
        t_ui = row_t
        rt_ui = row_rt

        row_ui = ft.Row(
            [
                ft.Text(f"R{row_idx}", size=8, width=16, color=ft.Colors.BLACK),
                loc_ui,
                num_ui,
                t_ui,
                rt_ui,
                rem_btn,
            ],
            spacing=2,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        row_content = ft.Container(
            content=ft.Column(
                [row_ui],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                spacing=0,
            ),
            # This is now a minimal wrapper that only provides horizontal padding around the row of fields.
            # It auto-sizes to the natural height of row_ui (the Row containing the raw controls).
            # The outer row_wrapper (_make_row_frame, 60px in clean) + its Column(CENTER) provides
            # the visual slot and the space/gaps above and below the field strip.
            # Removed the previous fixed ROW_CONTENT_HEIGHT on this layer to reduce redundancy
            # and let the fields determine their own vertical space (addressing the "space top, none bottom" issue).
            # Only horizontal padding remains here.
            padding=ft.Padding.symmetric(horizontal=2, vertical=0),
        )

        row_wrapper = _make_row_frame(row_idx, row_content)

        row_data["ui"] = row_wrapper
        rack_form_rows.append(row_data)
        rack_rows_column.controls.append(row_wrapper)
        try:
            rack_rows_column.update()
            rack_rows_viewport.update()
        except Exception:
            pass

        _row_update_suggestion()

    add_row_btn = ft.IconButton(
        icon=ft.Icons.ADD_CIRCLE,
        icon_size=30,
        width=44,
        height=44,
        padding=0,
        tooltip="Add another rack row",
        on_click=lambda e: _add_rack_row(),
    )
    rack_header = _make_debug_header("Create multiple racks at once", add_row_btn)

    rack_labels_row = _make_labels_row(
        ["Loc", "#", "Template", "Rack Type"],
        [180, 120, 90, 100],
    )

    rack_rows_viewport = _make_row_viewport(rack_rows_column)
    rack_multi = ft.Column(
        [rack_labels_row, rack_rows_viewport, taken_rack_text],
        tight=True,
        spacing=2,
        visible=False,
    )

    # Multi-amp rows (Device Type = Amplifier). See AMP_ROW_SPECS + _add_amp_row.
    amp_form_rows = []
    amp_rows_column = ft.ListView(controls=[], spacing=4, auto_scroll=True, expand=False)

    def _add_amp_row(e=None):
        row_idx = len(amp_form_rows) + 1

        # Build row using the declarative AMP_ROW_SPECS + shared _make_* factories.
        controls = {}
        for key, ctype, label, width in AMP_ROW_SPECS:
            if ctype == "dropdown":
                controls[key] = _make_row_dropdown(get_options_for_field(label), width)
            else:
                controls[key] = _make_row_textfield(width, hint_text="e.g. 1.00 (unique)")
        row_loc = controls["loc"]
        row_num = controls["num"]
        row_amp_num = controls["amp_num"]
        row_amp_type = controls["amp_type"]
        row_amp_id = controls["amp_id"]

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
                amp_form_rows.remove(rdata)
                if rdata.get("ui") in amp_rows_column.controls:
                    amp_rows_column.controls.remove(rdata["ui"])
                try:
                    amp_rows_column.update()
                    amp_rows_viewport.update()
                except Exception:
                    pass

        # Build row_data first (without ui), create rem_btn capturing it so remove works,
        # then build ui, set ui, append.
        row_data = {
            "loc_dd": row_loc,
            "num_dd": row_num,
            "amp_num_dd": row_amp_num,
            "amp_type_dd": row_amp_type,
            "amp_id_tf": row_amp_id,
            "extra_amp_values": row_extra,
            # "ui" set below
        }
        rem_btn = _make_remove_button(lambda e, rdata=row_data: _remove_amp_row(e, rdata))

        # Visual versions for the Row (clean only).
        loc_ui = row_loc
        num_ui = row_num
        amp_num_ui = row_amp_num
        amp_type_ui = row_amp_type
        amp_id_ui = row_amp_id

        row_ui = ft.Row(
            [
                ft.Text(f"A{row_idx}", size=8, width=16, color=ft.Colors.BLACK),
                loc_ui,
                num_ui,
                amp_num_ui,
                amp_type_ui,
                amp_id_ui,
                rem_btn,
            ],
            spacing=2,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        row_content = ft.Container(
            content=ft.Column(
                [row_ui],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                spacing=0,
            ),
            # This is now a minimal wrapper that only provides horizontal padding around the row of fields.
            # It auto-sizes to the natural height of row_ui (the Row containing the raw controls).
            # The outer row_wrapper (_make_row_frame, 60px in clean) + its Column(CENTER) provides
            # the visual slot and the space/gaps above and below the field strip.
            # Removed the previous fixed ROW_CONTENT_HEIGHT on this layer to reduce redundancy
            # and let the fields determine their own vertical space (addressing the "space top, none bottom" issue).
            # Only horizontal padding remains here.
            padding=ft.Padding.symmetric(horizontal=2, vertical=0),
        )

        row_wrapper = _make_row_frame(row_idx, row_content)

        row_data["ui"] = row_wrapper
        amp_form_rows.append(row_data)
        amp_rows_column.controls.append(row_wrapper)
        try:
            amp_rows_column.update()
            amp_rows_viewport.update()
        except Exception:
            pass

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
        icon_size=30,
        width=44,
        height=44,
        padding=0,
        tooltip="Add another amp row",
        on_click=lambda e: _add_amp_row(),
    )
    amp_header = _make_debug_header("Create multiple amps at once", add_amp_btn)
    # reuse or recreate taken for amps
    taken_amp_text = ft.Text(
        f"Taken Amp IDs (avoid these): {', '.join(get_taken_amp_ids()) if get_taken_amp_ids() else 'none yet'}",
        size=10,
        italic=True,
        color=ft.Colors.BLACK,
    )

    amp_labels_row = _make_labels_row(
        ["Loc", "#", "Amp #", "Amp Type", "Amp ID"],
        [180, 100, 100, 85, 85],
    )

    amp_rows_viewport = _make_row_viewport(amp_rows_column)
    amp_multi = ft.Column(
        [amp_labels_row, amp_rows_viewport, taken_amp_text],
        tight=True,
        spacing=2,
        visible=False,
    )

    # Top right header container (will hold the active "Create multiple..." header on the right of device type row)
    top_right_header = ft.Container(alignment=ft.Alignment(1.0, 0.0))
    top_right_header.content = rack_header  # initial default (Rack)

    # Visibility groups toggled by Device Type (we now drive everything through rack_multi / amp_multi).
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
                _add_rack_row()
        else:
            if len(amp_form_rows) == 0:
                _add_amp_row()
            # prefill logic for amp id already in _add_amp_row

        # Let auto-fill run for rack (harmless for amp)
        try:
            _auto_fill_from_template()
            rack_multi.update()
            amp_multi.update()
        except Exception:
            pass

        # Always update the right-side header (in case previous updates failed)
        try:
            if is_rack:
                top_right_header.content = rack_header
            else:
                top_right_header.content = amp_header
            top_right_header.update()
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
        dense=FORM_DENSE,
        height=FORM_CONTROL_HEIGHT,
        content_padding=FORM_CONTENT_PADDING,
        text_style=ft.TextStyle(color=ft.Colors.BLACK, size=14),  # +2 on value text
        label_style=ft.TextStyle(color=ft.Colors.BLACK, size=11),  # +2 on "Device Type" label
        on_select=_switch_form,
    )

    # Top Device Type dropdown (clean only).
    device_type_ui = device_type_dd

    # Container for Device Type row, increased ~10px in height, with 2px padding at bottom to separate the divider.
    device_type_container = ft.Container(
        content=device_type_ui,
        # No fixed height to prevent clipping the dropdown's internal border/rendering.
        # Added vertical padding (~10px total) to give the device type row a bit more space,
        # with 2px bottom to separate from the following divider.
        alignment=ft.Alignment(0.0, 0.0),
        padding=ft.Padding.symmetric(vertical=5, horizontal=0),
    )

    # header on right of same row.
    top_bar = ft.Row([
        device_type_container,
        ft.Container(expand=True),
        top_right_header,
    ])
    divider = ft.Container(height=2, bgcolor=ft.Colors.GREY_400)

    dlg = ft.AlertDialog(
        title=ft.Text("Create New Device", color=ft.Colors.BLACK),
        content=ft.Container(
            width=780,
            bgcolor=ft.Colors.WHITE,
            content=ft.Column(
                [top_bar, divider, rack_multi, amp_multi],
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

    # Prime the form for the default device type (Rack) — this also adds the first dynamic row.
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
