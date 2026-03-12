"""
Couche d'abstraction pour la base de données.
Supporte SQLite (dev local) et PostgreSQL (production).
Le choix se fait automatiquement via DATABASE_URL.
"""

import sqlite3
from config import DATABASE_URL, IS_POSTGRES

if IS_POSTGRES:
    import psycopg2
    import psycopg2.extras


def get_connection():
    """Retourne une connexion à la base active."""
    if IS_POSTGRES:
        return psycopg2.connect(DATABASE_URL)
    else:
        db_path = DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn


def execute_query(query, params=None, fetch=False):
    """Exécute une requête SQL. Retourne une liste de dicts si fetch=True."""
    conn = get_connection()
    if IS_POSTGRES:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        cursor = conn.cursor()

    try:
        cursor.execute(query, params or ())
        if fetch:
            return [dict(row) for row in cursor.fetchall()]
        else:
            conn.commit()
            return None
    finally:
        cursor.close()
        conn.close()


def setup_tables():
    """Crée les tables si elles n'existent pas."""
    if IS_POSTGRES:
        execute_query("""
            CREATE TABLE IF NOT EXISTS items (
                id   INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)
        execute_query("""
            CREATE TABLE IF NOT EXISTS ah_prices (
                id             SERIAL PRIMARY KEY,
                item_id        INTEGER NOT NULL REFERENCES items(id),
                min_price_gold REAL    NOT NULL,
                timestamp      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    else:
        execute_query("""
            CREATE TABLE IF NOT EXISTS items (
                id   INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)
        execute_query("""
            CREATE TABLE IF NOT EXISTS ah_prices (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id        INTEGER NOT NULL,
                min_price_gold REAL    NOT NULL,
                timestamp      DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES items(id)
            )
        """)

    db_type = "PostgreSQL" if IS_POSTGRES else "SQLite"
    print(f"Tables initialisées ({db_type}).")


def upsert_item(item_id: int, name: str):
    if IS_POSTGRES:
        execute_query(
            "INSERT INTO items (id, name) VALUES (%s, %s) ON CONFLICT (id) DO UPDATE SET name = %s",
            (item_id, name, name),
        )
    else:
        execute_query(
            "INSERT OR REPLACE INTO items (id, name) VALUES (?, ?)",
            (item_id, name),
        )


def insert_price(item_id: int, price: float):
    if IS_POSTGRES:
        execute_query(
            "INSERT INTO ah_prices (item_id, min_price_gold) VALUES (%s, %s)",
            (item_id, price),
        )
    else:
        execute_query(
            "INSERT INTO ah_prices (item_id, min_price_gold) VALUES (?, ?)",
            (item_id, price),
        )


def get_items() -> list[dict]:
    return execute_query("SELECT id, name FROM items ORDER BY name", fetch=True)


def get_prices(item_id: int, limit: int = 20) -> list[dict]:
    if IS_POSTGRES:
        return execute_query(
            "SELECT timestamp, min_price_gold FROM ah_prices WHERE item_id = %s ORDER BY timestamp DESC LIMIT %s",
            (item_id, limit),
            fetch=True,
        )
    else:
        return execute_query(
            "SELECT timestamp, min_price_gold FROM ah_prices WHERE item_id = ? ORDER BY timestamp DESC LIMIT ?",
            (item_id, limit),
            fetch=True,
        )


def get_stats() -> dict:
    rows = execute_query("SELECT COUNT(*) as c FROM ah_prices", fetch=True)
    total_records = rows[0]["c"] if rows else 0

    rows = execute_query("SELECT COUNT(*) as c FROM items", fetch=True)
    total_items = rows[0]["c"] if rows else 0

    rows = execute_query("SELECT MAX(timestamp) as t FROM ah_prices", fetch=True)
    last_update = rows[0]["t"] if rows else None

    return {
        "total_records": total_records,
        "tracked_items": total_items,
        "last_update": str(last_update) if last_update else None,
    }
