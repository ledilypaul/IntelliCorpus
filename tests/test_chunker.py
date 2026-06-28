import pytest
from ai_pipelines.chunker import (
    CHUNK_SIZE,
    ENCODING_NAME,
    OVERLAP_SIZE,
    _add_overlap,
    _merge_small_chunks,
    _split_recursive,
    split_text,
)
from ai_pipelines.tokenizer import count_tokens, decode_tokens, encode_text


def _make_text(n_approx_tokens: int) -> str:
    """Génère un texte d'exactement n tokens en tranchant via le tokenizer."""
    tokens = encode_text("hello " * (n_approx_tokens + 10), ENCODING_NAME)
    return decode_tokens(tokens[:n_approx_tokens], ENCODING_NAME)


# ---------------------------------------------------------------------------
# _split_recursive
# ---------------------------------------------------------------------------


class TestSplitRecursive:

    def test_texte_vide_retourne_liste_vide(self):
        assert _split_recursive("", ["\n\n"]) == []

    def test_texte_que_espaces_retourne_liste_vide(self):
        assert _split_recursive("   \n\n  ", ["\n\n"]) == []

    def test_texte_court_retourne_tel_quel(self):
        text = "Un texte court."
        result = _split_recursive(text, ["\n\n", "\n", ".", " "])
        assert result == [text]

    def test_tous_les_chunks_respectent_chunk_size(self):
        long_text = _make_text(2000)
        chunks = _split_recursive(long_text, ["\n\n", "\n", ".", " "])
        for chunk in chunks:
            assert count_tokens(chunk, ENCODING_NAME) <= CHUNK_SIZE

    def test_split_sur_double_saut_de_ligne(self):
        para = _make_text(300)
        text = f"{para}\n\n{para}\n\n{para}"
        # Chaque paragraphe tient seul → doit rester intact
        chunks = _split_recursive(text, ["\n\n"])
        assert len(chunks) == 3

    def test_split_brutal_sans_separateurs(self):
        long_text = _make_text(2000)
        chunks = _split_recursive(long_text, [])
        assert len(chunks) > 1
        for chunk in chunks:
            assert count_tokens(chunk, ENCODING_NAME) <= CHUNK_SIZE

    def test_aucun_chunk_vide(self):
        long_text = _make_text(1600)
        chunks = _split_recursive(long_text, ["\n\n", "\n", ".", " "])
        for chunk in chunks:
            assert chunk.strip() != ""


# ---------------------------------------------------------------------------
# _merge_small_chunks
# ---------------------------------------------------------------------------


class TestMergeSmallChunks:

    def test_liste_vide(self):
        assert _merge_small_chunks([]) == []

    def test_un_seul_chunk_retourne_tel_quel(self):
        assert _merge_small_chunks(["bonjour"]) == ["bonjour"]

    def test_deux_petits_chunks_sont_fusionnes(self):
        result = _merge_small_chunks(["bonjour", "monde"])
        assert result == ["bonjour monde"]

    def test_separator_personnalise_utilise(self):
        result = _merge_small_chunks(["bonjour", "monde"], separator="-")
        assert result == ["bonjour-monde"]

    def test_deux_grands_chunks_ne_sont_pas_fusionnes(self):
        # 600 + 600 = 1200 tokens > CHUNK_SIZE → pas de fusion
        big = _make_text(600)
        result = _merge_small_chunks([big, big])
        assert len(result) == 2

    def test_fusion_partielle_premier_petit_dernier_grand(self):
        small = _make_text(50)
        big = _make_text(790)
        # small + " " + big dépasse CHUNK_SIZE → pas de fusion
        result = _merge_small_chunks([small, big])
        assert len(result) == 2

    def test_tous_les_chunks_fusionnes_respectent_chunk_size(self):
        chunks = [_make_text(60) for _ in range(20)]
        result = _merge_small_chunks(chunks)
        for chunk in result:
            assert count_tokens(chunk, ENCODING_NAME) <= CHUNK_SIZE


# ---------------------------------------------------------------------------
# _add_overlap
# ---------------------------------------------------------------------------


class TestAddOverlap:

    def test_liste_vide(self):
        assert _add_overlap([]) == []

    def test_un_seul_chunk_inchange(self):
        chunk = "Un seul chunk."
        assert _add_overlap([chunk]) == [chunk]

    def test_premier_chunk_inchange(self):
        chunks = [_make_text(400), _make_text(400)]
        result = _add_overlap(chunks)
        assert result[0] == chunks[0]

    def test_chunk_suivant_contient_la_queue_du_precedent(self):
        chunk_a = _make_text(400)
        chunk_b = _make_text(400)
        result = _add_overlap([chunk_a, chunk_b])
        # Les derniers tokens de chunk_a doivent apparaître au début de result[1]
        prev_tokens = encode_text(chunk_a, ENCODING_NAME)
        tail_text = decode_tokens(prev_tokens[-OVERLAP_SIZE:], ENCODING_NAME)
        assert result[1].startswith(tail_text)

    def test_taille_overlap_correcte(self):
        chunk_a = _make_text(400)
        chunk_b = _make_text(400)
        result = _add_overlap([chunk_a, chunk_b])
        # result[1] = tail(150) + " " + chunk_b → ~550 tokens
        added = count_tokens(result[1], ENCODING_NAME) - count_tokens(chunk_b, ENCODING_NAME)
        assert abs(added - OVERLAP_SIZE) <= 5  # tolérance de 5 tokens (espace de séparation)


# ---------------------------------------------------------------------------
# split_text
# ---------------------------------------------------------------------------


class TestSplitText:

    def test_texte_vide(self):
        assert split_text("") == []

    def test_texte_court_un_seul_chunk(self):
        text = "Un texte court."
        result = split_text(text)
        assert len(result) == 1
        assert result[0] == text

    def test_tous_les_chunks_respectent_chunk_size(self):
        long_text = _make_text(3000)
        chunks = split_text(long_text)
        # Les chunks 2+ ont un overlap préfixé → taille max = CHUNK_SIZE + OVERLAP_SIZE
        for chunk in chunks:
            assert count_tokens(chunk, ENCODING_NAME) <= CHUNK_SIZE + OVERLAP_SIZE

    def test_aucun_chunk_vide(self):
        long_text = _make_text(2000)
        chunks = split_text(long_text)
        for chunk in chunks:
            assert chunk.strip() != ""

    def test_merge_reduit_le_nombre_de_chunks(self):
        # Des centaines de mots séparés par des espaces → le merge doit regrouper
        text = " ".join(["mot"] * 2000)
        raw = _split_recursive(text, ["\n\n", "\n", ".", " "])
        merged = split_text(text)
        assert len(merged) <= len(raw)
