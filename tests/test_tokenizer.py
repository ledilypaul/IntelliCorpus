from ai_pipelines.tokenizer import count_tokens, decode_tokens, encode_text

ENCODING = "cl100k_base"


# ---------------------------------------------------------------------------
# encode_text
# ---------------------------------------------------------------------------


class TestEncodeText:

    def test_texte_vide_retourne_liste_vide(self):
        assert encode_text("", ENCODING) == []

    def test_retourne_une_liste_d_entiers(self):
        result = encode_text("bonjour", ENCODING)
        assert isinstance(result, list)
        assert all(isinstance(t, int) for t in result)

    def test_texte_non_vide_produit_des_tokens(self):
        result = encode_text("hello world", ENCODING)
        assert len(result) > 0

    def test_textes_differents_produisent_tokens_differents(self):
        assert encode_text("chat", ENCODING) != encode_text("chien", ENCODING)

    def test_round_trip_encode_decode(self):
        text = "Le modèle apprend des représentations."
        tokens = encode_text(text, ENCODING)
        assert decode_tokens(tokens, ENCODING) == text


# ---------------------------------------------------------------------------
# count_tokens
# ---------------------------------------------------------------------------


class TestCountTokens:

    def test_texte_vide_retourne_zero(self):
        assert count_tokens("", ENCODING) == 0

    def test_texte_simple_retourne_entier_positif(self):
        assert count_tokens("hello", ENCODING) > 0

    def test_coherent_avec_encode_text(self):
        text = "Un texte quelconque pour le test."
        assert count_tokens(text, ENCODING) == len(encode_text(text, ENCODING))

    def test_texte_long_plus_de_tokens_que_texte_court(self):
        short = "bonjour"
        long = "bonjour " * 50
        assert count_tokens(long, ENCODING) > count_tokens(short, ENCODING)


# ---------------------------------------------------------------------------
# decode_tokens
# ---------------------------------------------------------------------------


class TestDecodeTokens:

    def test_liste_vide_retourne_chaine_vide(self):
        assert decode_tokens([], ENCODING) == ""

    def test_round_trip_decode_encode(self):
        text = "Apprentissage automatique et traitement du langage."
        tokens = encode_text(text, ENCODING)
        assert decode_tokens(tokens, ENCODING) == text

    def test_tranche_de_tokens_retourne_sous_texte(self):
        text = "hello world"
        tokens = encode_text(text, ENCODING)
        # Le premier token doit décoder en quelque chose de non-vide
        assert decode_tokens(tokens[:1], ENCODING) != ""
