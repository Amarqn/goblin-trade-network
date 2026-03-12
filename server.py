"""
API REST pour le Goblin Trade Network.
Sert le dashboard et expose les données de l'Hôtel des Ventes
avec un algorithme de recommandation basé sur les moyennes mobiles.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from config import validate_config
from db import get_items as db_get_items, get_prices, get_stats


app = FastAPI(
    title="Goblin Trade Network API",
    version="3.0.0",
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def analyze_prices(history: list[dict]) -> dict:
    """
    Compare le prix actuel à la moyenne et l'écart-type
    pour générer un signal d'achat, vente ou conservation.
    """
    if len(history) < 2:
        return {
            "action": "ATTENDRE",
            "signal": "wait",
            "color": "#f59e0b",
            "reason": "Pas assez de données.",
            "confidence": 0,
            "stats": None,
        }

    prices = [h["price"] for h in history]
    current = prices[0]
    avg = sum(prices) / len(prices)
    variance = sum((p - avg) ** 2 for p in prices) / len(prices)
    std_dev = variance ** 0.5

    mid = len(prices) // 2
    recent_avg = sum(prices[:mid]) / mid if mid > 0 else avg
    older_avg = sum(prices[mid:]) / (len(prices) - mid) if len(prices) - mid > 0 else avg

    trend = "haussiere" if recent_avg > older_avg else "baissiere"
    trend_label = "Haussière" if trend == "haussiere" else "Baissière"
    deviation_pct = ((current - avg) / avg * 100) if avg > 0 else 0

    stats = {
        "current_price": round(current, 2),
        "average_price": round(avg, 2),
        "std_deviation": round(std_dev, 2),
        "volatility_pct": round((std_dev / avg * 100) if avg > 0 else 0, 1),
        "trend": trend,
        "trend_label": trend_label,
        "deviation_pct": round(deviation_pct, 1),
        "data_points": len(prices),
        "min_price": round(min(prices), 2),
        "max_price": round(max(prices), 2),
    }

    if current < avg - std_dev:
        return {
            "action": "ACHETER",
            "signal": "buy",
            "color": "#10b981",
            "reason": f"Prix sous la moyenne de {abs(deviation_pct):.1f}%. Tendance {trend_label.lower()}.",
            "confidence": min(90, int(abs(deviation_pct))),
            "stats": stats,
        }
    elif current > avg + std_dev:
        return {
            "action": "VENDRE",
            "signal": "sell",
            "color": "#ef4444",
            "reason": f"Prix au-dessus de la moyenne de +{deviation_pct:.1f}%. Tendance {trend_label.lower()}.",
            "confidence": min(90, int(abs(deviation_pct))),
            "stats": stats,
        }
    else:
        return {
            "action": "CONSERVER",
            "signal": "hold",
            "color": "#f59e0b",
            "reason": f"Prix stable autour de la moyenne. Volatilité: {stats['volatility_pct']}%.",
            "confidence": 50,
            "stats": stats,
        }


# --- Routes ---

@app.get("/api/items")
def get_items():
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
    try:
        stats = get_stats()
        return {"status": "success", **stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard")
def get_dashboard():
    """Données complètes pour le dashboard : classement, alertes, analyses."""
    try:
        items = db_get_items()
        dashboard = []

        for item in items:
            rows = get_prices(item["id"])
            history = [{"date": str(r["timestamp"]), "price": r["min_price_gold"]} for r in rows]
            analysis = analyze_prices(history)
            dashboard.append({
                "id": item["id"],
                "name": item["name"],
                "history": history,
                "analysis": analysis,
            })

        dashboard.sort(
            key=lambda x: x["analysis"]["stats"]["current_price"]
            if x["analysis"]["stats"]
            else float("inf")
        )

        deals = [d for d in dashboard if d["analysis"]["signal"] == "buy"]
        stats = get_stats()

        return {
            "status": "success",
            "items": dashboard,
            "deals": deals,
            "stats": stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Frontend ---

@app.get("/")
def root():
    if os.path.isfile("static/index.html"):
        return FileResponse("static/index.html")
    return {"message": "Goblin Trade Network API", "docs": "/docs"}


if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    validate_config()
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
