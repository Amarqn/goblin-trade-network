"""
config.py — Module de configuration centralisé.
Charge les variables d'environnement depuis un fichier .env
et les expose de manière sécurisée au reste de l'application.

Principe de Cybersécurité : Aucune clé API n'est jamais écrite en dur.
"""

import os
from dotenv import load_dotenv

# Charge le fichier .env s'il existe (mode développement local)
load_dotenv()


# --- Blizzard API ---
BLIZZARD_CLIENT_ID = os.getenv("BLIZZARD_CLIENT_ID")
BLIZZARD_CLIENT_SECRET = os.getenv("BLIZZARD_CLIENT_SECRET")

# --- Serveur WoW ---
CONNECTED_REALM_ID = int(os.getenv("CONNECTED_REALM_ID", "1390"))
REGION = os.getenv("REGION", "eu")
LOCALE = os.getenv("LOCALE", "fr_FR")

# --- Base de données ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///wow_economy.db")

# Détection automatique du mode
IS_POSTGRES = DATABASE_URL.startswith("postgresql")

# --- Serveur ---
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# --- Objets surveillés (Composants The War Within) ---
TRACKED_ITEMS = {
    213699: "Bismuth (Minerai)",
    212280: "Arbuste-champignon (Herbe)",
    211330: "Tisse-toile (Tissu)",
    210804: "Poussière tempêtueuse (Enchantement)",
    224464: "Flacon de chaos alchimique",
}


def validate_config():
    """Vérifie que les variables critiques sont bien définies."""
    missing = []
    if not BLIZZARD_CLIENT_ID:
        missing.append("BLIZZARD_CLIENT_ID")
    if not BLIZZARD_CLIENT_SECRET:
        missing.append("BLIZZARD_CLIENT_SECRET")

    if missing:
        raise EnvironmentError(
            f"⛔ Variables d'environnement manquantes : {', '.join(missing)}\n"
            f"💡 Créez un fichier .env à partir de .env.example"
        )
