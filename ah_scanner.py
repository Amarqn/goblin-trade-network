import requests
import time

# --- VOS CLÉS BLIZZARD ---
CLIENT_ID = "eb78f80c9496414ab1bab42b090afc52"
CLIENT_SECRET = "Ibt8O2w7TankTxjqvqw1rKigYo6WkBmo"

# ID du serveur Hyjal (EU)
HYJAL_ID = 1390

def get_token():
    url = "https://oauth.battle.net/token"
    data = {"grant_type": "client_credentials"}
    auth = (CLIENT_ID, CLIENT_SECRET)
    response = requests.post(url, data=data, auth=auth)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print("❌ Erreur d'identification.")
        return None

def scan_auction_house(access_token):
    print("📡 Connexion à l'Hôtel des Ventes d'Hyjal en cours...")
    print("⏳ Attention, le fichier est énorme, cela peut prendre quelques secondes...\n")
    
    # L'URL officielle pour récupérer TOUT l'Hôtel des Ventes d'un serveur
    url = f"https://eu.api.blizzard.com/data/wow/connected-realm/{HYJAL_ID}/auctions"
    
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"namespace": "dynamic-eu", "locale": "fr_FR"}
    
    # On chronomètre pour voir à quelle vitesse on télécharge cette masse de données
    start_time = time.time()
    response = requests.get(url, headers=headers, params=params)
    end_time = time.time()
    
    if response.status_code == 200:
        data = response.json()
        auctions = data.get("auctions", [])
        
        print(f"✅ TÉLÉCHARGEMENT RÉUSSI en {end_time - start_time:.2f} secondes !")
        print(f"📦 Nombre d'enchères actives en ce moment même : {len(auctions):,.0f}".replace(',', ' '))
        
        print("\n🔎 --- ÉCHANTILLON (Les 3 premières enchères brutes) ---")
        for i in range(3):
            enchere = auctions[i]
            item_id = enchere["item"]["id"]
            quantite = enchere.get("quantity", 1)
            
            # Les prix sont parfois "buyout" (achat immédiat) ou "unit_price" (prix à l'unité)
            prix_brut = enchere.get("unit_price", enchere.get("buyout", 0))
            prix_or = prix_brut / 10000
            
            print(f"- Objet ID: {item_id} | Quantité: {quantite} | Prix unitaire: {prix_or:,.2f} PO")
        
        print("\n🤯 Imaginez devoir trier ça à la main...")
    else:
        print(f"❌ Erreur lors de la requête : {response.status_code}")

if __name__ == "__main__":
    token = get_token()
    if token:
        scan_auction_house(token)