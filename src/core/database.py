import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("data/app_data.db")

def get_db_connection():
    """Create connection and ensure data folder exists"""
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_database():
    """Initialize tables"""
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
        print("✅ Database initialized successfully.")
        
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