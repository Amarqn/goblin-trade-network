"""
Script de test rapide.
Se connecte à l'API Blizzard et affiche un échantillon
des enchères actives sur le serveur.
"""

import requests
import time
from config import (
    BLIZZARD_CLIENT_ID,
    BLIZZARD_CLIENT_SECRET,
    CONNECTED_REALM_ID,
    validate_config,
)


def get_token():
    resp = requests.post(
        "https://oauth.battle.net/token",
        data={"grant_type": "client_credentials"},
        auth=(BLIZZARD_CLIENT_ID, BLIZZARD_CLIENT_SECRET),
    )
    if resp.status_code == 200:
        return resp.json()["access_token"]
    print("Erreur d'identification.")
    return None


def scan_auction_house(access_token):
    url = f"https://eu.api.blizzard.com/data/wow/connected-realm/{CONNECTED_REALM_ID}/auctions"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"namespace": "dynamic-eu", "locale": "fr_FR"}

    start = time.time()
    resp = requests.get(url, headers=headers, params=params)
    elapsed = time.time() - start

    if resp.status_code == 200:
        auctions = resp.json().get("auctions", [])
        print(f"Telechargement OK en {elapsed:.2f}s")
        print(f"Encheres actives : {len(auctions):,}".replace(",", " "))

        print("\nEchantillon (3 premieres encheres) :")
        for auc in auctions[:3]:
            item_id = auc["item"]["id"]
            qty = auc.get("quantity", 1)
            price = auc.get("unit_price", auc.get("buyout", 0)) / 10000
            print(f"  Objet {item_id} | Qte: {qty} | Prix: {price:,.2f} PO")
    else:
        print(f"Erreur : {resp.status_code}")


if __name__ == "__main__":
    validate_config()
    token = get_token()
    if token:
        scan_auction_house(token)
