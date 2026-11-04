import sqlite3
from contextlib import contextmanager
from .config import DB_PATH

@contextmanager
def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()

def init_db():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS farmers (
            phone TEXT PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY, farmer_phone TEXT NOT NULL, kind TEXT NOT NULL,
            text TEXT, media_id TEXT, status TEXT DEFAULT 'received',
            error TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT, farmer_phone TEXT NOT NULL,
            payload TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'draft',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS conversations (
            farmer_phone TEXT PRIMARY KEY, payload TEXT NOT NULL DEFAULT '{}',
            history TEXT NOT NULL DEFAULT '[]',
            awaiting_confirmation INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS conversation_turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_phone TEXT NOT NULL, message_id TEXT NOT NULL,
            role TEXT NOT NULL, text TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(message_id, role)
        );
        CREATE INDEX IF NOT EXISTS conversation_turns_phone
            ON conversation_turns(farmer_phone, id);
        CREATE TABLE IF NOT EXISTS machines (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            machine_type TEXT NOT NULL, location TEXT, hourly_rate REAL,
            available INTEGER NOT NULL DEFAULT 1,
            owner_type TEXT NOT NULL DEFAULT 'company',
            reserved_for_own_use INTEGER NOT NULL DEFAULT 0,
            available_from TEXT, available_to TEXT,
            compatibility_notes TEXT
        );
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT, request_id INTEGER NOT NULL,
            machine_id INTEGER NOT NULL, start_at TEXT, end_at TEXT,
            status TEXT NOT NULL DEFAULT 'proposed'
        );
        """)
        machine_columns = {row['name'] for row in con.execute('PRAGMA table_info(machines)')}
        migrations = (
            ('owner_type', "TEXT NOT NULL DEFAULT 'company'"),
            ('reserved_for_own_use', 'INTEGER NOT NULL DEFAULT 0'),
            ('available_from', 'TEXT'),
            ('available_to', 'TEXT'),
            ('compatibility_notes', 'TEXT'),
        )
        for name, definition in migrations:
            if name not in machine_columns:
                con.execute(f'ALTER TABLE machines ADD COLUMN {name} {definition}')
