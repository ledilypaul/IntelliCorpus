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