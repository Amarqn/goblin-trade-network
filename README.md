# 💰 Goblin Trade Network

**Application Full-Stack d'Intelligence Économique pour World of Warcraft**

> Analyse en temps réel de l'Hôtel des Ventes (Auction House) du serveur Hyjal-EU, avec pipeline ETL, API REST et recommandations IA.

---

## 🎯 Objectif du Projet

Ce projet démontre l'intégration de compétences transversales en informatique à travers un cas d'usage concret : **l'optimisation des transactions dans une économie virtuelle de jeu vidéo**.

L'application collecte les données de ~80 000 enchères depuis l'API Blizzard, les transforme, les stocke dans une base relationnelle, et génère des recommandations d'achat/vente via un algorithme d'analyse statistique.

---

## 🏗️ Architecture Technique

```
┌─────────────────────────────────────────────────────┐
│                   FRONTEND (HTML/CSS/JS)             │
│          Dashboard interactif + Chart.js             │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP REST
┌──────────────────────▼──────────────────────────────┐
│                  BACKEND (FastAPI)                    │
│   API REST · Algorithme IA · Middleware CORS          │
└──────────────────────┬──────────────────────────────┘
                       │ SQL
┌──────────────────────▼──────────────────────────────┐
│              BASE DE DONNÉES (SQLite/PostgreSQL)     │
│         Schéma relationnel normalisé                 │
└──────────────────────┬──────────────────────────────┘
                       │ Alimenté par
┌──────────────────────▼──────────────────────────────┐
│              PIPELINE ETL (ah_pipeline.py)            │
│   Extract → Transform → Load  (API Blizzard OAuth2) │
└─────────────────────────────────────────────────────┘
```

---

## 🔬 Compétences Démontrées

| Domaine | Implémentation |
|---|---|
| **Data Engineering** | Pipeline ETL complet, extraction de ~80 000 enregistrements, nettoyage et chargement en base |
| **Intelligence Artificielle** | Algorithme de recommandation basé sur les moyennes mobiles, écart-type et analyse de tendance |
| **Développement Backend** | API REST avec FastAPI, architecture MVC, gestion d'erreurs, documentation auto-générée (Swagger) |
| **Développement Frontend** | Interface responsive, graphiques interactifs (Chart.js), UX soignée |
| **Base de Données** | Modèle relationnel normalisé, requêtes SQL optimisées, migration SQLite → PostgreSQL |
| **Cybersécurité** | Authentification OAuth 2.0 (Blizzard API), variables d'environnement, CORS configuré |
| **DevOps** | Déploiement Cloud (Render), CI/CD via GitHub, séparation des environnements |

---

## 📁 Structure du Projet

```
goblin-trade-network/
├── ah_pipeline.py        # Pipeline ETL (Extract, Transform, Load)
├── server.py             # API Backend FastAPI + Algorithme IA
├── config.py             # Configuration centralisée (variables d'env)
├── requirements.txt      # Dépendances Python
├── .env.example          # Template de configuration (sans secrets)
├── .gitignore            # Fichiers exclus du versioning
├── README.md             # Documentation
└── static/
    └── index.html        # Frontend (Dashboard interactif)
```

---

## 🚀 Installation & Lancement

### Prérequis
- Python 3.10+
- Un compte développeur Blizzard ([develop.battle.net](https://develop.battle.net))

### 1. Cloner le dépôt
```bash
git clone https://github.com/VOTRE_USERNAME/goblin-trade-network.git
cd goblin-trade-network
```

### 2. Configurer l'environnement
```bash
cp .env.example .env
# Éditez .env avec vos clés Blizzard
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Lancer le pipeline ETL (collecte des données)
```bash
python ah_pipeline.py
```

### 5. Démarrer le serveur
```bash
python server.py
```

L'application est accessible sur `http://localhost:8000`.

---

## 📊 Algorithme d'Analyse

L'algorithme de recommandation repose sur trois indicateurs statistiques :

1. **Moyenne mobile** — Prix moyen sur les N derniers relevés
2. **Écart-type** — Mesure de la volatilité des prix
3. **Tendance directionnelle** — Comparaison de la moyenne récente vs. ancienne

**Logique de décision :**
- `ACHETER` → Prix < Moyenne − σ (sous-évalué)
- `VENDRE` → Prix > Moyenne + σ (surévalué)
- `CONSERVER` → Prix dans l'intervalle [μ−σ, μ+σ] (stable)

Cette approche s'inspire de la stratégie financière *Moving Average Crossover*, simplifiée pour le contexte du jeu.

---

## 🌐 Déploiement Cloud

Le projet est déployé sur **Render** (backend + frontend) avec une base **PostgreSQL** hébergée sur **Supabase**.

**URL de production :** `https://goblin-trade-network.onrender.com`

---

## 🛡️ Sécurité

- Les clés API ne sont **jamais** versionnées (`.gitignore`)
- Authentification **OAuth 2.0** avec les serveurs Blizzard
- Variables sensibles stockées en **variables d'environnement**
- CORS configuré pour restreindre les origines autorisées

---

## 📄 Licence

Projet personnel à visée académique.  
Données fournies par l'API Blizzard — © Blizzard Entertainment.
