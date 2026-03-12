"""
db.py — Couche d'abstraction Base de Données
==============================================
Supporte SQLite (développement local) et PostgreSQL (production cloud).
Détecte automatiquement le mode via DATABASE_URL.

Compétences démontrées : Design Pattern, Abstraction, SQL portable.
"""

import sqlite3
from config import DATABASE_URL, IS_POSTGRES

# PostgreSQL (si disponible)
if IS_POSTGRES:
    import psycopg2
    import psycopg2.extras


def get_connection():
    """
    Retourne une connexion à la base de données.
    Détecte automatiquement SQLite ou PostgreSQL.
    """
    if IS_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        db_path = DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn


def execute_query(query, params=None, fetch=False):
    """
    Exécute une requête SQL de manière portable.
    - fetch=False : INSERT/UPDATE/CREATE (commit automatique)
    - fetch=True  : SELECT (retourne une liste de dicts)
    """
    conn = get_connection()

    if IS_POSTGRES:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        cursor = conn.cursor()

    try:
        cursor.execute(query, params or ())

        if fetch:
            rows = cursor.fetchall()
            if IS_POSTGRES:
                # psycopg2 RealDictCursor retourne déjà des dicts
                return [dict(row) for row in rows]
            else:
                # sqlite3 Row → dict
                return [dict(row) for row in rows]
        else:
            conn.commit()
            return None
    finally:
        cursor.close()
        conn.close()


def setup_tables():
    """
    Crée les tables si elles n'existent pas.
    SQL compatible SQLite ET PostgreSQL.
    """
    if IS_POSTGRES:
        # PostgreSQL utilise SERIAL au lieu de AUTOINCREMENT
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
        # SQLite
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

    print(f"📁 Tables initialisées ({'PostgreSQL' if IS_POSTGRES else 'SQLite'}).")


def upsert_item(item_id: int, name: str):
    """Insère ou met à jour un objet dans le dictionnaire."""
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
    """Insère un relevé de prix."""
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
    """Retourne tous les objets surveillés."""
    return execute_query("SELECT id, name FROM items ORDER BY name", fetch=True)


def get_prices(item_id: int, limit: int = 20) -> list[dict]:
    """Retourne l'historique des prix d'un objet."""
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
    """Retourne les statistiques globales."""
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
