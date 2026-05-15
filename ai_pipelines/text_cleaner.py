import re
import unicodedata
from collections import Counter


def fix_hyphenation(text: str) -> str:
    """Rejoin the words that were split at the end of a line sea-\nrch -> search

    Args:
        text (str): Text need to be clean

    Returns:
        str: Cleaned text
    """
    # Match : un mot, un tiret, un saut de ligne, un autre mot
    # \w+   : un ou plusieurs caractères de mot (lettres, chiffres)
    # -     : le tiret littéral
    # \n    : un saut de ligne
    # \w+   : la suite du mot
    pattern = r"(\w+)-\s*\n\s*(\w+)"
    return re.sub(pattern, r"\1\2", text)


def remove_repeated_headers_footers(
    pages: list[str], 
    threshold: float = 0.5,
    n_lines: int = 2
) -> list[str]:
    """Détecte et supprime les en-têtes/pieds de page récurrents.
    
    Args:
        pages: liste du texte de chaque page
        threshold: ratio min de pages où la ligne doit apparaître (0.5 = 50%)
        n_lines: nombre de lignes à examiner en haut et en bas de chaque page
    """
    if len(pages) < 3:
        # Pas assez de pages pour détecter une répétition fiable
        return pages
    
    # 1. Collecter les premières et dernières lignes de chaque page
    header_candidates = []
    footer_candidates = []
    
    for page in pages:
        lines = [l.strip() for l in page.split("\n") if l.strip()]
        if not lines:
            continue
        header_candidates.extend(lines[:n_lines])
        footer_candidates.extend(lines[-n_lines:])
    
    # 2. Compter les occurrences
    header_counts = Counter(header_candidates)
    footer_counts = Counter(footer_candidates)
    
    # 3. Identifier les lignes qui apparaissent dans >threshold des pages
    min_count = int(len(pages) * threshold)
    repeated_headers = {line for line, count in header_counts.items() if count >= min_count}
    repeated_footers = {line for line, count in footer_counts.items() if count >= min_count}
    
    # 4. Supprimer ces lignes de chaque page
    cleaned_pages = []
    for page in pages:
        cleaned_lines = [
            line for line in page.split("\n")
            if line.strip() not in repeated_headers
            and line.strip() not in repeated_footers
        ]
        cleaned_pages.append("\n".join(cleaned_lines))
    
    return cleaned_pages

def normalize_unicode(text: str) -> str:
    """Normalise les ligatures, espaces insécables, etc."""
    # NFKC = Normalisation Form Compatibility Composition
    # Décompose puis recompose les caractères en leur forme canonique
    # Les ligatures comme 'ﬁ' deviennent 'fi'
    text = unicodedata.normalize("NFKC", text)
    
    # Remplace les espaces insécables par des espaces normaux
    text = text.replace("\xa0", " ")
    
    return text

def collapse_whitespace(text: str) -> str:
    """Réduit les espaces multiples et les sauts de ligne abusifs."""
    # 1. Remplace les tabulations et espaces multiples par un seul espace
    #    [ \t]+ = un espace ou tabulation, une ou plusieurs fois
    text = re.sub(r"[ \t]+", " ", text)
    
    # 2. Plus de 2 sauts de ligne consécutifs → max 2 (préserve paragraphes)
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    # 3. Espaces en début/fin de ligne
    text = re.sub(r" *\n *", "\n", text)
    
    # 4. Strip global
    return text.strip()

def clean_text(raw: str) -> str:
    """Orchestrateur : applique toutes les étapes dans le bon ordre."""
    text = normalize_unicode(raw)
    text = fix_hyphenation(text)
    text = collapse_whitespace(text)
    return text