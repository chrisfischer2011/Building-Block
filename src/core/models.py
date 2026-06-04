"""
Data models for the Building Block application.

This module defines the core domain models used across the UI and data layers.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional


@dataclass
class Device:
    """
    Represents a physical device in the system.

    Device Types:
        - "Rack"       → Container device. Has many signal/routing/patching fields.
        - "Amplifier"  → Child device that belongs inside a Rack.

    Relationship:
        - Amplifiers reference their parent Rack via `parent_id`.
        - For user-friendly display, Amplifiers also store "Amp Location" and "Amp Rack #"
          in properties (these help with filtered dropdowns during creation/editing).

    Type-specific fields are stored in `properties` for now. This gives us flexibility
    while we stabilize the exact schema.
    """

    id: Optional[int] = None
    name: str = ""
    device_type: str = ""           # "Rack" or "Amplifier"
    parent_id: Optional[int] = None # Points to a Rack's id when this is an Amplifier

    # Type-specific fields live here (e.g. "Rack #", "AES Input", "Ch A", etc.)
    properties: dict[str, Any] = field(default_factory=dict)

    notes: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary suitable for database storage."""
        import json
        return {
            "id": self.id,
            "name": self.name,
            "device_type": self.device_type,
            "parent_id": self.parent_id,
            "properties": json.dumps(self.properties) if self.properties else "{}",  # Store as JSON string
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Device":
        """Create a Device from a dictionary (from database or UI)."""
        import json

        def _clean(val, default=""):
            if val is None:
                return default
            if isinstance(val, float) and str(val) == "nan":
                return default
            return val

        props = data.get("properties") or {}
        if isinstance(props, str):
            try:
                props = json.loads(props)
            except Exception:
                props = {}

        return cls(
            id=data.get("id"),
            name=_clean(data.get("name"), ""),
            device_type=_clean(data.get("device_type"), ""),
            parent_id=data.get("parent_id"),
            properties=props if isinstance(props, dict) else {},
            notes=_clean(data.get("notes"), ""),
        )

    def __str__(self) -> str:
        return self.name or f"Unnamed {self.device_type or 'Device'}"


# Keep the old name as an alias during transition if needed
DataEntry = Device


# =============================================================================
# Known fields per device type
# These will be used to drive the Inspector forms dynamically.
# =============================================================================

RACK_FIELDS = [
    # === Initial Form Fields (shown first when creating a Rack) ===
    "Rack Location",
    "Rack #",
    "Template",
    "Rack Type",

    # === Auto-fillable from Template ===
    "Switch Config",
    "Off Ramp",
    "AES Input",
    "Analog Input",
    "Distro 1",
    "Distro 2",
    "Signal In",
    "Signal Thru",
    "Signal Out",
    "Signal Out 2",
    "Maps 1",
    "Maps 2",
    "Maps 3",
    "Maps 4",
    "Maps 5",
    "Maps 6",

    # === Amp Assignment Fields (populated when amplifiers are assigned) ===
    "Amp # 1",
    "Amp # 2",
    "Amp # 3",
    "Amp # 4",
    "Amp # 5",
    "Amp # 6",
    "Amp # 7",
    "Amp # 8",
    "Amp # 9",
    "Amp # 10",
    "Amp # 11",
    "Amp # 12",
    "Amp # 13",
    "Amp # 14",
    "Amp # 15",
    "Amp # 16",

    # === 1U Custom Fields ===
    "1u A",
    "1u B",
]

# Fields that should appear first / on the "Initial Form" when creating a Rack
CORE_RACK_FIELDS = [
    "Rack Location",
    "Rack #",
    "Template",
    "Rack Type",
]

AMPLIFIER_FIELDS = [
    "Rack Location",
    "Rack #",
    "Amp #",
    "Amp Type",
    "Amp ID",
    "Mode",
    "Ch A",
    "Ch B",
    "Ch C",
    "Ch D",
    "Hang A",
    "Hang B",
    "Hang C",
    "Hang D",
    "Output Patch",
    "ANA 1",
    "ANA 2",
    "ANA 3",
    "AES 1/2",
    "AES 3/4",
]

ALL_DEVICE_FIELDS = {
    "Rack": RACK_FIELDS,
    "Amplifier": AMPLIFIER_FIELDS,
}

# =============================================================================
# Field Options (Dropdown values)
# Most fields are dropdowns. We will populate these gradually.
# Structure: FIELD_NAME -> list of possible values
# =============================================================================

DEVICE_FIELD_OPTIONS: dict[str, list[str]] = {
    # Rack fields
    "Rack Type": ["224", "223", "117", "112", "112(AIS)"],
    "Template": ["D90", "D80"],                    # New - drives many auto-fill values
    "Switch Config": ["Primary Only", "Redundant"],
    "Off Ramp": ["", "None", "DS10", "DS20", "Other"],
    "AES Input": ["Off Ramp", "Signal In"],
    "Analog Input": ["Off Ramp", "Signal In"],
    "Distro 1": [
        "6u CAMLOCK Distro",
        "6u POWERLOCK Distro",
        "AIS Box",
        "L21-30 Maps",
        "32amp Cee-Form Maps",
    ],
    "Distro 2": [
        "6u CAMLOCK Distro",
        "6u POWERLOCK Distro",
        "AIS Box",
        "L21-30 Maps",
        "32amp Cee-Form Maps",
    ],
    "Signal In": ["NC14", "Ca-Com"],
    "Signal Thru": ["NC14", "Ca-Com"],
    "Signal Out": ["NC14", "Ca-Com"],
    "Signal Out 2": ["NC14", "Ca-Com"],
    "Maps 1": ["LK", "NL8", "NL4"],
    "Maps 2": ["LK", "NL8", "NL4"],
    "Maps 3": ["LK", "NL8", "NL4"],
    "Maps 4": ["LK", "NL8", "NL4"],
    "Maps 5": ["LK", "NL8", "NL4"],
    "Maps 6": ["LK", "NL8", "NL4"],

    # Amplifier fields
    "Amp Type": ["D90", "D80", "D40"],
    "Rack Location": ["Stage Right(SR)", "Stage Left(SL)", "Delay(DLY)"],
    "Rack #": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
    "Amp #": [
        "Amp # 1", "Amp # 2", "Amp # 3", "Amp # 4",
        "Amp # 5", "Amp # 6", "Amp # 7", "Amp # 8",
        "Amp # 9", "Amp # 10", "Amp # 11", "Amp # 12",
        "Amp # 13", "Amp # 14", "Amp # 15", "Amp # 16",
    ],
    "Mode": ["2-Way Active", "Dual Channel", "Mix Top/Sub"],
    "Output Patch": ["LK", "NL8", "NL4"],

    # Common / shared fields (free text unless options added later)
    "Ch A": [],
    "Ch B": [],
    "Ch C": [],
    "Ch D": [],
    "Hang A": [],
    "Hang B": [],
    "Hang C": [],
    "Hang D": [],
    "ANA 1": [],
    "ANA 2": [],
    "ANA 3": [],
    "AES 1/2": [],
    "AES 3/4": [],
}


def get_fields_for_device(device: Device | str) -> list[str]:
    """Returns the list of known fields for a given device type."""
    if isinstance(device, Device):
        device_type = device.device_type
    else:
        device_type = device

    return ALL_DEVICE_FIELDS.get(device_type, [])


def get_options_for_field(field_name: str) -> list[str]:
    """Returns the dropdown options for a specific field (if any are defined)."""
    return DEVICE_FIELD_OPTIONS.get(field_name, [])


def normalize_amp_id(value: str | float | int | None) -> str:
    """Normalize an Amp ID to always have exactly 2 decimal places.

    Examples:
        1      -> "1.00"
        1.1    -> "1.10"
        1.234  -> "1.23"
        "1.00" -> "1.00"
        "" or None or invalid -> original stripped (validation elsewhere will reject)
    """
    if value is None:
        return ""
    s = str(value).strip()
    if not s:
        return ""
    try:
        f = float(s)
        return f"{f:.2f}"
    except (ValueError, TypeError):
        return s


def get_rack_name(location: str, rack_number: str | int) -> str:
    """Compute the rack display name from location and rack number (e.g. 'SL2').

    Same logic as used in get_display_name for racks.
    """
    loc = location or ""
    num = str(rack_number or "").strip()
    import re
    m = re.search(r'\(([^)]+)\)', loc)
    pref = m.group(1) if m else "".join(c for c in loc if c.isupper())[:2] or "RACK"
    if num:
        return f"{pref}{num}"
    return pref or "Rack"


def get_display_name(device_type: str, properties: dict) -> str:
    """Compute the canonical display name for a device based on its type and key properties.

    This is used both at creation time and when "naming fields" are edited in the inspector
    so that the sidebar list and inspector header stay in sync with the data.
    Amp IDs are always normalized to 2 decimal places.
    """
    dtype = (device_type or "").lower()
    props = properties or {}

    if dtype == "rack":
        loc = props.get("Rack Location", "") or ""
        num = props.get("Rack #", "") or ""
        return get_rack_name(loc, num)

    elif dtype == "amplifier":
        amp_id = normalize_amp_id(props.get("Amp ID", ""))
        amp_type = str(props.get("Amp Type", "") or "").strip()
        if amp_id and amp_type:
            return f"{amp_id} {amp_type}"
        if amp_id:
            return amp_id
        if amp_type:
            return amp_type
        return "Amplifier"

    # Fallback
    return props.get("name", "") or f"Unnamed {device_type or 'Device'}"


# =============================================================================
# Rack Template Defaults
# Key = (Template, Rack Type)
# Value = dict of field -> default value
# =============================================================================

RACK_TEMPLATE_DEFAULTS = {
    # D90 Templates
    ("D90", "224"): {
        "Switch Config": "Redundant",
        "Off Ramp": "",
        "AES Input": "Signal In",
        "Analog Input": "Signal In",
        "Distro 1": "6u CAMLOCK Distro",
        "Distro 2": "",
        "Signal In": "NC14",
        "Signal Thru": "NC14",
        "Signal Out": "Ca-Com",
        "Signal Out 2": "",
        "Maps 1": "LK",
        "Maps 2": "LK",
        "Maps 3": "LK",
        "Maps 4": "LK",
        "Maps 5": "",
        "Maps 6": "",
        "Amp Slots": 16,
    },
    ("D90", "223"): {
        "Switch Config": "Redundant",
        "Off Ramp": "",
        "AES Input": "Signal In",
        "Analog Input": "Signal In",
        "Distro 1": "6u CAMLOCK Distro",
        "Distro 2": "",
        "Signal In": "NC14",
        "Signal Thru": "NC14",
        "Signal Out": "Ca-Com",
        "Signal Out 2": "",
        "Maps 1": "LK",
        "Maps 2": "LK",
        "Maps 3": "LK",
        "Maps 4": "LK",
        "Maps 5": "",
        "Maps 6": "",
        "Amp Slots": 16,
    },
    ("D90", "117"): {
        "Switch Config": "Redundant",
        "Off Ramp": "",
        "AES Input": "Signal In",
        "Analog Input": "Signal In",
        "Distro 1": "L21-30 Maps",
        "Distro 2": "L21-30 Maps",
        "Signal In": "Ca-Com",
        "Signal Thru": "Ca-Com",
        "Signal Out": "",
        "Signal Out 2": "",
        "Maps 1": "LK",
        "Maps 2": "LK",
        "Maps 3": "",
        "Maps 4": "",
        "Maps 5": "",
        "Maps 6": "",
        "Amp Slots": 6,
    },
    ("D90", "112"): {
        "Switch Config": "Redundant",
        "Off Ramp": "",
        "AES Input": "Signal In",
        "Analog Input": "Signal In",
        "Distro 1": "L21-30 Maps",
        "Distro 2": "",
        "Signal In": "Ca-Com",
        "Signal Thru": "Ca-Com",
        "Signal Out": "",
        "Signal Out 2": "",
        "Maps 1": "LK",
        "Maps 2": "",
        "Maps 3": "",
        "Maps 4": "",
        "Maps 5": "",
        "Maps 6": "",
        "Amp Slots": 4,
    },
    ("D90", "112(AIS)"): {
        "Switch Config": "Redundant",
        "Off Ramp": "",
        "AES Input": "Signal In",
        "Analog Input": "Signal In",
        "Distro 1": "AIS Box",
        "Distro 2": "",
        "Signal In": "Ca-Com",
        "Signal Thru": "Ca-Com",
        "Signal Out": "",
        "Signal Out 2": "",
        "Maps 1": "",
        "Maps 2": "",
        "Maps 3": "",
        "Maps 4": "",
        "Maps 5": "",
        "Maps 6": "",
        "Amp Slots": 4,
    },
    # D80 Templates
    ("D80", "224"): {
        "Switch Config": "Primary Only",
        "Off Ramp": "DS10",
        "AES Input": "Off Ramp",
        "Analog Input": "Signal In",
        "Distro 1": "6u CAMLOCK Distro",
        "Distro 2": "",
        "Signal In": "NC14",
        "Signal Thru": "NC14",
        "Signal Out": "Ca-Com",
        "Signal Out 2": "",
        "Maps 1": "LK",
        "Maps 2": "LK",
        "Maps 3": "LK",
        "Maps 4": "LK",
        "Maps 5": "",
        "Maps 6": "",
        "Amp Slots": 16,
    },
    ("D80", "223"): {
        "Switch Config": "Primary Only",
        "Off Ramp": "DS10",
        "AES Input": "Off Ramp",
        "Analog Input": "Signal In",
        "Distro 1": "6u CAMLOCK Distro",
        "Distro 2": "",
        "Signal In": "NC14",
        "Signal Thru": "NC14",
        "Signal Out": "Ca-Com",
        "Signal Out 2": "",
        "Maps 1": "LK",
        "Maps 2": "LK",
        "Maps 3": "LK",
        "Maps 4": "LK",
        "Maps 5": "",
        "Maps 6": "",
        "Amp Slots": 16,
    },
    ("D80", "117"): {
        "Switch Config": "Primary Only",
        "Off Ramp": "",
        "AES Input": "Signal In",
        "Analog Input": "Signal In",
        "Distro 1": "L21-30 Maps",
        "Distro 2": "L21-30 Maps",
        "Signal In": "Ca-Com",
        "Signal Thru": "Ca-Com",
        "Signal Out": "",
        "Signal Out 2": "",
        "Maps 1": "LK",
        "Maps 2": "LK",
        "Maps 3": "",
        "Maps 4": "",
        "Maps 5": "",
        "Maps 6": "",
        "Amp Slots": 6,
    },
    ("D80", "112"): {
        "Switch Config": "Primary Only",
        "Off Ramp": "",
        "AES Input": "Signal In",
        "Analog Input": "Signal In",
        "Distro 1": "L21-30 Maps",
        "Distro 2": "",
        "Signal In": "Ca-Com",
        "Signal Thru": "Ca-Com",
        "Signal Out": "",
        "Signal Out 2": "",
        "Maps 1": "LK",
        "Maps 2": "",
        "Maps 3": "",
        "Maps 4": "",
        "Maps 5": "",
        "Maps 6": "",
        "Amp Slots": 4,
    },
    ("D80", "112(AIS)"): {
        "Switch Config": "Primary Only",
        "Off Ramp": "",
        "AES Input": "Signal In",
        "Analog Input": "Signal In",
        "Distro 1": "AIS Box",
        "Distro 2": "",
        "Signal In": "Ca-Com",
        "Signal Thru": "Ca-Com",
        "Signal Out": "",
        "Signal Out 2": "",
        "Maps 1": "",
        "Maps 2": "",
        "Maps 3": "",
        "Maps 4": "",
        "Maps 5": "",
        "Maps 6": "",
        "Amp Slots": 4,
    },
}


def get_rack_template_defaults(template: str, rack_type: str) -> dict:
    """Returns the default values for a given Template + Rack Type combination."""
    return RACK_TEMPLATE_DEFAULTS.get((template, rack_type), {}).copy()


def get_rack_amp_slots(template: str, rack_type: str) -> int:
    """Return the number of amplifier slots (Amp # 1 .. N) for the given Template + Rack Type.
    Falls back to 16 if unknown combination. Used to dynamically limit the Amp Assignments
    shown/available for a rack, and to auto-clear excess slots when Template/Rack Type changes.
    """
    defaults = RACK_TEMPLATE_DEFAULTS.get((template or "", rack_type or ""), {})
    try:
        n = int(defaults.get("Amp Slots", 16))
        return max(1, min(16, n))
    except (ValueError, TypeError):
        return 16
