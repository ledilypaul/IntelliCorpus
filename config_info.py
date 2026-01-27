APIS = {
    "arXiv" : {
        "api_url" : "http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={quantity}",
        "api_available" : True
    },
    "HAL": {
        "api_url": "https://api.archives-ouvertes.fr/search/?q={query}&rows={quantity}&wt=json&fl=docid,id_hal_s,uri_s,title_s,abstract_s,authFullName_s,publicationDate_s,doi_s,files_s,docType_s,journalTitle_s",
        "api_available": True
    },
    "PubMed": {
        "api_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={query}&retmax=5",
        "api_available": True
    },
    "Semantic Scholar": {
        "api_url": "https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit=5",
        "api_available": True
    },
    "Google Scholar": {
        "url": "https://scholar.google.com/scholar?q={query}",
        "api_available": False,
        "warning": "⚠️ CAPTCHA fréquent, scraping déconseillé"
    },
    "IEEE Xplore": {
        "api_url": "https://ieeexploreapi.ieee.org/api/v1/search/articles?queryText={query}&apikey={apikey}",
        "api_available": True,
        "requires_api_key": True
    },
    "CORE": {
        "api_url": "https://api.core.ac.uk/v3/search/works?q={query}",
        "api_available": True,
        "requires_api_key": True
    },
    "ResearchGate": {
        "url": "https://www.researchgate.net/search/publication?q={query}",
        "api_available": False,
        "warning": "⚠️ Protection anti-bot très forte"
    }
}
