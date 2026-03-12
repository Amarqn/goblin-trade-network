"""
Script de test pour le WoW Token.
Récupère le prix actuel du Jeton WoW et le sauvegarde
dans une base SQLite locale.
"""

import requests
import sqlite3
from config import BLIZZARD_CLIENT_ID, BLIZZARD_CLIENT_SECRET, validate_config


def setup_database():
    conn = sqlite3.connect("wow_economy.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS token_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            price_gold INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_price(price_gold):
    conn = sqlite3.connect("wow_economy.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO token_prices (price_gold) VALUES (?)", (price_gold,))
    conn.commit()
    conn.close()


def show_history():
    conn = sqlite3.connect("wow_economy.db")
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, price_gold FROM token_prices ORDER BY timestamp DESC")
    rows = cursor.fetchall()

    print("\nHistorique des prix :")
    for date, price in rows:
        print(f"  [{date}] {price:,} PO".replace(",", " "))
    conn.close()


def get_token():
    resp = requests.post(
        "https://oauth.battle.net/token",
        data={"grant_type": "client_credentials"},
        auth=(BLIZZARD_CLIENT_ID, BLIZZARD_CLIENT_SECRET),
    )
    if resp.status_code == 200:
        return resp.json()["access_token"]
    return None


def get_wow_token_price(access_token):
    resp = requests.get(
        "https://eu.api.blizzard.com/data/wow/token/index",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"namespace": "dynamic-eu", "locale": "fr_FR"},
    )
    if resp.status_code == 200:
        return resp.json()["price"] / 10000
    return None


if __name__ == "__main__":
    validate_config()
    setup_database()

    token = get_token()
    if token:
        price = get_wow_token_price(token)
        if price:
            print(f"Prix actuel du Jeton WoW : {price:,.0f} PO".replace(",", " "))
            save_price(price)
            show_history()
