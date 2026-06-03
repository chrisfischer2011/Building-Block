import sqlite3
import pandas as pd
import json
from pathlib import Path

from src.core.models import DataEntry, get_rack_name, normalize_amp_id

DB_PATH = Path("data/app_data.db")

def get_db_connection():
    """Create connection and ensure data folder exists"""
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_database():
    """Initialize tables and ensure schema is up to date for the new Device model."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS input_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                category TEXT,
                value REAL,
                notes TEXT
            )
        """)

        # Upgrade schema for new Device model (Phase 6)
        # Add missing columns if they don't exist
        existing_columns = [row[1] for row in conn.execute("PRAGMA table_info(input_data)").fetchall()]
        
        new_columns = {
            "name": "TEXT",
            "device_type": "TEXT",
            "parent_id": "INTEGER",
            "properties": "TEXT"   # Stored as JSON string
        }

        for col_name, col_type in new_columns.items():
            if col_name not in existing_columns:
                try:
                    conn.execute(f"ALTER TABLE input_data ADD COLUMN {col_name} {col_type}")
                    print(f"Added column '{col_name}' to input_data table.")
                except Exception as e:
                    print(f"Warning: Could not add column {col_name}: {e}")

        print("Database initialized successfully.")
        
        # Optional: Create a sample reference table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reference_data (
                id INTEGER PRIMARY KEY,
                name TEXT,
                type TEXT,
                default_value REAL
            )
        """)

def save_to_db(df: pd.DataFrame, table_name: str = "input_data"):
    """Save Pandas DataFrame to SQLite"""
    with get_db_connection() as conn:
        df.to_sql(table_name, conn, if_exists='append', index=False)

def load_from_db(table_name: str = "input_data") -> pd.DataFrame:
    """Load data into Pandas DataFrame"""
    with get_db_connection() as conn:
        return pd.read_sql(f"SELECT * FROM {table_name}", conn)


def overwrite_data(items: list, table_name: str = "input_data"):
    """Replace the entire table contents with the provided list of items.
    Each item should be a DataEntry (with to_dict) or a dict ready for to_sql.
    This is used to persist edits to existing records.
    """
    if not items:
        with get_db_connection() as conn:
            conn.execute(f"DELETE FROM {table_name}")
            conn.commit()
        return

    if hasattr(items[0], "to_dict"):
        rows = [it.to_dict() for it in items]
    else:
        rows = items

    df = pd.DataFrame(rows)
    with get_db_connection() as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.commit()


def clear_all_data(table_name: str = "input_data"):
    """Delete all rows from the working table (used by File > New).
    Preserves the table schema and any other tables.
    """
    with get_db_connection() as conn:
        conn.execute(f"DELETE FROM {table_name}")
        conn.commit()


def is_amp_id_taken(amp_id: str, exclude_id=None) -> bool:
    """Return True if the given amp_id is already used by any Amplifier
    (optionally excluding a specific device by its DB id, for edit self-check).
    Amp IDs are normalized to 2 decimal places for comparison.
    """
    if not amp_id:
        return False
    amp_id = normalize_amp_id(amp_id)
    try:
        df = load_from_db("input_data")
        for _, row in df.iterrows():
            if str(row.get("device_type", "")).lower() != "amplifier":
                continue
            row_id = row.get("id")
            if exclude_id is not None and row_id == exclude_id:
                continue
            props = row.get("properties") or "{}"
            if isinstance(props, str):
                try:
                    props = json.loads(props)
                except Exception:
                    props = {}
            existing = normalize_amp_id(props.get("Amp ID", ""))
            if existing == amp_id:
                return True
        return False
    except Exception as ex:
        print(f"is_amp_id_taken error: {ex}")
        return False  # fail open to avoid blocking on DB issues


def get_taken_amp_ids():
    """Return sorted list of currently used (normalized) Amp IDs."""
    taken = set()
    try:
        df = load_from_db("input_data")
        for _, row in df.iterrows():
            if str(row.get("device_type", "")).lower() != "amplifier":
                continue
            props = row.get("properties") or "{}"
            if isinstance(props, str):
                try:
                    props = json.loads(props)
                except Exception:
                    props = {}
            aid = normalize_amp_id(props.get("Amp ID", ""))
            if aid:
                taken.add(aid)
        return sorted(taken, key=lambda x: float(x))
    except Exception as ex:
        print(f"get_taken_amp_ids error: {ex}")
        return []


def get_next_free_amp_id(start=0.01, end=99.99, step=0.01):
    """Find and return the smallest available Amp ID (as 'X.XX' string) not currently taken."""
    taken = set(get_taken_amp_ids())
    i = int(start * 100)
    max_i = int(end * 100)
    while i <= max_i:
        candidate = f"{i / 100:.2f}"
        if candidate not in taken:
            return candidate
        i += int(step * 100)
    return f"{end:.2f}"  # last resort


def get_taken_rack_names():
    """Return set of existing rack names (e.g. 'SL2')."""
    taken = set()
    try:
        df = load_from_db("input_data")
        for _, row in df.iterrows():
            if str(row.get("device_type", "")).lower() != "rack":
                continue
            it = DataEntry.from_dict(row)
            if it and it.name:
                taken.add(it.name.strip())
        return taken
    except Exception as ex:
        print(f"get_taken_rack_names error: {ex}")
        return set()


def is_rack_name_taken(name: str, exclude_id=None) -> bool:
    """Return True if the rack name is already used (optionally excluding self by id)."""
    if not name:
        return False
    name = str(name).strip()
    try:
        df = load_from_db("input_data")
        for _, row in df.iterrows():
            if str(row.get("device_type", "")).lower() != "rack":
                continue
            row_id = row.get("id")
            if exclude_id is not None and row_id == exclude_id:
                continue
            it = DataEntry.from_dict(row)
            if it and it.name and it.name.strip() == name:
                return True
        return False
    except Exception as ex:
        print(f"is_rack_name_taken error: {ex}")
        return False
