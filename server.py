"""
server.py — API Backend (FastAPI)
==================================
Expose les données de l'Hôtel des Ventes via une API REST.
Intègre un algorithme d'analyse basé sur les moyennes mobiles
pour générer des recommandations d'achat/vente.

Compétences démontrées : API REST, Architecture MVC, IA basique, CORS.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from config import validate_config
from db import get_items as db_get_items, get_prices, get_stats


# ──────────────────────────────────────────────
#  APPLICATION FASTAPI
# ──────────────────────────────────────────────

app = FastAPI(
    title="Goblin Trade Network API",
    description="API d'analyse de l'économie de World of Warcraft",
    version="2.0.0",
)

# CORS — Autorise le frontend à communiquer avec le backend
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
#  ALGORITHME D'ANALYSE (IA Basique)
# ──────────────────────────────────────────────

def analyze_prices(history: list[dict]) -> dict:
    """
    Algorithme de recommandation basé sur la moyenne mobile.

    Stratégie :
    - Compare le prix actuel à la moyenne historique
    - Calcule la volatilité (écart-type) pour évaluer le risque
    - Identifie la tendance (haussière / baissière)
    - Génère un signal : ACHETER / VENDRE / ATTENDRE

    C'est une version simplifiée des indicateurs utilisés en finance
    quantitative (Moving Average Crossover Strategy).
    """
    if len(history) < 2:
        return {
            "action": "⏳ ATTENDRE",
            "color": "#f59e0b",
            "reason": "Pas assez de données — exécutez le pipeline ETL plusieurs fois.",
            "confidence": 0,
            "stats": None,
        }

    prices = [h["price"] for h in history]
    current = prices[0]
    avg = sum(prices) / len(prices)

    # Écart-type (mesure de volatilité)
    variance = sum((p - avg) ** 2 for p in prices) / len(prices)
    std_dev = variance ** 0.5

    # Tendance : comparer la première moitié à la seconde
    mid = len(prices) // 2
    recent_avg = sum(prices[:mid]) / mid if mid > 0 else avg
    older_avg = sum(prices[mid:]) / (len(prices) - mid) if len(prices) - mid > 0 else avg

    trend = "haussière" if recent_avg > older_avg else "baissière"
    deviation_pct = ((current - avg) / avg * 100) if avg > 0 else 0

    stats = {
        "current_price": round(current, 2),
        "average_price": round(avg, 2),
        "std_deviation": round(std_dev, 2),
        "volatility_pct": round((std_dev / avg * 100) if avg > 0 else 0, 1),
        "trend": trend,
        "deviation_pct": round(deviation_pct, 1),
        "data_points": len(prices),
    }

    # Logique de décision
    if current < avg - std_dev:
        return {
            "action": "🟢 ACHETER",
            "color": "#10b981",
            "reason": (
                f"Prix significativement sous la moyenne ({avg:,.1f} PO). "
                f"Tendance {trend}. Écart de {abs(deviation_pct):.1f}%."
            ),
            "confidence": min(90, int(abs(deviation_pct))),
            "stats": stats,
        }
    elif current > avg + std_dev:
        return {
            "action": "🔴 VENDRE",
            "color": "#ef4444",
            "reason": (
                f"Prix significativement au-dessus de la moyenne ({avg:,.1f} PO). "
                f"Tendance {trend}. Écart de +{deviation_pct:.1f}%."
            ),
            "confidence": min(90, int(abs(deviation_pct))),
            "stats": stats,
        }
    else:
        return {
            "action": "🟡 CONSERVER",
            "color": "#f59e0b",
            "reason": (
                f"Prix proche de la moyenne ({avg:,.1f} PO). "
                f"Volatilité : {stats['volatility_pct']}%. Tendance {trend}."
            ),
            "confidence": 50,
            "stats": stats,
        }


# ──────────────────────────────────────────────
#  ROUTES API
# ──────────────────────────────────────────────

@app.get("/api/items")
def get_items():
    """Retourne la liste des objets surveillés."""
    try:
        items = db_get_items()
        return {
            "status": "success",
            "count": len(items),
            "data": [{"id": r["id"], "name": r["name"]} for r in items],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prices/{item_id}")
def get_item_prices(item_id: int):
    """Retourne l'historique et l'analyse IA d'un objet."""
    try:
        rows = get_prices(item_id)
        history = [{"date": str(r["timestamp"]), "price": r["min_price_gold"]} for r in rows]
        analysis = analyze_prices(history)

        return {
            "status": "success",
            "item_id": item_id,
            "data": history,
            "analysis": analysis,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
def get_global_stats():
    """Retourne des statistiques globales pour le dashboard."""
    try:
        stats = get_stats()
        return {"status": "success", **stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
#  FRONTEND + FICHIERS STATIQUES
# ──────────────────────────────────────────────

@app.get("/")
def root():
    """Sert le frontend."""
    if os.path.isfile("static/index.html"):
        return FileResponse("static/index.html")
    return {"message": "Goblin Trade Network API v2.0", "docs": "/docs"}


# Monte les fichiers statiques sur /static (après les routes API)
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


# ──────────────────────────────────────────────
#  LANCEMENT
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    validate_config()
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
