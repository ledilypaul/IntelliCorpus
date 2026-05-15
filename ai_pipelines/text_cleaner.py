import re
import unicodedata
from collections import Counter


def fix_hyphenation(text: str) -> str:
    """Rejoin words split at end of line: sea-\nrch -> search

    Args:
        text (str): Text to clean

    Returns:
        str: Cleaned text
    """
    # Match: a word, a hyphen, a newline, the rest of the word
    # \w+  : one or more word characters (letters, digits)
    # -    : literal hyphen
    # \n   : newline
    # \w+  : continuation of the word
    pattern = r"(\w+)-\s*\n\s*(\w+)"
    return re.sub(pattern, r"\1\2", text)


def remove_repeated_headers_footers(
    pages: list[str],
    threshold: float = 0.5,
    n_lines: int = 2
) -> list[str]:
    """Detect and remove recurring headers and footers.

    Args:
        pages: list of page text strings
        threshold: minimum ratio of pages where a line must appear (0.5 = 50%)
        n_lines: number of lines to inspect at the top and bottom of each page
    """
    if len(pages) < 3:
        # Not enough pages to reliably detect repetition
        return pages

    # 1. Collect first and last lines of each page
    header_candidates = []
    footer_candidates = []

    for page in pages:
        lines = [l.strip() for l in page.split("\n") if l.strip()]
        if not lines:
            continue
        header_candidates.extend(lines[:n_lines])
        footer_candidates.extend(lines[-n_lines:])

    # 2. Count occurrences
    header_counts = Counter(header_candidates)
    footer_counts = Counter(footer_candidates)

    # 3. Identify lines appearing in more than threshold of pages
    min_count = int(len(pages) * threshold)
    repeated_headers = {line for line, count in header_counts.items() if count >= min_count}
    repeated_footers = {line for line, count in footer_counts.items() if count >= min_count}

    # 4. Remove those lines from each page
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
    """Normalize unicode characters to their canonical form.

    Args:
        text (str): Text to normalize

    Returns:
        str: Normalized text
    """
    # NFKC = Normalization Form Compatibility Composition
    # Decomposes then recomposes characters into their canonical form
    # Ligatures like 'ﬁ' become 'fi'
    text = unicodedata.normalize("NFKC", text)

    # Replace non-breaking spaces with regular spaces
    text = text.replace("\xa0", " ")

    return text

def collapse_whitespace(text: str) -> str:
    """Collapse redundant whitespace while preserving paragraph breaks.

    Args:
        text (str): Text to clean

    Returns:
        str: Cleaned text
    """
    # 1. Replace tabs and multiple spaces with a single space
    #    [ \t]+ = one space or tab, one or more times
    text = re.sub(r"[ \t]+", " ", text)

    # 2. More than 2 consecutive newlines → max 2 (preserves paragraphs)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 3. Strip spaces at start/end of lines
    text = re.sub(r" *\n *", "\n", text)

    # 4. Global strip
    return text.strip()

def clean_text(raw: str) -> str:
    """Apply all cleaning steps in order."""
    text = normalize_unicode(raw)
    text = fix_hyphenation(text)
    text = collapse_whitespace(text)
    return text
