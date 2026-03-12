import requests
import sqlite3
import time

# --- VOS CLÉS BLIZZARD ---
CLIENT_ID = "eb78f80c9496414ab1bab42b090afc52"
CLIENT_SECRET = "Ibt8O2w7TankTxjqvqw1rKigYo6WkBmo"
HYJAL_ID = 1390

# --- LE DICTIONNAIRE (Les objets qu'on veut surveiller) ---
# Format : { ID_Objet : "Nom de l'objet" }
# J'ai mis quelques composants de base de The War Within (Minerais, Herbes, Tissu)
TRACKED_ITEMS = {
    213699: "Bismuth (Minerai)",
    212280: "Arbuste-champignon (Herbe)",
    211330: "Tisse-toile (Tissu)",
    210804: "Poussière tempêtueuse (Enchantement)",
    224464: "Flacon de chaos alchimique"
}

def setup_database():
    """Prépare les tables de la base de données relationnelle."""
    conn = sqlite3.connect("wow_economy.db")
    cursor = conn.cursor()
    
    # Table du dictionnaire d'objets
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    ''')
    
    # Table de l'historique des prix de l'Hôtel des Ventes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ah_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            min_price_gold REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(item_id) REFERENCES items(id)
        )
    ''')
    
    # On remplit le dictionnaire dans la base
    for item_id, name in TRACKED_ITEMS.items():
        cursor.execute("INSERT OR IGNORE INTO items (id, name) VALUES (?, ?)", (item_id, name))
        
    conn.commit()
    conn.close()

def get_token():
    url = "https://oauth.battle.net/token"
    response = requests.post(url, data={"grant_type": "client_credentials"}, auth=(CLIENT_ID, CLIENT_SECRET))
    return response.json().get("access_token")

def run_etl_pipeline(access_token):
    print("🚀 Démarrage du Pipeline ETL...")
    
    # 1. EXTRACT (Téléchargement)
    url = f"https://eu.api.blizzard.com/data/wow/connected-realm/{HYJAL_ID}/auctions"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers, params={"namespace": "dynamic-eu", "locale": "fr_FR"})
    
    if response.status_code != 200:
        print("❌ Erreur de téléchargement.")
        return
        
    auctions = response.json().get("auctions", [])
    print(f"📥 Extraction terminée : {len(auctions):,} enchères brutes récupérées.")
    
    # 2. TRANSFORM (Nettoyage et calcul du prix minimum)
    # On prépare un dictionnaire temporaire avec des prix infinis
    lowest_prices = {item_id: float('inf') for item_id in TRACKED_ITEMS.keys()}
    
    for auc in auctions:
        item_id = auc["item"]["id"]
        
        # Si c'est un objet qu'on surveille
        if item_id in lowest_prices:
            # Le prix est soit à l'unité (unit_price), soit pour le lot (buyout)
            prix_brut = auc.get("unit_price", auc.get("buyout", 0))
            if prix_brut > 0 and prix_brut < lowest_prices[item_id]:
                lowest_prices[item_id] = prix_brut
                
    print("⚙️ Transformation terminée : Bruit éliminé, prix minimums isolés.")
    
    # 3. LOAD (Sauvegarde dans la base de données)
    conn = sqlite3.connect("wow_economy.db")
    cursor = conn.cursor()
    
    print("\n💾 --- RÉSULTATS SAUVEGARDÉS ---")
    for item_id, price_copper in lowest_prices.items():
        if price_copper != float('inf'):
            price_gold = price_copper / 10000
            name = TRACKED_ITEMS[item_id]
            print(f"- {name} : {price_gold:,.2f} PO")
            
            cursor.execute("INSERT INTO ah_prices (item_id, min_price_gold) VALUES (?, ?)", (item_id, price_gold))
            
    conn.commit()
    conn.close()
    print("✅ Pipeline ETL exécuté avec succès. La base de données est à jour !")

if __name__ == "__main__":
    setup_database()
    token = get_token()
    if token:
        run_etl_pipeline(token)