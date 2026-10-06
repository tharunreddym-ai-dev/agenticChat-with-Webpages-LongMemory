import sqlite3


def get_connection(path):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def create_table(path):
    connection = get_connection(path)
    try:
        cursor = connection.cursor()

        cursor.execute("""
                CREATE TABLE IF NOT EXISTS sets(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
                )
        """)

        cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                set_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user','assistant')),
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (set_id) REFERENCES sets(id)
                )
        """)

        cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_bases(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                set_id INTEGER NOT NULL,
                url_name TEXT NOT NULL,
                source_url TEXT NOT NULL,
                chunk_count INTEGER NOT NULL,
                uploaded_at TEXT NOT NULL,
                FOREIGN KEY (set_id) REFERENCES sets(id)
                )
        """)

        connection.commit()
    finally:
        connection.close()
