"""
Rack Visual Component

Bottom panel visualization for selected racks.
Initial implementation: faithful 112 / 112(AIS) faceplate style based on the
provided guideline, with these adaptations:
- Data comes from the live selected rack (DataEntry.properties) + live lookup
  of assigned Amplifier objects (no rack_components table).
- Middle amp RU count is dynamic (get_rack_amp_slots from the rack's Template + Rack Type).
- Special top switch row and bottom I/O row are hard-coded to match the desired 112 layout.
- Pure display for the first pass (GestureDetectors present but on_tap is a no-op).
- Only activates for Rack Type "112" or "112(AIS)"; otherwise the caller falls back.
"""

import flet as ft
from typing import Optional

from src.core.database import load_from_db
from src.core.models import DataEntry, get_rack_amp_slots, get_display_name
from src.ui.theme import CARD_CONTENT_PADDING, CARD_ELEVATION_LOW, CARD_MARGIN


def _build_amp_lookup() -> dict[str, DataEntry]:
    """Load all Amplifiers from DB and return a name -> Device lookup.
    Keys are the amp's .name and also its computed display name for robustness.
    """
    lookup: dict[str, DataEntry] = {}
    try:
        df = load_from_db("input_data")
        for _, row in df.iterrows():
            try:
                dev = DataEntry.from_dict(row)
                if not dev or (getattr(dev, "device_type", "") or "").lower() != "amplifier":
                    continue
                nm = (getattr(dev, "name", "") or "").strip()
                if nm:
                    lookup[nm] = dev
                # Also index under the canonical display name in case the slot stores that form
                try:
                    disp = get_display_name(dev.device_type, dev.properties or {})
                    if disp and disp != nm:
                        lookup[disp] = dev
                except Exception:
                    pass
            except Exception:
                continue
    except Exception:
        pass
    return lookup


def _get_rack_prop(rack: DataEntry, key: str, default: str = "") -> str:
    props = getattr(rack, "properties", {}) or {}
    if isinstance(props, str):
        try:
            import json
            props = json.loads(props)
        except Exception:
            props = {}
    val = props.get(key)
    return str(val).strip() if val is not None else default


def _build_112_visual(page: ft.Page, rack: DataEntry) -> ft.Container:
    """Build the 112 rack visualization to closely match the provided reference diagram,
    with overall size constrained to represent 1/4 of a printable page section.

    This makes the visual "print accurate" — the on-screen preview reflects the
    final proportions when these rack sections are laid out on paper (112 = 1/4 page).

    Layout (12 RU):
    - Left yellow RU scale 1-12.
    - RU1: SWITCH PRIMARY (brown) + SWITCH SECONDARY (red) full width bar.
    - RU2-9: Black bay with 4 amp positions (text labels only, yellow on black) at specific
      vertical locations matching the reference: top=AMP4 (uses "Amp # 4" data), then AMP1
      ("Amp # 1"), AMP2 ("Amp # 2"), AMP3 ("Amp # 3").
    - RU10-12: Light blue bottom section with exact blocks from the diagram:
        Left (tall): DISTRO 1 | MAPS 2 | MAPS 1
        Right upper: two "ETHERNET I/O MANAGEMENT"
        Right lower: SIGNAL THRU | SIGNAL IN
    Values are populated live from the rack properties + amp lookups.
    The entire returned control has explicit width/height limits (no expand).
    """
    amp_lookup = _build_amp_lookup()
    rack_props = getattr(rack, "properties", {}) or {}
    if isinstance(rack_props, str):
        try:
            import json
            rack_props = json.loads(rack_props)
        except Exception:
            rack_props = {}

    rack_name = getattr(rack, "name", "") or "Rack"
    template = _get_rack_prop(rack, "Template")
    rack_type = _get_rack_prop(rack, "Rack Type")
    n_slots = get_rack_amp_slots(template, rack_type)

    # =====================================================================
    # Print-accurate sizing: 112 rack visual = 1/4 of the printable page
    # These fixed limits ensure the preview in the app matches how it will
    # appear when the racks are printed as sections on a page (e.g. 2x2 layout).
    # Width/height chosen so the 12RU + I/O layout is proportionally correct
    # and does not grow/shrink to fill arbitrary UI space.
    # =====================================================================
    TARGET_WIDTH = 420   # 1/4 page width in preview pixels
    TARGET_HEIGHT = 510  # 1/4 page height in preview pixels (includes title + frame)

    # Compute RU height so the 12 logical rows (1 switch + 8 black bay + 3 bottom)
    # exactly fill the target printable section height.
    TITLE_HEIGHT = 20
    OUTER_FRAME = 10
    available_for_rack = TARGET_HEIGHT - TITLE_HEIGHT - OUTER_FRAME
    RU_HEIGHT = available_for_rack / 12   # ~39-40 px per RU for accurate print scale

    # Colors matching the reference image
    BROWN_PRIMARY = ft.Colors.BROWN_600
    RED_SECONDARY = ft.Colors.RED
    AMP_TEXT_COLOR = ft.Colors.YELLOW
    AMP_TEXT_SECONDARY = ft.Colors.YELLOW_200
    BOTTOM_BG = ft.Colors.CYAN_100  # light blue/cyan for bottom section
    RU_LABEL_BG = ft.Colors.YELLOW_200

    # === Left RU scale (yellow 1-12 aligned to each row) ===
    ru_labels = []
    for ru in range(1, 13):
        ru_labels.append(
            ft.Container(
                content=ft.Text(
                    str(ru),
                    size=10,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLACK,
                    text_align=ft.TextAlign.CENTER,
                ),
                width=24,
                height=RU_HEIGHT,
                bgcolor=RU_LABEL_BG,
                alignment=ft.Alignment.CENTER,
                border=ft.Border(
                    right=ft.BorderSide(width=1, color=ft.Colors.BLACK26),
                ),
            )
        )
    left_scale = ft.Column(ru_labels, spacing=0, tight=True)

    # === Switch row (RU 1) - brown left + red right ===
    switch_primary_val = _get_rack_prop(rack, "Switch Config", "—")
    switch_row = ft.Container(
        height=RU_HEIGHT,
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("SWITCH PRIMARY", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, size=10),
                            ft.Text(switch_primary_val, color=ft.Colors.WHITE70, size=8),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=1,
                    ),
                    bgcolor=BROWN_PRIMARY,
                    expand=2,
                    padding=ft.Padding.symmetric(horizontal=5, vertical=1),
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("SWITCH SECONDARY", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, size=10),
                            ft.Text("Redundant" if switch_primary_val == "Redundant" else "—", color=ft.Colors.WHITE70, size=8),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=1,
                    ),
                    bgcolor=RED_SECONDARY,
                    expand=3,
                    padding=ft.Padding.symmetric(horizontal=5, vertical=1),
                    alignment=ft.Alignment.CENTER,
                ),
            ],
            spacing=0,
        ),
        bgcolor=ft.Colors.BLACK,
    )

    # === Amp labels for the 4 fixed visual positions (order & placement from the PNG) ===
    def _make_amp_label(label: str, slot_key: str) -> ft.Container:
        assigned = _get_rack_prop(rack, slot_key)
        value_text = assigned or "—"
        if assigned:
            amp_dev = amp_lookup.get(assigned)
            if amp_dev:
                atype = (amp_dev.properties or {}).get("Amp Type", "")
                if atype:
                    value_text = f"{assigned} {atype}"
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(label, weight=ft.FontWeight.BOLD, color=AMP_TEXT_COLOR, size=12),
                    ft.Text(value_text, color=AMP_TEXT_SECONDARY, size=8),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=1,
            ),
            alignment=ft.Alignment.CENTER,
        )

    # Black middle bay (RU 2-9). Amps placed with spacers to match the reference PNG spacing.
    middle_height = 8 * RU_HEIGHT
    middle_bay = ft.Container(
        height=middle_height,
        bgcolor=ft.Colors.BLACK,
        content=ft.Column(
            [
                ft.Container(height=RU_HEIGHT * 0.35, bgcolor=ft.Colors.BLACK),
                _make_amp_label("AMP4", "Amp # 4"),
                ft.Container(height=RU_HEIGHT * 1.15, bgcolor=ft.Colors.BLACK),
                _make_amp_label("AMP1", "Amp # 1"),
                ft.Container(height=RU_HEIGHT * 0.95, bgcolor=ft.Colors.BLACK),
                _make_amp_label("AMP2", "Amp # 2"),
                ft.Container(height=RU_HEIGHT * 0.95, bgcolor=ft.Colors.BLACK),
                _make_amp_label("AMP3", "Amp # 3"),
                ft.Container(height=RU_HEIGHT * 0.55, bgcolor=ft.Colors.BLACK),
            ],
            spacing=0,
            alignment=ft.MainAxisAlignment.START,
        ),
        alignment=ft.Alignment.CENTER,
    )

    # === Bottom section (RU 10-12) - exact layout from the PNG ===
    bottom_height = 3 * RU_HEIGHT

    def _make_tall_block(label: str, val: str) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(label, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK, size=10, text_align=ft.TextAlign.CENTER),
                    ft.Text(val or "—", color=ft.Colors.BLACK87, size=8, text_align=ft.TextAlign.CENTER),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=2,
            ),
            bgcolor=BOTTOM_BG,
            expand=1,
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.symmetric(horizontal=2, vertical=3),
        )

    def _make_small_block(label: str, val: str) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(label, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK, size=7, text_align=ft.TextAlign.CENTER),
                    ft.Text(val or "—", color=ft.Colors.BLACK87, size=7, text_align=ft.TextAlign.CENTER),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=1,
            ),
            bgcolor=BOTTOM_BG,
            expand=1,
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.symmetric(horizontal=1, vertical=1),
        )

    distro1_val = _get_rack_prop(rack, "Distro 1")
    maps2_val = _get_rack_prop(rack, "Maps 2")
    maps1_val = _get_rack_prop(rack, "Maps 1")
    signal_thru_val = _get_rack_prop(rack, "Signal Thru")
    signal_in_val = _get_rack_prop(rack, "Signal In")
    eth1_val = _get_rack_prop(rack, "Off Ramp")
    eth2_val = _get_rack_prop(rack, "AES Input")

    right_split = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        _make_small_block("ETHERNET I/O\nMANAGEMENT", eth1_val),
                        _make_small_block("ETHERNET I/O\nMANAGEMENT", eth2_val),
                    ],
                    expand=True,
                    spacing=1,
                ),
                ft.Row(
                    [
                        _make_small_block("SIGNAL THRU", signal_thru_val),
                        _make_small_block("SIGNAL IN", signal_in_val),
                    ],
                    expand=True,
                    spacing=1,
                ),
            ],
            spacing=1,
            expand=True,
        ),
        expand=1,
    )

    bottom_section = ft.Container(
        height=bottom_height,
        content=ft.Row(
            [
                _make_tall_block("DISTRO 1", distro1_val),
                _make_tall_block("MAPS 2", maps2_val),
                _make_tall_block("MAPS 1", maps1_val),
                right_split,
            ],
            spacing=1,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        ),
        bgcolor=ft.Colors.BLACK,
    )

    # === Main face content (scale + visual rows) ===
    face_content = ft.Column(
        [
            switch_row,
            middle_bay,
            bottom_section,
        ],
        spacing=0,
        tight=True,
    )

    # The rack face with left scale. Constrain its width to leave room inside the 1/4 page box.
    face_width = TARGET_WIDTH - 18
    face_row = ft.Row(
        [left_scale, face_content],
        spacing=1,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )
    framed_face = ft.Container(
        content=face_row,
        width=face_width,
        bgcolor=ft.Colors.BLACK,
        padding=ft.Padding.only(left=1, right=1, top=1, bottom=1),
        border=ft.Border(
            left=ft.BorderSide(width=1, color=ft.Colors.GREY_500),
            right=ft.BorderSide(width=1, color=ft.Colors.GREY_500),
            top=ft.BorderSide(width=1, color=ft.Colors.GREY_500),
            bottom=ft.BorderSide(width=1, color=ft.Colors.GREY_500),
        ),
    )

    # === Final 1/4 page section preview box ===
    # Explicit size + frame so it visually represents exactly 1/4 of the printable page.
    # This is the "limit" the user requested for visual accuracy in print layout.
    preview_box = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "1/4 PAGE SECTION — 112 RACK",
                    size=10,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                ),
                ft.Text(
                    f"{rack_name}  |  {template} {rack_type}  |  {n_slots} amp slots",
                    size=8,
                    color=ft.Colors.WHITE70,
                ),
                framed_face,
            ],
            spacing=3,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=TARGET_WIDTH,
        height=TARGET_HEIGHT,
        bgcolor=ft.Colors.with_opacity(0.95, ft.Colors.GREY_800),
        border=ft.Border(
            left=ft.BorderSide(width=2, color=ft.Colors.GREY_400),
            top=ft.BorderSide(width=2, color=ft.Colors.GREY_400),
            right=ft.BorderSide(width=2, color=ft.Colors.GREY_400),
            bottom=ft.BorderSide(width=2, color=ft.Colors.GREY_400),
        ),
        border_radius=3,
        padding=ft.Padding.symmetric(horizontal=4, vertical=3),
    )

    return preview_box


def create_rack_visual_panel(page: ft.Page, app_state) -> ft.Card:
    """Creates the bottom visual panel.

    It registers itself so AppState.clear() (File > New) and selection changes
    can force a rebuild. When the selected item is a Rack with Rack Type 112 or
    112(AIS) it shows the stylized faceplate; otherwise it shows a compact
    placeholder (caller in main_layout may also fall back to the legacy main_content).
    """
    color_scheme = page.theme.color_scheme
    visual_wrapper = ft.Container(expand=True)

    def _rebuild_visual():
        """Rebuild the visual content based on current app_state.selected_item."""
        item = getattr(app_state, "selected_item", None)
        is_rack = bool(item) and (getattr(item, "device_type", "") or "").lower() == "rack"
        rack_type = ""
        if is_rack:
            props = getattr(item, "properties", {}) or {}
            if isinstance(props, str):
                try:
                    import json
                    props = json.loads(props)
                except Exception:
                    props = {}
            rack_type = (props.get("Rack Type") or "").strip()

        is_112 = rack_type in ("112", "112(AIS)")

        if is_rack and is_112:
            try:
                content = _build_112_visual(page, item)
            except Exception as ex:
                print(f"[RackVisual] Failed to build 112 visual: {ex}")
                content = ft.Container(
                    content=ft.Text("Error rendering rack visual", color=ft.Colors.RED),
                    padding=20,
                )
        else:
            # Placeholder when nothing selected or not a qualifying 112 rack.
            # We keep it minimal so the legacy main_content fallback (used by caller) can still be chosen.
            content = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.VIEW_IN_AR, size=36, color=color_scheme.on_tertiary_container),
                        ft.Text(
                            "112 Rack Visualization",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=color_scheme.on_tertiary_container,
                        ),
                        ft.Text(
                            "Select a Rack with Rack Type '112' or '112(AIS)' to see the layout.",
                            size=11,
                            color=color_scheme.on_tertiary_container,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                alignment=ft.Alignment.CENTER,
                padding=ft.Padding.only(top=20, bottom=20),
            )

        visual_wrapper.content = content
        try:
            visual_wrapper.update()
        except Exception:
            pass

    # Initial build
    _rebuild_visual()

    # Register so global File > New / clear can reset us to the placeholder.
    if hasattr(app_state, "register_visual_refresh"):
        app_state.register_visual_refresh(_rebuild_visual)

    return ft.Card(
        content=ft.Container(
            content=visual_wrapper,
            padding=CARD_CONTENT_PADDING,
            # No expand=True — the 112 visual inside is now explicitly sized
            # to 1/4 printable page (see _build_112_visual TARGET_WIDTH/HEIGHT).
            # This keeps the preview proportionally accurate for future printing
            # instead of stretching to fill the bottom panel.
        ),
        bgcolor=color_scheme.tertiary_container,
        elevation=CARD_ELEVATION_LOW,
        margin=CARD_MARGIN,
        # The card will size itself to the fixed preview box when a 112 rack is selected.
    )