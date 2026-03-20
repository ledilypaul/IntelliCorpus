
import requests,time
from typing import List, Dict
from IPython.display import JSON
import xmltodict

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
DB = "pubmed"


def pubmed_search(
    query: str,
    retmax: int = 100,
    retstart: int = 0,
    email: str | None = None,
    api_key: str | None = None) -> Dict:
    """
    Step 1: Search PubMed and store results on NCBI server (usehistory)
    """
    url = f"{EUTILS_BASE}/esearch.fcgi"

    params = {
        "db": DB,
        "term": query,
        "retmax": retmax,
        "retstart": retstart,
        "usehistory": "y",
        "retmode": "json",
    }

    if email:
        params["email"] = email
    if api_key:
        params["api_key"] = api_key

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json()["esearchresult"]


def pubmed_fetch(
    webenv: str,
    query_key: str,
    batch_size: int = 100,
    email: str | None = None,
    api_key: str | None = None
) -> str:
    """
    Step 2: Fetch PubMed records using WebEnv + QueryKey (XML)
    """
    url = f"{EUTILS_BASE}/efetch.fcgi"

    params = {
        "db": DB,
        "query_key": query_key,
        "WebEnv": webenv,
        "retmax": batch_size,
        "retmode": "xml",
    }

    if email:
        params["email"] = email
    if api_key:
        params["api_key"] = api_key

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    return response.text


def fetch_pubmed(query: str, max_results: int = 200, batch_size: int = 100, delay: float = 0.34, email: str | None = None, api_key: str | None = None) -> List[str]:
    """
    High-level generator:
    - search
    - iterate over result pages
    - fetch XML batches
    """
    search_result = pubmed_search(
        query=query,
        retmax=max_results,
        email=email,
        api_key=api_key
    )
    count = int(search_result["count"])
    webenv = search_result["webenv"]
    query_key = search_result["querykey"]

    results_xml = []

    for start in range(0, min(count, max_results), batch_size):
        xml = pubmed_fetch(
            webenv=webenv,
            query_key=query_key,
            batch_size=batch_size,
            email=email,
            api_key=api_key,
        )
        results_xml.append(xml)
        time.sleep(delay)  # respect NCBI rate-limit
        # pprint(xml)
    return results_xml

from pprint import pprint
def format_hal_data(results):
    for result in results:
        parsed_dict = xmltodict.parse(result, dict_constructor=dict)
        print("yolo")
        pprint(parsed_dict)