import json

def parser_hal(feed : str):
    if isinstance(feed, str):
        feed = json.loads(feed)
    docs = feed.get("response", {}).get("docs", [])
    results = []
    for doc in docs:
        results.append({
            "id": doc.get("docid"),
            "title" : doc.get("title_s"),
            "summary" : doc.get("abstract_s"),
            "published" : doc.get("publicationDate_s"),
            "authors" : [a for a in doc.get("authFullName_s",[])],
            "uri": doc.get("uri_s"),
            "pdf_url" : doc.get("files_s"),
            "source": "hal"
        })
    return results
