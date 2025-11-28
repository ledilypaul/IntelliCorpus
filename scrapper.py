import requests, feedparser, json
from config_info import APIS

url = 'http://export.arxiv.org/api/query?search_query=all:electron&start=0&max_results=1'
headers = {"User-Agent": "python-requests"}
"""
User-Agent	Identifie le client (navigateur, script Python, etc.)
Accept	Indique les formats de réponse acceptés (application/json, etc.)
Accept-Language	Langue préférée pour la réponse (fr-FR, en-US, etc.)
Authorization	Sert à transmettre une clé API ou un token d’accès sécurisé
Connection	Gère la persistance de la connexion (keep-alive, close)

"""

# def fetch_results(source, query, api_key=None):
#     url = source["api_url"].format(query=query, apikey=api_key or "")
#     print(url)
#     headers = {"User-Agent": "python-requests"}
#     if source.get("requires_api_key") and source == "CORE" and api_key:
#         headers["Authorization"] = f"Bearer {api_key}"
#     try:
#         response = requests.get(url, headers=headers, timeout=15)
#         if "application/json" in response.headers.get("Content-Type", ""):
#             return response.json()
#         return response.text
#     except Exception as e:
#         print(f"⚠️ Erreur pour {source} : {e}")
#         return None

def fetch_raw(url, headers=None):
    headers = headers or {"User-Agent": "python-requests"}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.text if "xml" in r.headers.get("Content-Type", "") else r.json()

def parser_arxiv(raw_result : str):
    feed = feedparser.parse(raw_result)
    results = []
    for e in feed.entries:
        results.append({
            "id": e.get("id"),
            "title": e.get("title"),
            "summary": e.get("summary"),
            "published": e.get("published"),
            "updated": e.get("updated"),
            "authors": [a.name for a in e.get("authors", [])],
            "pdf_url": next((link.href for link in e.links if link.type == "application/pdf"), None),
            "source": "arxiv"
        })
    print(feed)
    return 0

def parser_hal(raw_result : str):
    feed = json.loads(raw_result)
    for e in feed:
        print(e)
    # print(feed)
    results = []
    # for e in feed.entries:

        

raw_result = fetch_raw(APIS["arXiv"]["api_url"].format(query="AI agent",quantity='1'))
raw_result3 = fetch_raw(APIS["HAL"]["api_url"].format(query="AI agent",quantity='2'))

# result = fetch_results(APIS["arXiv"],"AI agent")
print(raw_result3)