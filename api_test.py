import requests
import sqlite3
from datetime import datetime

# --- VOS CLÉS BLIZZARD ---
CLIENT_ID = "eb78f80c9496414ab1bab42b090afc52"
CLIENT_SECRET = "Ibt8O2w7TankTxjqvqw1rKigYo6WkBmo"

# --- PARTIE 1 : LA BASE DE DONNÉES ---
def setup_database():
    """
    Crée le coffre-fort (le fichier wow_economy.db) et la table SQL si elle n'existe pas.
    """
    # Se connecte au fichier (ou le crée s'il n'existe pas)
    conn = sqlite3.connect("wow_economy.db")
    cursor = conn.cursor()
    
    # Création de la table avec 3 colonnes : un ID unique, le prix, et la date exacte
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS token_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            price_gold INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("📁 Banque de Guilde (Base de données) prête !")

def save_price_to_db(price_gold):
    """
    Sauvegarde le prix dans la base de données.
    """
    conn = sqlite3.connect("wow_economy.db")
    cursor = conn.cursor()
    
    # On insère une nouvelle ligne dans notre tableau
    cursor.execute("INSERT INTO token_prices (price_gold) VALUES (?)", (price_gold,))
    conn.commit()
    conn.close()
    print("💾 Prix archivé dans la base de données avec succès.")

def show_price_history():
    """
    Lit et affiche tout l'historique des prix sauvegardés.
    """
    conn = sqlite3.connect("wow_economy.db")
    cursor = conn.cursor()
    
    # On demande à SQL de nous donner tout l'historique
    cursor.execute("SELECT timestamp, price_gold FROM token_prices ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    
    print("\n📜 --- HISTORIQUE DES PRIX ---")
    for row in rows:
        date_heure = row[0]
        prix = row[1]
        print(f"[{date_heure}] : {prix:,.0f} PO".replace(',', ' '))
    print("-----------------------------\n")
    conn.close()

# --- PARTIE 2 : L'API BLIZZARD ---
def get_token():
    url = "https://oauth.battle.net/token"
    data = {"grant_type": "client_credentials"}
    auth = (CLIENT_ID, CLIENT_SECRET)
    response = requests.post(url, data=data, auth=auth)
    
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def get_wow_token_price(access_token):
    url = "https://eu.api.blizzard.com/data/wow/token/index"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"namespace": "dynamic-eu", "locale": "fr_FR"}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()["price"] / 10000
    return None

# --- PARTIE 3 : LE CHEF D'ORCHESTRE ---
if __name__ == "__main__":
    print("Lancement du Gobelin Analyste...\n")
    
    # 1. On s'assure que la base de données existe
    setup_database()
    
    # 2. On récupère le pass de Blizzard
    token = get_token()
    
    if token:
        # 3. On va chercher le prix
        prix = get_wow_token_price(token)
        
        if prix:
            print(f"💰 Le prix actuel est de : {prix:,.0f} PO".replace(',', ' '))
            
            # 4. On sauvegarde en base de données
            save_price_to_db(prix)
            
            # 5. On affiche l'historique
            show_price_history()