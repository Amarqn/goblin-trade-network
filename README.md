# Goblin Trade Network

**Outil d'analyse de marché pour World of Warcraft**

Application web qui surveille l'Hôtel des Ventes (Auction House) du serveur Hyjal-EU en temps réel et génère des recommandations d'achat/vente.

Accessible en ligne : **https://goblin-trade-network.onrender.com**

## Contexte

World of Warcraft possède une économie virtuelle complexe. Chaque serveur héberge un Hôtel des Ventes où les joueurs achètent et vendent des objets contre de l'or (la monnaie du jeu). À tout instant, des dizaines de milliers d'enchères sont actives, avec des prix qui fluctuent en fonction de l'offre et la demande, exactement comme un marché financier réel.

Le problème : analyser manuellement 80 000+ enchères pour trouver les bonnes affaires est impossible. Ce projet automatise ce processus en collectant les données via l'API officielle de Blizzard, en les stockant dans une base de données, et en appliquant des indicateurs statistiques pour identifier les objets sous-évalués ou surévalués.

## Comment ça fonctionne

Le projet suit un pipeline en 4 étapes :

**1. Collecte (ah_pipeline.py)**
Un script se connecte aux serveurs de Blizzard via OAuth 2.0 et télécharge l'intégralité des enchères actives (~80 000 entrées). C'est un pipeline ETL classique : extraction des données brutes, transformation (nettoyage, calcul du prix minimum par objet), puis chargement en base.

**2. Stockage (db.py)**
Les données sont persistées dans une base relationnelle. Le projet supporte SQLite pour le développement local et PostgreSQL (via Supabase) pour la production. Une couche d'abstraction permet de basculer entre les deux sans changer le code métier.

**3. Analyse (server.py)**
Une API REST (FastAPI) expose les données et applique un algorithme de recommandation inspiré des stratégies de finance quantitative. Il compare le prix actuel à la moyenne mobile et à l'écart-type pour générer un signal : acheter (prix anormalement bas), vendre (prix anormalement haut), ou conserver (prix stable).

**4. Interface (static/index.html)**
Un dashboard interactif permet de visualiser les prix, comparer les objets entre eux, et consulter les recommandations. Le tout fonctionne dans un navigateur, sans installation.

## Architecture

```
Frontend (HTML/CSS/JS + Chart.js)
        |
        | HTTP REST
        v
Backend (FastAPI + Python)
        |
        | SQL
        v
Base de données (SQLite / PostgreSQL)
        ^
        | Alimenté par
        |
Pipeline ETL (API Blizzard, OAuth 2.0)
```

## Algorithme de recommandation

L'algorithme repose sur trois indicateurs :

- **Moyenne mobile** : prix moyen sur les N derniers relevés
- **Écart-type** : mesure de la volatilité
- **Tendance** : comparaison de la moyenne récente vs ancienne

Logique de décision :
- Prix < Moyenne - écart-type → ACHETER (sous-évalué)
- Prix > Moyenne + écart-type → VENDRE (surévalué)
- Sinon → CONSERVER (stable)

C'est une version simplifiée de la stratégie *Moving Average Crossover* utilisée en trading.

## Structure du projet

```
goblin-trade-network/
├── ah_pipeline.py      Pipeline ETL
├── server.py           API REST + algorithme de recommandation
├── db.py               Couche d'abstraction base de données
├── config.py           Configuration centralisée (.env)
├── requirements.txt    Dépendances Python
├── .env.example        Template de configuration
├── .gitignore          Fichiers exclus du versioning
├── README.md
└── static/
    └── index.html      Dashboard interactif
```

## Déploiement

Le projet tourne en production sur Render (backend) avec une base PostgreSQL sur Supabase. Les clés API sont stockées dans les variables d'environnement de Render, jamais dans le code source.

## Stack technique

Python, FastAPI, SQLite, PostgreSQL, Supabase, Chart.js, HTML/CSS/JS, API Blizzard (OAuth 2.0), Render

## Licence

Projet personnel à visée académique.
Données fournies par l'API Blizzard. © Blizzard Entertainment.
