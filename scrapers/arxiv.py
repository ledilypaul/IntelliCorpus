import feedparser

def parser_arxiv(raw_result : str):
    feed = feedparser.parse(raw_result)
    results = []
    for e in feed.entries:
        results.append({
            "id": e.get("id"),
            "title": e.get("title"),
            "summary": e.get("summary"),
            "published_at": e.get("published"),
            "updated": e.get("updated"),
            "authors": [a.name for a in e.get("authors", [])],
            "pdf_url": next((link.href + ".pdf" for link in e.links if link.type == "application/pdf"), None),
            "source": "arxiv"
        })
    return results