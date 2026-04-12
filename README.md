# Structure recommandée
FastAPI (API REST)
├── /scrape endpoint
├── Playwright (navigation + extraction)
├── Parsers spécialisés par source
│   ├── arxiv_parser.py
│   ├── pubmed_parser.py
│   └── news_parser.py
└── Nettoyage basique (HTML → texte structuré)
```

**Alternatives à considérer** :
- **Firecrawl/Jina Reader API** : si tu veux éviter de maintenir Playwright
- **API natives** quand dispo (arXiv API, Semantic Scholar, etc.)

### **Phase Traitement/IA**

Tu as raison de séparer cette phase. Voici ce que je recommande :
```
┌─────────────────────────────────────────┐
│  Traitement post-scraping               │
├─────────────────────────────────────────┤
│ 1. Nettoyage avancé (regex, PDF→texte) │
│ 2. Déduplication (hash/embeddings)      │
│ 3. Enrichissement IA :                  │
│    - Résumé structuré (Claude API)      │
│    - Classification thématique          │
│    - Extraction entités clés            │
│ 4. Stockage (PostgreSQL + vecteurs?)    │
│ 5. Génération corpus final              │
└─────────────────────────────────────────┘
```

## 🚀 Architecture améliorée (optionnel)

Si tu veux pousser plus loin :
```
┌──────────┐      ┌────────────────┐      ┌──────────────┐
│   n8n    │─────▶│ Queue (Redis)  │─────▶│  Workers     │
│  (cron)  │      │  + Job tracking│      │  Scrapers    │
└──────────┘      └────────────────┘      └──────────────┘
                           │                      │
                           ▼                      ▼
                  ┌─────────────────┐    ┌────────────────┐
                  │  Traitement IA  │◀───│  Raw Storage   │
                  │  (Claude API)   │    │  (S3/local)    │
                  └─────────────────┘    └────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Base finale    │
                  │  + Embeddings   │
                  └─────────────────┘


mon_projet_recherche/
├── .env                     # Tes identifiants (Postgres, Neo4j, clés API)
├── requirements.txt         # Tes bibliothèques (sqlalchemy, polars, requests...)
│
├── config/
│   └── database.py          # Ton fichier de connexion (get_db_engine)
│
├── models/
│   └── postgres_schemas.py  # La définition de ta table (document_table)
│
├── scrapers/
│   ├── arxiv.py             # Fonction de scraping arXiv
│   ├── hal.py               # Fonction de scraping HAL
│   └── pubmed.py            # Fonction de scraping PubMed
│
├── processing/
│   └── cleaner.py           # Tes fonctions Polars pour nettoyer/dédupliquer
│
├── database/
│   └── crud.py              # Ta fameuse fonction upsert_data !
│
├── ai_pipeline/             # (Pour plus tard)
│   ├── chunking.py          
│   └── embeddings.py        
│
└── main_pipeline.py         # Le chef d'orchestre qui relie tout

## Roadmap IntelliCorpus

### Etape 1 — Consolidation
**Techno :** Python, PostgreSQL, SQLAlchemy, Polars
- Finaliser les scrapers (arXiv, HAL, PubMed)
- Ajouter `requirements.txt`
- Sécuriser le `.env`

### Etape 2 — Pipeline IA & PDFs
**Techno :** Claude API, pgvector, chunking

```
PDF → extraction texte → chunking → embeddings → pgvector
```

- Découper un PDF en chunks intelligents
- Générer des embeddings et faire de la recherche sémantique
- Implémenter le pattern RAG (Retrieval-Augmented Generation)

### Etape 3 — Graph DB & Ontologie
**Techno :** Neo4j, Cypher, RDF/OWL

```
PostgreSQL → ETL → Neo4j
Nœuds    : Article, Auteur, Concept, Journal
Relations : CITE, ÉCRIT_PAR, TRAITE_DE, PUBLIÉ_DANS
```

- Modéliser des relations complexes (citations, co-auteurs, concepts)
- Apprendre le langage Cypher
- Introduction à l'ontologie : classes, propriétés, inférences

### Etape 4 — Orchestration n8n
**Techno :** n8n, webhooks, cron jobs

```
Chaque nuit → scrape nouvelles publis → normalise → insère DB
            → si nouveau concept détecté → enrichit Neo4j → notification
```

- Construire des workflows visuels
- Déclencher des pipelines sur événement ou schedule
- Connecter des services entre eux