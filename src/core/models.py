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
        return {
            "id": self.id,
            "name": self.name,
            "device_type": self.device_type,
            "parent_id": self.parent_id,
            "properties": self.properties,   # Will be stored as JSON in DB later
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Device":
        """Create a Device from a dictionary (from database or UI)."""
        props = data.get("properties") or {}
        if isinstance(props, str):
            import json
            try:
                props = json.loads(props)
            except Exception:
                props = {}

        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            device_type=data.get("device_type", ""),
            parent_id=data.get("parent_id"),
            properties=props,
            notes=data.get("notes", ""),
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
    "Rack Location",
    "Rack #",
    "Rack Type",
    "Switch Config",
    "Off Ramp",
    "AES Input",
    "Analog Input",
    "Distro 1",
    "Distro 2",
    "Maps 1",
    "Maps 2",
    "Maps 3",
    "Maps 4",
    "Maps 5",
    "Maps 6",
    "Signal In",
    "Signal Through",
    "Signal Out 1",
    "Signal Out 2",
]

AMPLIFIER_FIELDS = [
    "Amp Location",      # Physical location / which rack the amp is in
    "Amp Rack #",        # Which rack this amp belongs to (containment)
    "Amp #",             # Physical slot/position inside the rack
    "Amp ID",            # Global / Show-level identifier (different from Amp #)
    "Amp Type",
    "Ch A",
    "Ch B",
    "Ch C",
    "Ch D",
    "Hang C",
    "Hang A",
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
    "Switch Config": ["Pri Only", "Redundant"],
    "Off Ramp": ["", "None", "DS10", "DS20", "Other"],
    "AES Input": ["Off Ramp", "Signal In"],
    "Analog Input": ["Off Ramp", "Signal In"],
    "Distro 1": [
        "6u CAMLOCK Distro",
        "6u POWERLOCK Distro",
        "AIS Box",
        "L21-30 Maps",
        "32amp Cee Form Maps",
    ],
    "Distro 2": [
        "6u CAMLOCK Distro",
        "6u POWERLOCK Distro",
        "AIS Box",
        "L21-30 Maps",
        "32amp Cee Form Maps",
    ],
    "Maps 1": [],
    "Maps 2": [],
    "Maps 3": [],
    "Maps 4": [],
    "Maps 5": [],
    "Maps 6": [],
    "Signal In": [],
    "Signal Through": [],
    "Signal Out 1": [],
    "Signal Out 2": [],

    # Amplifier fields
    "Amp Type": ["D90", "D80", "D40"],
    "Amp Location": ["Stage Right(SR)", "Stage Left(SL)", "Delay(DLY)"],
    "Amp Rack #": [],          # This will be dynamically filtered based on Amp Location

    # Common / shared fields
    "Ch A": [],
    "Ch B": [],
    "Ch C": [],
    "Ch D": [],
    "Hang C": [],
    "Hang A": [],
    "Output Patch": [],
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
