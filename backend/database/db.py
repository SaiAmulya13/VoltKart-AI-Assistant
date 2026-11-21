
import sqlite3

from backend.config import DATABASE_PATH, DATA_DIR


def get_connection():

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)

    connection.execute("PRAGMA foreign_keys = ON")

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    # Chats table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (

            chat_id TEXT PRIMARY KEY,

            title TEXT,

            created_at TEXT,

            updated_at TEXT
        )
    """)

    # Messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (

            message_id INTEGER PRIMARY KEY AUTOINCREMENT,

            chat_id TEXT,

            role TEXT,

            content TEXT,

            citations TEXT,

            created_at TEXT,

            FOREIGN KEY(chat_id)
            REFERENCES chats(chat_id)
        )
    """)

    # Uploaded files table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uploaded_files (

            file_id TEXT PRIMARY KEY,

            filename TEXT,

            stored_path TEXT,

            file_type TEXT,

            file_size INTEGER,

            uploaded_at TEXT
        )
    """)

    connection.commit()

    connection.close()

    print("Database initialized successfully!")
