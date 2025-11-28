"""
Scientific Article Scraper with FastAPI + Playwright
Supports: arXiv, Google Scholar, HAL, PubMed
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright
from typing import List, Optional, Dict
import asyncio
from datetime import datetime
import re
from urllib.parse import quote_plus
import hashlib

app = FastAPI(title="Scientific Scraper API", version="1.0")


# ========== MODELS ==========
class ScrapeRequest(BaseModel):
    keywords: List[str] = Field(..., example=["Apache Flink", "stream processing"])
    sources: List[str] = Field(default=["arxiv"], example=["arxiv", "scholar"])
    max_results: int = Field(default=10, ge=1, le=50)
    date_from: Optional[str] = Field(None, example="2024-01-01")


class Article(BaseModel):
    id: str  # Hash unique
    title: str
    authors: List[str]
    abstract: str
    url: str
    source: str
    publication_date: Optional[str]
    pdf_url: Optional[str]
    keywords: List[str]
    scraped_at: str


# ========== UTILITIES ==========
def generate_article_id(title: str, url: str) -> str:
    """Génère un ID unique pour dédupliquer"""
    unique_string = f"{title.lower().strip()}{url}"
    return hashlib.md5(unique_string.encode()).hexdigest()[:16]


def clean_text(text: str) -> str:
    """Nettoie le texte (espaces, retours à la ligne)"""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# ========== SCRAPERS ==========
async def scrape_arxiv(keywords: List[str], max_results: int, page) -> List[Dict]:
    """Scraper arXiv - API officielle disponible mais on montre Playwright"""
    articles = []
    query = " AND ".join([f'all:"{kw}"' for kw in keywords])
    url = f"https://arxiv.org/search/?query={quote_plus(query)}&searchtype=all&abstracts=show&order=-announced_date_first&size={max_results}"
    
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_selector("li.arxiv-result", timeout=10000)
        
        results = await page.query_selector_all("li.arxiv-result")
        
        for result in results[:max_results]:
            try:
                # Titre
                title_elem = await result.query_selector("p.title")
                title = clean_text(await title_elem.inner_text()) if title_elem else "N/A"
                
                # Auteurs
                authors_elem = await result.query_selector("p.authors")
                authors_text = await authors_elem.inner_text() if authors_elem else ""
                authors = [a.strip() for a in authors_text.replace("Authors:", "").split(",")]
                
                # Abstract
                abstract_elem = await result.query_selector("span.abstract-full")
                if not abstract_elem:
                    abstract_elem = await result.query_selector("p.abstract")
                abstract = clean_text(await abstract_elem.inner_text()) if abstract_elem else ""
                abstract = abstract.replace("△ Less", "").replace("▽ More", "")
                
                # URL et PDF
                link_elem = await result.query_selector("p.list-title a")
                article_url = await link_elem.get_attribute("href") if link_elem else ""
                if article_url and not article_url.startswith("http"):
                    article_url = f"https://arxiv.org{article_url}"
                
                pdf_url = article_url.replace("/abs/", "/pdf/") + ".pdf" if article_url else None
                
                # Date
                date_elem = await result.query_selector("p.is-size-7")
                date_text = await date_elem.inner_text() if date_elem else ""
                pub_date = re.search(r'Submitted.*?(\d{1,2}\s+\w+\s+\d{4})', date_text)
                pub_date = pub_date.group(1) if pub_date else None
                
                articles.append({
                    "title": title,
                    "authors": authors,
                    "abstract": abstract,
                    "url": article_url,
                    "pdf_url": pdf_url,
                    "source": "arxiv",
                    "publication_date": pub_date,
                    "keywords": keywords
                })
                
            except Exception as e:
                print(f"Error parsing arXiv result: {e}")
                continue
                
    except Exception as e:
        print(f"Error scraping arXiv: {e}")
    
    return articles


async def scrape_google_scholar(keywords: List[str], max_results: int, page) -> List[Dict]:
    """Scraper Google Scholar (attention au rate limiting!)"""
    articles = []
    query = "+".join([quote_plus(kw) for kw in keywords])
    url = f"https://scholar.google.com/scholar?q={query}&hl=en&as_sdt=0%2C5"
    
    try:
        # User agent important pour Scholar
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)  # Rate limiting respectueux
        
        results = await page.query_selector_all("div.gs_ri")
        
        for result in results[:max_results]:
            try:
                # Titre
                title_elem = await result.query_selector("h3.gs_rt a")
                title = clean_text(await title_elem.inner_text()) if title_elem else "N/A"
                article_url = await title_elem.get_attribute("href") if title_elem else ""
                
                # Auteurs et info
                authors_elem = await result.query_selector("div.gs_a")
                authors_text = await authors_elem.inner_text() if authors_elem else ""
                # Format: "Auteur1, Auteur2 - Source, Date"
                authors = [a.strip() for a in authors_text.split("-")[0].split(",")[:3]]
                
                # Abstract
                abstract_elem = await result.query_selector("div.gs_rs")
                abstract = clean_text(await abstract_elem.inner_text()) if abstract_elem else ""
                
                # PDF link si disponible
                pdf_elem = await result.query_selector("div.gs_ggs a")
                pdf_url = await pdf_elem.get_attribute("href") if pdf_elem else None
                
                articles.append({
                    "title": title,
                    "authors": authors,
                    "abstract": abstract,
                    "url": article_url,
                    "pdf_url": pdf_url,
                    "source": "google_scholar",
                    "publication_date": None,
                    "keywords": keywords
                })
                
            except Exception as e:
                print(f"Error parsing Scholar result: {e}")
                continue
                
    except Exception as e:
        print(f"Error scraping Scholar: {e}")
    
    return articles


async def scrape_hal(keywords: List[str], max_results: int, page) -> List[Dict]:
    """Scraper HAL (archives ouvertes françaises)"""
    articles = []
    query = " AND ".join([f'text_fulltext:"{kw}"' for kw in keywords])
    url = f"https://hal.science/search/index/?q={quote_plus(query)}&rows={max_results}"
    
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_selector("div.search-result-item", timeout=10000)
        
        results = await page.query_selector_all("div.search-result-item")
        
        for result in results[:max_results]:
            try:
                # Titre
                title_elem = await result.query_selector("h3.search-result-title a")
                title = clean_text(await title_elem.inner_text()) if title_elem else "N/A"
                article_url = await title_elem.get_attribute("href") if title_elem else ""
                if article_url and not article_url.startswith("http"):
                    article_url = f"https://hal.science{article_url}"
                
                # Auteurs
                authors_elems = await result.query_selector_all("span.search-result-authors a")
                authors = [clean_text(await a.inner_text()) for a in authors_elems]
                
                # Abstract
                abstract_elem = await result.query_selector("div.search-result-abstract")
                abstract = clean_text(await abstract_elem.inner_text()) if abstract_elem else ""
                
                # Date
                date_elem = await result.query_selector("span.search-result-date")
                pub_date = clean_text(await date_elem.inner_text()) if date_elem else None
                
                # PDF
                pdf_elem = await result.query_selector("a.btn-file")
                pdf_url = await pdf_elem.get_attribute("href") if pdf_elem else None
                
                articles.append({
                    "title": title,
                    "authors": authors,
                    "abstract": abstract,
                    "url": article_url,
                    "pdf_url": pdf_url,
                    "source": "hal",
                    "publication_date": pub_date,
                    "keywords": keywords
                })
                
            except Exception as e:
                print(f"Error parsing HAL result: {e}")
                continue
                
    except Exception as e:
        print(f"Error scraping HAL: {e}")
    
    return articles


# ========== API ENDPOINTS ==========
@app.get("/")
async def root():
    return {
        "service": "Scientific Article Scraper",
        "version": "1.0",
        "sources": ["arxiv", "scholar", "hal"],
        "endpoints": {
            "scrape": "/scrape [POST]",
            "health": "/health [GET]"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/scrape", response_model=Dict)
async def scrape_articles(request: ScrapeRequest):
    """
    Scrape articles scientifiques depuis plusieurs sources
    
    Exemple de requête:
    {
        "keywords": ["Apache Flink", "real-time processing"],
        "sources": ["arxiv", "scholar"],
        "max_results": 10
    }
    """
    
    all_articles = []
    errors = []
    
    # Validation des sources
    valid_sources = {"arxiv", "scholar", "hal"}
    invalid = set(request.sources) - valid_sources
    if invalid:
        raise HTTPException(400, f"Sources invalides: {invalid}. Utilisez: {valid_sources}")
    
    async with async_playwright() as p:
        # Lancement du navigateur
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        # Scraping par source
        for source in request.sources:
            try:
                if source == "arxiv":
                    articles = await scrape_arxiv(request.keywords, request.max_results, page)
                elif source == "scholar":
                    articles = await scrape_google_scholar(request.keywords, request.max_results, page)
                elif source == "hal":
                    articles = await scrape_hal(request.keywords, request.max_results, page)
                else:
                    continue
                
                all_articles.extend(articles)
                
            except Exception as e:
                errors.append({"source": source, "error": str(e)})
        
        await browser.close()
    
    # Déduplication par ID
    unique_articles = {}
    for article in all_articles:
        article_id = generate_article_id(article["title"], article["url"])
        if article_id not in unique_articles:
            article["id"] = article_id
            article["scraped_at"] = datetime.now().isoformat()
            unique_articles[article_id] = article
    
    return {
        "success": True,
        "query": {
            "keywords": request.keywords,
            "sources": request.sources,
            "max_results_per_source": request.max_results
        },
        "results": {
            "total": len(unique_articles),
            "articles": list(unique_articles.values())
        },
        "errors": errors if errors else None,
        "timestamp": datetime.now().isoformat()
    }


# ========== LANCEMENT ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)