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
def _build_112_visual(page: ft.Page, rack: DataEntry) -> ft.Container:
    """Build the 112 rack visualization using a strict unit-based grid for print accuracy.

    Grid rules (as specified):
    - Each of the 12 numbered rows (1-12) is 1 unit high.
    - 5 additional rows above the numbers (rows 1-5) for header info.
      - Row 1: "1/4 Page section--112 Rack"
      - Row 2: rack info line (name | template type | amp slots)
      - Rows 3-5: blank
    - Numbered rows start at grid row 6 (number "1" in row 6, "2" in row 7, ..., "12" in row 17).
    - Every row is 10 units wide.
    - Item sizes (h x w in units):
        Switch Primary=1x5, Switch Secondary=1x5
        Amp slots (the 4 positions)=2x10 each
        Distro 1=3x2, Maps 1=3x2, Maps 2=3x2
        Ethernet I/O Management=1x2 (two instances)
        Signal Thru=2x2, Signal In=2x2

    The left column shows the RU numbers 1-12 only next to the numbered rows.
    The overall visual is constrained (for 1/4 page section use).
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

    # Unit system (tuned so total ~ matches previous 1/4 page target size)
    UNIT_W = 38          # px per horizontal unit (10 units wide = 380 px content)
    UNIT_H = 28          # px per vertical unit (1 unit high row)
    LEFT_NUM_W = 30      # px for the RU number strip

    RACK_CONTENT_W = 10 * UNIT_W
    HEADER_H = 5 * UNIT_H
    RACK_FACE_H = 12 * UNIT_H   # the 12 numbered rows

    BROWN = ft.Colors.BROWN_600
    RED = ft.Colors.RED
    YELLOW = ft.Colors.YELLOW
    YELLOW_DIM = ft.Colors.YELLOW_200
    LIGHT_BLUE = ft.Colors.CYAN_100
    BLACK = ft.Colors.BLACK
    DARK = ft.Colors.GREY_900

    # Helper to get assigned amp display for a slot
    def _get_amp_display(slot_key: str) -> str:
        val = _get_rack_prop(rack, slot_key)
        if not val:
            return "—"
        dev = amp_lookup.get(val)
        if dev:
            at = (dev.properties or {}).get("Amp Type", "")
            return f"{val} {at}".strip() if at else val
        return val

    # === Header rows 1-5 (full width above the numbered rack) ===
    header_rows = []
    # Row 1
    header_rows.append(
        ft.Container(
            height=UNIT_H,
            width=RACK_CONTENT_W,
            bgcolor=DARK,
            content=ft.Text(
                "1/4 Page section--112 Rack",
                size=11,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
                text_align=ft.TextAlign.CENTER,
            ),
            alignment=ft.Alignment.CENTER,
        )
    )
    # Row 2
    info_line = f"{rack_name}|{template} {rack_type}| {n_slots} amp slots"
    header_rows.append(
        ft.Container(
            height=UNIT_H,
            width=RACK_CONTENT_W,
            bgcolor=DARK,
            content=ft.Text(
                info_line,
                size=9,
                color=ft.Colors.WHITE70,
                text_align=ft.TextAlign.CENTER,
            ),
            alignment=ft.Alignment.CENTER,
        )
    )
    # Rows 3-5 blank
    for _ in range(3):
        header_rows.append(
            ft.Container(height=UNIT_H, width=RACK_CONTENT_W, bgcolor=BLACK)
        )

    header = ft.Container(
        width=LEFT_NUM_W + RACK_CONTENT_W,
        height=HEADER_H,
        content=ft.Column(header_rows, spacing=0),
        padding=ft.Padding.only(left=LEFT_NUM_W),  # align text with rack content
    )

    # === Numbered rows 6-17 (numbers 1-12 on left, 10-unit content on right) ===
    # Content row 0 = number "1", content row 11 = number "12"
    num_labels = []
    for i in range(1, 13):
        num_labels.append(
            ft.Container(
                height=UNIT_H,
                width=LEFT_NUM_W,
                bgcolor=ft.Colors.YELLOW_200,
                content=ft.Text(
                    str(i),
                    size=9,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLACK,
                    text_align=ft.TextAlign.CENTER,
                ),
                alignment=ft.Alignment.CENTER,
            )
        )
    left_numbers = ft.Column(num_labels, spacing=0, tight=True)

    # Build the 12-row rack content using Stack for precise unit positioning
    # content rows 0-11
    stack_children = []

    # Full black background for the amp/switch area
    stack_children.append(
        ft.Container(
            left=0,
            top=0,
            width=RACK_CONTENT_W,
            height=RACK_FACE_H,
            bgcolor=BLACK,
        )
    )

    # Row 0 (number 1): Switches - 1x5 each
    # Switch Primary (cols 0-4)
    switch_val = _get_rack_prop(rack, "Switch Config", "—")
    stack_children.append(
        ft.Container(
            left=0,
            top=0 * UNIT_H,
            width=5 * UNIT_W,
            height=1 * UNIT_H,
            bgcolor=BROWN,
            content=ft.Column(
                [
                    ft.Text("SWITCH PRIMARY", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, size=9),
                    ft.Text(switch_val, color=ft.Colors.WHITE70, size=7),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=1,
            ),
            alignment=ft.Alignment.CENTER,
        )
    )
    # Switch Secondary (cols 5-9)
    stack_children.append(
        ft.Container(
            left=5 * UNIT_W,
            top=0 * UNIT_H,
            width=5 * UNIT_W,
            height=1 * UNIT_H,
            bgcolor=RED,
            content=ft.Column(
                [
                    ft.Text("SWITCH SECONDARY", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, size=9),
                    ft.Text("Redundant" if switch_val == "Redundant" else "—", color=ft.Colors.WHITE70, size=7),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=1,
            ),
            alignment=ft.Alignment.CENTER,
        )
    )

    # Amp slots - 2x10 each, placed in the 8 rows after the switch row (content rows 1-8)
    # Using the mapping from the reference (top position = AMP4 slot, etc.)
    amp_defs = [
        ("AMP4", "Amp # 4", 1),   # starts at content row 1
        ("AMP1", "Amp # 1", 3),
        ("AMP2", "Amp # 2", 5),
        ("AMP3", "Amp # 3", 7),
    ]
    for label, slot_key, start_row in amp_defs:
        val = _get_amp_display(slot_key)
        stack_children.append(
            ft.Container(
                left=0,
                top=start_row * UNIT_H,
                width=10 * UNIT_W,
                height=2 * UNIT_H,
                bgcolor=ft.Colors.GREY_800,
                border=ft.Border(
                    left=ft.BorderSide(width=1, color=ft.Colors.WHITE24),
                    top=ft.BorderSide(width=1, color=ft.Colors.WHITE24),
                    right=ft.BorderSide(width=1, color=ft.Colors.WHITE24),
                    bottom=ft.BorderSide(width=1, color=ft.Colors.WHITE24),
                ),
                content=ft.Column(
                    [
                        ft.Text(label, weight=ft.FontWeight.BOLD, color=YELLOW, size=11),
                        ft.Text(val, color=YELLOW_DIM, size=8),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=2,
                ),
                alignment=ft.Alignment.CENTER,
            )
        )

    # Bottom I/O - rows 9-11 (3 units high), cols as specified
    distro1_val = _get_rack_prop(rack, "Distro 1")
    maps2_val = _get_rack_prop(rack, "Maps 2")
    maps1_val = _get_rack_prop(rack, "Maps 1")
    signal_thru_val = _get_rack_prop(rack, "Signal Thru")
    signal_in_val = _get_rack_prop(rack, "Signal In")
    eth1_val = _get_rack_prop(rack, "Off Ramp") or "—"
    eth2_val = _get_rack_prop(rack, "AES Input") or "—"

    bottom_start = 9

    # Distro 1 (3x2) cols 0-1
    stack_children.append(
        ft.Container(
            left=0,
            top=bottom_start * UNIT_H,
            width=2 * UNIT_W,
            height=3 * UNIT_H,
            bgcolor=LIGHT_BLUE,
            content=ft.Column(
                [ft.Text("DISTRO 1", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK, size=8),
                 ft.Text(distro1_val or "—", color=ft.Colors.BLACK87, size=7)],
                alignment=ft.MainAxisAlignment.CENTER, spacing=2
            ),
            alignment=ft.Alignment.CENTER,
        )
    )
    # Maps 2 (3x2) cols 2-3
    stack_children.append(
        ft.Container(
            left=2 * UNIT_W,
            top=bottom_start * UNIT_H,
            width=2 * UNIT_W,
            height=3 * UNIT_H,
            bgcolor=LIGHT_BLUE,
            content=ft.Column(
                [ft.Text("MAPS 2", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK, size=8),
                 ft.Text(maps2_val or "—", color=ft.Colors.BLACK87, size=7)],
                alignment=ft.MainAxisAlignment.CENTER, spacing=2
            ),
            alignment=ft.Alignment.CENTER,
        )
    )
    # Maps 1 (3x2) cols 4-5
    stack_children.append(
        ft.Container(
            left=4 * UNIT_W,
            top=bottom_start * UNIT_H,
            width=2 * UNIT_W,
            height=3 * UNIT_H,
            bgcolor=LIGHT_BLUE,
            content=ft.Column(
                [ft.Text("MAPS 1", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK, size=8),
                 ft.Text(maps1_val or "—", color=ft.Colors.BLACK87, size=7)],
                alignment=ft.MainAxisAlignment.CENTER, spacing=2
            ),
            alignment=ft.Alignment.CENTER,
        )
    )

    # Right side cols 6-9
    # Row 9 (top of bottom 3): two Ethernet 1x2
    stack_children.append(
        ft.Container(
            left=6 * UNIT_W,
            top=bottom_start * UNIT_H,
            width=2 * UNIT_W,
            height=1 * UNIT_H,
            bgcolor=LIGHT_BLUE,
            content=ft.Text("ETHERNET I/O\nMANAGEMENT", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK, size=6, text_align=ft.TextAlign.CENTER),
            alignment=ft.Alignment.CENTER,
            padding=1,
        )
    )
    stack_children.append(
        ft.Container(
            left=8 * UNIT_W,
            top=bottom_start * UNIT_H,
            width=2 * UNIT_W,
            height=1 * UNIT_H,
            bgcolor=LIGHT_BLUE,
            content=ft.Text("ETHERNET I/O\nMANAGEMENT", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK, size=6, text_align=ft.TextAlign.CENTER),
            alignment=ft.Alignment.CENTER,
            padding=1,
        )
    )

    # Rows 10-11: Signal Thru 2x2 (cols 6-7) and Signal In 2x2 (cols 8-9)
    stack_children.append(
        ft.Container(
            left=6 * UNIT_W,
            top=(bottom_start + 1) * UNIT_H,
            width=2 * UNIT_W,
            height=2 * UNIT_H,
            bgcolor=LIGHT_BLUE,
            content=ft.Column(
                [ft.Text("SIGNAL THRU", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK, size=7),
                 ft.Text(signal_thru_val or "—", color=ft.Colors.BLACK87, size=6)],
                alignment=ft.MainAxisAlignment.CENTER, spacing=1
            ),
            alignment=ft.Alignment.CENTER,
        )
    )
    stack_children.append(
        ft.Container(
            left=8 * UNIT_W,
            top=(bottom_start + 1) * UNIT_H,
            width=2 * UNIT_W,
            height=2 * UNIT_H,
            bgcolor=LIGHT_BLUE,
            content=ft.Column(
                [ft.Text("SIGNAL IN", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK, size=7),
                 ft.Text(signal_in_val or "—", color=ft.Colors.BLACK87, size=6)],
                alignment=ft.MainAxisAlignment.CENTER, spacing=1
            ),
            alignment=ft.Alignment.CENTER,
        )
    )

    rack_content = ft.Container(
        width=RACK_CONTENT_W,
        height=RACK_FACE_H,
        content=ft.Stack(stack_children),
        bgcolor=BLACK,  # base for any uncovered areas
    )

    # Lower part: numbers + rack content
    lower = ft.Row(
        [left_numbers, rack_content],
        spacing=0,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )

    # === Final assembly inside the 1/4 page box ===
    face = ft.Column([header, lower], spacing=0, tight=True)

    # Keep overall size close to previous 1/4 page target for UI consistency
    box_w = LEFT_NUM_W + RACK_CONTENT_W + 10
    box_h = HEADER_H + RACK_FACE_H + 20

    return ft.Container(
        content=face,
        width=box_w,
        height=box_h,
        bgcolor=ft.Colors.GREY_800,
        border=ft.Border(
            left=ft.BorderSide(width=2, color=ft.Colors.GREY_400),
            top=ft.BorderSide(width=2, color=ft.Colors.GREY_400),
            right=ft.BorderSide(width=2, color=ft.Colors.GREY_400),
            bottom=ft.BorderSide(width=2, color=ft.Colors.GREY_400),
        ),
        border_radius=3,
        padding=4,
    )


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