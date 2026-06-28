from ai_pipelines.text_cleaner import (
    clean_text,
    collapse_whitespace,
    fix_hyphenation,
    normalize_unicode,
    remove_repeated_headers_footers,
)


# ---------------------------------------------------------------------------
# fix_hyphenation
# ---------------------------------------------------------------------------


class TestFixHyphenation:

    def test_mot_coupe_en_fin_de_ligne(self):
        assert fix_hyphenation("sea-\nrch") == "search"

    def test_mot_coupe_avec_espaces_autour_du_saut(self):
        assert fix_hyphenation("algo-  \n  rithm") == "algorithm"

    def test_texte_sans_coupure_inchange(self):
        text = "un texte normal sans coupure"
        assert fix_hyphenation(text) == text

    def test_tiret_en_milieu_de_ligne_inchange(self):
        text = "state-of-the-art model"
        assert fix_hyphenation(text) == text

    def test_plusieurs_coupures_independantes_dans_le_meme_texte(self):
        # Deux coupures indépendantes (pas chaînées) → toutes deux résolues en un passage
        text = "ap-\nprenti et al-\ngorithm"
        assert fix_hyphenation(text) == "apprenti et algorithm"


# ---------------------------------------------------------------------------
# remove_repeated_headers_footers
# ---------------------------------------------------------------------------


class TestRemoveRepeatedHeadersFooters:

    def test_moins_de_trois_pages_retourne_tel_quel(self):
        pages = ["page 1", "page 2"]
        assert remove_repeated_headers_footers(pages) == pages

    def test_header_present_sur_toutes_les_pages_supprime(self):
        header = "Titre du document"
        pages = [f"{header}\nContenu {i}" for i in range(5)]
        result = remove_repeated_headers_footers(pages)
        for page in result:
            assert header not in page

    def test_footer_present_sur_toutes_les_pages_supprime(self):
        footer = "Page confidentielle"
        pages = [f"Contenu {i}\n{footer}" for i in range(5)]
        result = remove_repeated_headers_footers(pages)
        for page in result:
            assert footer not in page

    def test_ligne_non_repetee_conservee(self):
        # 6 pages, threshold=0.5 → min_count=3 ; le contenu unique (1 fois) est conservé
        header = "En-tête"
        pages = [f"{header}\nContenu unique {i}" for i in range(6)]
        result = remove_repeated_headers_footers(pages, threshold=0.5)
        for i, page in enumerate(result):
            assert f"Contenu unique {i}" in page

    def test_threshold_50_percent(self):
        # Apparaît sur 3 pages sur 4 (75%) → supprimé avec threshold=0.5
        repeated = "Ligne répétée"
        pages = [
            f"{repeated}\nA",
            f"{repeated}\nB",
            f"{repeated}\nC",
            "Autre en-tête\nD",
        ]
        result = remove_repeated_headers_footers(pages, threshold=0.5)
        assert repeated not in result[0]

    def test_liste_vide_retourne_liste_vide(self):
        assert remove_repeated_headers_footers([]) == []


# ---------------------------------------------------------------------------
# normalize_unicode
# ---------------------------------------------------------------------------


class TestNormalizeUnicode:

    def test_ligature_fi_decomposee(self):
        assert normalize_unicode("ﬁle") == "file"

    def test_espace_insecable_remplace(self):
        assert normalize_unicode("mot\xa0mot") == "mot mot"

    def test_texte_ascii_inchange(self):
        text = "Hello world 123"
        assert normalize_unicode(text) == text

    def test_plusieurs_ligatures(self):
        result = normalize_unicode("ﬁnd the ﬂow")
        assert result == "find the flow"


# ---------------------------------------------------------------------------
# collapse_whitespace
# ---------------------------------------------------------------------------


class TestCollapseWhitespace:

    def test_espaces_multiples_reduits_a_un(self):
        assert collapse_whitespace("un   texte") == "un texte"

    def test_tabulation_remplacee_par_espace(self):
        assert collapse_whitespace("col1\tcol2") == "col1 col2"

    def test_trois_sauts_de_ligne_reduits_a_deux(self):
        result = collapse_whitespace("para1\n\n\n\npara2")
        assert result == "para1\n\npara2"

    def test_espaces_en_debut_et_fin_supprimes(self):
        assert collapse_whitespace("  texte  ") == "texte"

    def test_espaces_autour_des_sauts_de_ligne_supprimes(self):
        result = collapse_whitespace("ligne1 \n ligne2")
        assert result == "ligne1\nligne2"

    def test_texte_propre_inchange(self):
        text = "Un texte\ndéjà propre."
        assert collapse_whitespace(text) == text


# ---------------------------------------------------------------------------
# clean_text
# ---------------------------------------------------------------------------


class TestCleanText:

    def test_texte_vide_retourne_chaine_vide(self):
        assert clean_text("") == ""

    def test_texte_propre_inchange(self):
        text = "Un texte déjà propre."
        assert clean_text(text) == text

    def test_applique_toutes_les_transformations(self):
        raw = "ﬁnd\xa0the al-\ngorithm   here\n\n\n\nend"
        result = clean_text(raw)
        assert result == "find the algorithm here\n\nend"

    def test_coupure_et_unicode_combines(self):
        # Une seule coupure (pas chaînée) + espace insécable
        raw = "appren-\ntissage\xa0automatique"
        assert clean_text(raw) == "apprentissage automatique"
