"""
ah_pipeline.py — Pipeline ETL (Extract, Transform, Load)
=========================================================
Ce script orchestre le cycle complet de collecte de données :
  1. EXTRACT  → Télécharge les ~80 000 enchères depuis l'API Blizzard
  2. TRANSFORM → Filtre le bruit, isole le prix minimum par objet surveillé
  3. LOAD     → Persiste les résultats dans la base de données relationnelle

Compétences démontrées : Data Engineering, Pipeline ETL, API REST, SQL.
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


# ──────────────────────────────────────────────
#  AUTHENTIFICATION BLIZZARD (OAuth 2.0)
# ──────────────────────────────────────────────

def get_access_token() -> str:
    """Obtient un jeton OAuth2 via Client Credentials Grant."""
    url = "https://oauth.battle.net/token"
    resp = requests.post(
        url,
        data={"grant_type": "client_credentials"},
        auth=(BLIZZARD_CLIENT_ID, BLIZZARD_CLIENT_SECRET),
        timeout=15,
    )
    resp.raise_for_status()
    token = resp.json()["access_token"]
    print("🔑 Authentification OAuth2 réussie.")
    return token


# ──────────────────────────────────────────────
#  PIPELINE ETL
# ──────────────────────────────────────────────

def extract(token: str) -> list[dict]:
    """Phase EXTRACT — Télécharge les enchères brutes."""
    url = (
        f"https://{REGION}.api.blizzard.com/data/wow/"
        f"connected-realm/{CONNECTED_REALM_ID}/auctions"
    )
    headers = {"Authorization": f"Bearer {token}"}
    params = {"namespace": f"dynamic-{REGION}", "locale": LOCALE}

    print("📡 Connexion à l'Hôtel des Ventes...")
    start = time.time()
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    elapsed = time.time() - start

    auctions = resp.json().get("auctions", [])
    print(f"📥 {len(auctions):,} enchères extraites en {elapsed:.1f}s")
    return auctions


def transform(auctions: list[dict]) -> dict[int, float]:
    """Phase TRANSFORM — Isole le prix minimum par objet surveillé."""
    lowest = {item_id: float("inf") for item_id in TRACKED_ITEMS}

    for auc in auctions:
        aid = auc["item"]["id"]
        if aid in lowest:
            price = auc.get("unit_price", auc.get("buyout", 0))
            if 0 < price < lowest[aid]:
                lowest[aid] = price

    # Convertit cuivre → or et élimine les objets non trouvés
    results = {
        iid: price / 10_000
        for iid, price in lowest.items()
        if price != float("inf")
    }
    print(f"⚙️  Transformation terminée : {len(results)} objets avec prix valide.")
    return results


def load(prices: dict[int, float]):
    """Phase LOAD — Persiste les prix dans la base relationnelle."""
    for item_id, gold_price in prices.items():
        insert_price(item_id, gold_price)
        print(f"  💾 {TRACKED_ITEMS[item_id]:40s} → {gold_price:>12,.2f} PO")

    print(f"✅ Pipeline ETL terminé — base {'PostgreSQL' if IS_POSTGRES else 'SQLite'} à jour.")


# ──────────────────────────────────────────────
#  POINT D'ENTRÉE
# ──────────────────────────────────────────────

def run():
    """Exécute le pipeline complet."""
    validate_config()
    setup_tables()

    # Enregistre les objets surveillés
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
        print(f"❌ Erreur fatale : {e}", file=sys.stderr)
        sys.exit(1)
