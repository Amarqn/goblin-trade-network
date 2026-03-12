"""
Pipeline ETL pour l'Hôtel des Ventes de World of Warcraft.
Télécharge les enchères actives, isole le prix minimum
de chaque objet surveillé, et sauvegarde en base.
"""

import requests
import time
import sys
from config import (
    BLIZZARD_CLIENT_ID,
    BLIZZARD_CLIENT_SECRET,
    CONNECTED_REALM_ID,
    REGION,
    LOCALE,
    TRACKED_ITEMS,
    IS_POSTGRES,
    validate_config,
)
from db import setup_tables, upsert_item, insert_price


def get_access_token() -> str:
    """Authentification OAuth2 auprès de Blizzard."""
    resp = requests.post(
        "https://oauth.battle.net/token",
        data={"grant_type": "client_credentials"},
        auth=(BLIZZARD_CLIENT_ID, BLIZZARD_CLIENT_SECRET),
        timeout=15,
    )
    resp.raise_for_status()
    print("Authentification OK.")
    return resp.json()["access_token"]


def extract(token: str) -> list[dict]:
    """Télécharge toutes les enchères du serveur."""
    url = (
        f"https://{REGION}.api.blizzard.com/data/wow/"
        f"connected-realm/{CONNECTED_REALM_ID}/auctions"
    )
    headers = {"Authorization": f"Bearer {token}"}
    params = {"namespace": f"dynamic-{REGION}", "locale": LOCALE}

    print("Connexion a l'Hotel des Ventes...")
    start = time.time()
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()

    auctions = resp.json().get("auctions", [])
    print(f"{len(auctions):,} encheres extraites en {time.time() - start:.1f}s")
    return auctions


def transform(auctions: list[dict]) -> dict[int, float]:
    """Isole le prix minimum par objet surveillé."""
    lowest = {item_id: float("inf") for item_id in TRACKED_ITEMS}

    for auc in auctions:
        aid = auc["item"]["id"]
        if aid in lowest:
            price = auc.get("unit_price", auc.get("buyout", 0))
            if 0 < price < lowest[aid]:
                lowest[aid] = price

    results = {
        iid: price / 10_000
        for iid, price in lowest.items()
        if price != float("inf")
    }
    print(f"{len(results)} objets avec prix valide.")
    return results


def load(prices: dict[int, float]):
    """Sauvegarde les prix en base."""
    for item_id, gold_price in prices.items():
        insert_price(item_id, gold_price)
        print(f"  {TRACKED_ITEMS[item_id]:40s} -> {gold_price:>12,.2f} PO")

    db_type = "PostgreSQL" if IS_POSTGRES else "SQLite"
    print(f"Pipeline ETL termine. Base {db_type} a jour.")


def run():
    validate_config()
    setup_tables()

    for item_id, name in TRACKED_ITEMS.items():
        upsert_item(item_id, name)

    token = get_access_token()
    raw = extract(token)
    prices = transform(raw)
    load(prices)


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"Erreur: {e}", file=sys.stderr)
        sys.exit(1)
