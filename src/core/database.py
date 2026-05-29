import sqlite3
import pandas as pd
from pathlib import Path

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


def clear_all_data(table_name: str = "input_data"):
    """Delete all rows from the working table (used by File > New).
    Preserves the table schema and any other tables.
    """
    with get_db_connection() as conn:
        conn.execute(f"DELETE FROM {table_name}")
        conn.commit()