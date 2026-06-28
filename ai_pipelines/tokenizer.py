import tiktoken
from functools import lru_cache

@lru_cache(maxsize=8)
def _get_encoding(encoding_name: str):
    """Renvoie l'encodeur tiktoken mis en RAM 

    Args:
        encoding_name (str): name of the encoder
    """
    return tiktoken.get_encoding(encoding_name)

def encode_text(text: str, encoding_name: str = "cl100k_base") -> list[int]:
    encoding = _get_encoding(encoding_name)
    return encoding.encode(text)

def count_tokens(string: str, encoding_name: str) -> int:
    """Renvoie le nombre de tokens dans une chaîne de texte."""
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(string))

def decode_tokens(tokens: list[int], encoding_name: str ="cl100k_base") -> str:
    """utile pour overlap, reconstruire text a partir de token

    Args:
        tokens (list[int]): matrice

    Returns:
        str: text traduit
    """
    encoding = _get_encoding(encoding_name)
    return encoding.decode(tokens)

