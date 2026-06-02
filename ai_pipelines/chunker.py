from ai_pipelines.tokenizer import count_tokens, encode_text, decode_tokens

SEPARATORS = ["\n\n", "\n", ".", " "]
CHUNK_SIZE = 800
ENCODING_NAME = "cl100k_base"

def _split_recursive(text: str, separators: list[str]) -> list[str]:
    """
    Splitte récursivement un texte en morceaux <= CHUNK_SIZE tokens.
    Essaie chaque séparateur dans l'ordre, du plus sémantique au plus brutal.

    NB: Cette fonction ne fait PAS la fusion, elle peut renvoyer plein de petits morceaux.
    """
    # 1 Cas de base : le texte tient déjà
    if count_tokens(text, ENCODING_NAME) <= CHUNK_SIZE:
        return [text] if text.strip() else []

    # 2 Cas où on a épuisé les séparateurs : split brutal au niveau token
    if not separators:
        tokens = encode_text(text, ENCODING_NAME)
        return [
            decode_tokens(tokens[i : i + CHUNK_SIZE], ENCODING_NAME)
            for i in range(0, len(tokens), CHUNK_SIZE)
        ]

    # 3 Cas général : on prend le séparateur courant et on split
    current_sep = separators[0]
    remaining_seps = separators[1:]
    parts = text.split(current_sep)

    # 4 Pour chaque morceau, on recurse s'il est encore trop gros
    result = []
    for part in parts:
        if not part.strip():
            continue
        result.extend(_split_recursive(part, remaining_seps))

    return result


def _merge_small_chunks(chunks: list[str], separator: str = " ") -> list[str]:
    """
    Fusionne les petits morceaux adjacents tant que la somme reste <= CHUNK_SIZE.
    """
    if not chunks:
        return []

    merged = []
    current = chunks[0]

    for next_chunk in chunks[1:]:
        candidate = current + separator + next_chunk
        if count_tokens(candidate, ENCODING_NAME) <= CHUNK_SIZE:
            current = candidate
        else:
            merged.append(current)
            current = next_chunk

    merged.append(current)
    return merged


def split_text(text: str) -> list[str]:
    """Split un texte en chunks de 800 tokens.

    Args:
        text (str): texte brut à découper.

    Returns:
        list[str]: liste de chunks, chacun <= CHUNK_SIZE tokens.
    """
    raw_chunks = _split_recursive(text, SEPARATORS)
    merged_chunks = _merge_small_chunks(raw_chunks)
    return merged_chunks
