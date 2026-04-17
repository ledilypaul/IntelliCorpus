# IntelliCorpus

Projet d'apprentissage progressif pour construire un corpus scientifique intelligent.
Chaque étape introduit une nouvelle stack technologique sur un cas d'usage concret.

---

## Objectif final

Un système capable de :
- Collecter automatiquement des articles scientifiques (arXiv, HAL, PubMed)
- Stocker les PDFs et leurs métadonnées
- Répondre à des questions sur le contenu via RAG (Retrieval-Augmented Generation)
- Modéliser les relations entre articles, auteurs et concepts (graph de connaissances)
- Exposer la base de connaissances via une API GraphQL
- S'orchestrer automatiquement via n8n (scraping nocturne, enrichissement IA)

---

## Architecture cible

```
┌─────────────┐     ┌──────────────────┐     ┌───────────────┐
│     n8n     │────▶│  Scrapers (APIs) │────▶│  PostgreSQL   │
│  (schedule) │     │  arXiv/HAL/      │     │  (métadonnées)│
└─────────────┘     │  PubMed          │     └───────┬───────┘
                    └──────────────────┘             │
                                                     ▼
                    ┌──────────────────┐     ┌───────────────┐
                    │   Claude API     │◀────│    MinIO      │
                    │   (RAG + Q&A)    │     │   (PDFs)      │
                    └────────┬─────────┘     └───────────────┘
                             │
                    ┌────────▼─────────┐     ┌───────────────┐
                    │    pgvector      │     │    Neo4j      │
                    │  (embeddings)    │     │  (graphe de   │
                    └──────────────────┘     │  connaissances│
                                             └───────┬───────┘
                                                     │
                                            ┌────────▼──────┐
                                            │  GraphQL API  │
                                            └───────────────┘
```

---

## Stack technologique

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| Collecte | Python, feedparser, requests | Scrapers arXiv / HAL / PubMed |
| Métadonnées | PostgreSQL + SQLAlchemy | Stockage structuré des articles |
| PDFs | MinIO (S3-compatible) | Stockage objet local, scalable cloud |
| Embeddings | pgvector (extension PostgreSQL) | Recherche sémantique |
| IA / RAG | Claude API | Q&A sur les articles |
| Graphe | Neo4j + Cypher | Relations auteurs / citations / concepts |
| API | GraphQL (Strawberry ou Ariadne) | Exposition de la base de connaissances |
| Orchestration | n8n | Automatisation des pipelines |

---

## Roadmap

### Étape 1 — Collecte & Stockage *(en cours)*

**Stack :** Python, PostgreSQL, SQLAlchemy, Polars, MinIO

**Objectif :** Pipeline complet de collecte → nettoyage → stockage

- [x] Scrapers arXiv, HAL, PubMed (APIs officielles)
- [x] Normalisation des données avec Polars
- [x] Upsert PostgreSQL (métadonnées)
- [ ] Mise en place MinIO pour stocker les PDFs
- [ ] Téléchargement et stockage des PDFs dans MinIO
- [ ] Référencer le chemin PDF dans PostgreSQL (`pdf_url` → chemin MinIO)
- [ ] `main_pipeline.py` : orchestrateur bout en bout

**Schéma de données :**
```
PostgreSQL
└── articles
    ├── id (UUID5 déterministe)
    ├── title, abstract, authors
    ├── source (arxiv / hal / pubmed)
    ├── published_at
    └── minio_path  ← chemin vers le PDF dans MinIO
```

---

### Étape 2 — RAG & IA Générative

**Stack :** Claude API, pgvector, PyMuPDF ou pdfplumber

**Objectif :** Pouvoir poser des questions sur ses articles et obtenir des réponses sourcées

```
PDF (MinIO) → extraction texte → chunking → embeddings → pgvector
                                                              ↓
                                          requête utilisateur → Claude API → réponse sourcée
```

- [ ] Extraction du texte depuis les PDFs (pdfplumber)
- [ ] Découpage en chunks intelligents (par section, par paragraphe)
- [ ] Génération d'embeddings via Claude API ou `sentence-transformers`
- [ ] Stockage des embeddings dans pgvector
- [ ] Implémentation du pattern RAG : recherche sémantique → contexte → Claude API
- [ ] Interface CLI simple pour interroger le corpus

---

### Étape 3 — Graphe de connaissances avec Neo4j

**Stack :** Neo4j, Cypher, Python driver Neo4j

**Objectif :** Modéliser les relations complexes entre entités scientifiques

```
PostgreSQL → ETL → Neo4j

Nœuds    : Article, Auteur, Concept, Journal
Relations : CITE, ÉCRIT_PAR, TRAITE_DE, PUBLIÉ_DANS
```

- [ ] Installer Neo4j (Docker)
- [ ] Apprendre Cypher (langage de requête Neo4j)
- [ ] Extraire les entités (auteurs, concepts) via Claude API
- [ ] ETL PostgreSQL → Neo4j
- [ ] Requêtes : "quels auteurs travaillent sur le même concept ?", "quels articles se citent ?"

---

### Étape 4 — API GraphQL

**Stack :** Strawberry (Python) ou Ariadne, FastAPI

**Objectif :** Exposer toute la base de connaissances en une seule API interrogeable

```
GraphQL ≠ Graph DB
GraphQL = langage de requête pour API (alternative à REST)
→ tu demandes exactement les champs que tu veux, en une seule requête
```

- [ ] Comprendre la différence GraphQL vs REST
- [ ] Définir le schéma GraphQL (types Article, Author, Concept)
- [ ] Connecter PostgreSQL + Neo4j derrière le même endpoint GraphQL
- [ ] Requêtes imbriquées : article → auteurs → autres articles du même auteur

---

### Étape 5 — Orchestration n8n

**Stack :** n8n, webhooks, cron jobs

**Objectif :** Automatiser l'ensemble du pipeline sans intervention manuelle

```
Chaque nuit :
  → scrape nouvelles publications
  → normalise et insère dans PostgreSQL
  → télécharge les PDFs dans MinIO
  → génère les embeddings → pgvector
  → enrichit Neo4j (nouveaux auteurs, concepts)
  → notification si nouveau concept détecté
```

- [ ] Configurer n8n (déjà dans docker-compose)
- [ ] Workflow : scraping nocturne (cron)
- [ ] Workflow : enrichissement IA sur nouveaux documents
- [ ] Workflow : notification sur détection de nouveau concept

---

## Structure du projet

```
IntelliCorpus/
├── .env                    # Credentials (Postgres, MinIO, Claude API)
├── requirements.txt
├── docker-compose.yml      # PostgreSQL + MinIO + n8n + Neo4j
├── main_pipeline.py        # Orchestrateur principal
│
├── config/
│   └── database.py         # Connexion PostgreSQL (singleton)
│
├── models/
│   └── corpus_schema.py    # Schéma SQLAlchemy
│
├── scrapers/
│   ├── arxiv.py
│   ├── hal.py
│   └── pubmed.py
│
├── processing/
│   └── cleaning_data.py    # Normalisation Polars
│
├── database/
│   └── crud.py             # Upsert PostgreSQL
│
├── storage/                # (Étape 1)
│   └── minio_client.py     # Upload/download PDFs
│
├── ai_pipelines/           # (Étape 2)
│   ├── pdf_extractor.py    # PDF → texte
│   ├── chunker.py          # Découpage en chunks
│   ├── embeddings.py       # Génération embeddings
│   └── rag.py              # Pipeline RAG + Claude API
│
├── graph/                  # (Étape 3)
│   ├── neo4j_client.py
│   └── etl_postgres_neo4j.py
│
└── api/                    # (Étape 4)
    └── graphql_schema.py   # API GraphQL
```

---

## Lancer le projet

```bash
# 1. Copier et remplir les variables d'environnement
cp .env.example .env

# 2. Démarrer l'infrastructure
docker-compose up -d

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer le pipeline de collecte
python main_pipeline.py
```
