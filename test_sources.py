"""
Test automatique des sources scientifiques
Vérifie l'accessibilité et détecte les protections anti-bot
"""

import requests
import time
from typing import Dict, List
from datetime import datetime

# Configuration
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

SOURCES_TO_TEST = {
    "arXiv": {
        "url": "https://arxiv.org/search/?query=all:machine+learning&searchtype=all&size=10",
        "check_strings": ["arxiv-result", "Search Results"],
        "api_available": True,
        "api_url": "http://export.arxiv.org/api/query?search_query=all:machine+learning&max_results=5"
    },
    "HAL": {
        "url": "https://hal.science/search/index/?q=machine+learning&rows=10",
        "check_strings": ["search-result-item", "résultats"],
        "api_available": True,
        "api_url": "https://api.archives-ouvertes.fr/search/?q=machine+learning&rows=5"
    },
    "PubMed": {
        "url": "https://pubmed.ncbi.nlm.nih.gov/?term=machine+learning",
        "check_strings": ["search-results", "docsum-title"],
        "api_available": True,
        "api_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=machine+learning&retmax=5"
    },
    "Semantic Scholar": {
        "url": "https://www.semanticscholar.org/search?q=machine%20learning",
        "check_strings": ["search-result", "paper-title"],
        "api_available": True,
        "api_url": "https://api.semanticscholar.org/graph/v1/paper/search?query=machine+learning&limit=5"
    },
    "Google Scholar": {
        "url": "https://scholar.google.com/scholar?q=machine+learning",
        "check_strings": ["gs_ri", "gs_rt"],
        "api_available": False,
        "warning": "⚠️ Rate limiting très strict + CAPTCHA fréquent"
    },
    "IEEE Xplore": {
        "url": "https://ieeexplore.ieee.org/search/searchresult.jsp?queryText=machine%20learning",
        "check_strings": ["List-results", "result-item"],
        "api_available": True,
        "api_url": "https://ieeexploreapi.ieee.org/api/v1/search/articles",
        "note": "Requiert API Key (gratuite pour 200 req/jour)"
    },
    "CORE": {
        "url": "https://core.ac.uk/search?q=machine%20learning",
        "check_strings": ["search-result", "article-title"],
        "api_available": True,
        "api_url": "https://api.core.ac.uk/v3/search/works",
        "note": "API gratuite avec clé"
    },
    "ResearchGate": {
        "url": "https://www.researchgate.net/search/publication?q=machine%20learning",
        "check_strings": ["nova-legacy-o-stack__item", "publication-title"],
        "api_available": False,
        "warning": "⚠️ Protection anti-bot forte, déconseillé"
    }
}


def test_source(name: str, config: Dict) -> Dict:
    """Teste l'accessibilité d'une source"""
    result = {
        "source": name,
        "url": config["url"],
        "status": "❌ FAILED",
        "status_code": None,
        "response_time": None,
        "accessible": False,
        "content_found": False,
        "has_api": config.get("api_available", False),
        "captcha_detected": False,
        "errors": [],
        "recommendations": []
    }
    
    try:
        start_time = time.time()
        response = requests.get(
            config["url"],
            headers=HEADERS,
            timeout=15,
            allow_redirects=True
        )
        result["response_time"] = round(time.time() - start_time, 2)
        result["status_code"] = response.status_code
        
        # Analyse du statut HTTP
        if response.status_code == 200:
            result["accessible"] = True
            result["status"] = "✅ ACCESSIBLE"
            
            # Vérifier le contenu
            content = response.text.lower()
            for check_string in config.get("check_strings", []):
                if check_string.lower() in content:
                    result["content_found"] = True
                    break
            
            # Détection CAPTCHA
            captcha_keywords = ["captcha", "recaptcha", "cloudflare", "access denied", "are you a robot"]
            if any(keyword in content for keyword in captcha_keywords):
                result["captcha_detected"] = True
                result["status"] = "⚠️ CAPTCHA"
                result["errors"].append("CAPTCHA ou protection anti-bot détecté")
                result["recommendations"].append("Utiliser l'API si disponible")
            
            if not result["content_found"] and not result["captcha_detected"]:
                result["errors"].append("Contenu attendu non trouvé (sélecteurs peut-être obsolètes)")
        
        elif response.status_code == 403:
            result["status"] = "🚫 BLOCKED"
            result["errors"].append("Accès refusé (403 Forbidden)")
            result["recommendations"].append("Utiliser User-Agent, proxies ou API")
        
        elif response.status_code == 429:
            result["status"] = "⏱️ RATE LIMITED"
            result["errors"].append("Trop de requêtes (429 Too Many Requests)")
            result["recommendations"].append("Ajouter des délais entre requêtes")
        
        else:
            result["errors"].append(f"Code HTTP inhabituel: {response.status_code}")
        
        # Test API si disponible
        if config.get("api_available") and config.get("api_url"):
            try:
                api_response = requests.get(config["api_url"], timeout=10)
                if api_response.status_code == 200:
                    result["api_status"] = "✅ API disponible"
                    result["recommendations"].append("🎯 RECOMMANDÉ: Utiliser l'API au lieu du scraping")
                else:
                    result["api_status"] = f"⚠️ API erreur {api_response.status_code}"
            except Exception as e:
                result["api_status"] = f"❌ API inaccessible: {str(e)[:50]}"
        
        # Warnings spécifiques
        if "warning" in config:
            result["warnings"] = config["warning"]
        
        if "note" in config:
            result["notes"] = config["note"]
            
    except requests.exceptions.Timeout:
        result["errors"].append("Timeout - site trop lent")
        result["recommendations"].append("Augmenter le timeout ou réessayer plus tard")
    
    except requests.exceptions.ConnectionError:
        result["errors"].append("Erreur de connexion - vérifier l'URL")
    
    except Exception as e:
        result["errors"].append(f"Erreur inattendue: {str(e)}")
    
    return result


def print_results(results: List[Dict]):
    """Affiche les résultats formatés"""
    print("\n" + "="*80)
    print("📊 RAPPORT DE TEST DES SOURCES SCIENTIFIQUES")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    accessible_count = sum(1 for r in results if r["accessible"])
    with_api = sum(1 for r in results if r["has_api"])
    
    print(f"✅ Sources accessibles: {accessible_count}/{len(results)}")
    print(f"🔌 Sources avec API: {with_api}/{len(results)}\n")
    
    for result in results:
        print(f"\n{'─'*80}")
        print(f"🔍 {result['source']}")
        print(f"{'─'*80}")
        print(f"Status: {result['status']}")
        print(f"URL: {result['url']}")
        
        if result["status_code"]:
            print(f"Code HTTP: {result['status_code']}")
        
        if result["response_time"]:
            print(f"Temps de réponse: {result['response_time']}s")
        
        if result.get("api_status"):
            print(f"API: {result['api_status']}")
        
        if result["errors"]:
            print(f"\n❌ Erreurs:")
            for error in result["errors"]:
                print(f"   - {error}")
        
        if result["recommendations"]:
            print(f"\n💡 Recommandations:")
            for rec in result["recommendations"]:
                print(f"   - {rec}")
        
        if result.get("warnings"):
            print(f"\n⚠️  {result['warnings']}")
        
        if result.get("notes"):
            print(f"\nℹ️  {result['notes']}")
    
    # Résumé des recommandations
    print(f"\n\n{'='*80}")
    print("🎯 RECOMMANDATIONS GLOBALES")
    print(f"{'='*80}\n")
    
    priority_apis = [r for r in results if r.get("api_status") and "✅" in r["api_status"]]
    if priority_apis:
        print("🥇 PRIORITÉ: Utiliser les APIs disponibles")
        for r in priority_apis:
            print(f"   - {r['source']}: {r.get('api_url', 'Voir documentation')}")
    
    print("\n🥈 Pour le scraping:")
    good_for_scraping = [r for r in results if r["accessible"] and not r["captcha_detected"]]
    if good_for_scraping:
        for r in good_for_scraping:
            print(f"   ✅ {r['source']}")
    
    blocked = [r for r in results if not r["accessible"] or r["captcha_detected"]]
    if blocked:
        print("\n⚠️  À éviter (bloqués ou protégés):")
        for r in blocked:
            print(f"   ❌ {r['source']}")


def main():
    print("🚀 Démarrage des tests...")
    print(f"Nombre de sources à tester: {len(SOURCES_TO_TEST)}\n")
    
    results = []
    for i, (name, config) in enumerate(SOURCES_TO_TEST.items(), 1):
        print(f"[{i}/{len(SOURCES_TO_TEST)}] Test de {name}...", end=" ")
        result = test_source(name, config)
        results.append(result)
        print(result["status"])
        
        # Délai entre tests pour être respectueux
        if i < len(SOURCES_TO_TEST):
            time.sleep(2)
    
    print_results(results)
    
    # Export JSON optionnel
    # try:
    #     import json
    #     with open("source_test_results.json", "w", encoding="utf-8") as f:
    #         json.dump(results, f, indent=2, ensure_ascii=False)
    #     print(f"\n💾 Résultats sauvegardés dans: source_test_results.json")
    # except Exception as e:
    #     print(f"\n⚠️ Impossible de sauvegarder les résultats: {e}")


if __name__ == "__main__":
    main()