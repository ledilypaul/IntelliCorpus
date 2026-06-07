import json
from pathlib import Path

from scrapers.arxiv import parser_arxiv
from scrapers.hal import parser_hal
from scrapers.pubmed import format_pubmed_data, get_authors

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture(filename: str) -> str:
    return (FIXTURES_DIR / filename).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# parser_arxiv
# ---------------------------------------------------------------------------


class TestParserArxiv:

    def test_returns_one_entry_per_feed_entry(self):
        feed = _load_fixture("arxiv_sample.xml")
        result = parser_arxiv(feed)
        assert len(result) == 2

    def test_entry_has_expected_fields(self):
        feed = _load_fixture("arxiv_sample.xml")
        entry = parser_arxiv(feed)[0]
        assert entry["id"] == "http://arxiv.org/abs/2101.00001v1"
        assert entry["title"] == "Sample Paper About Neural Networks"
        assert entry["summary"] == "This is a sample abstract for testing the arXiv parser."
        assert entry["published_at"] == "2021-01-01T00:00:00Z"
        assert entry["updated"] == "2021-01-02T00:00:00Z"

    def test_source_is_arxiv(self):
        feed = _load_fixture("arxiv_sample.xml")
        for entry in parser_arxiv(feed):
            assert entry["source"] == "arxiv"

    def test_authors_extracted_as_name_list(self):
        feed = _load_fixture("arxiv_sample.xml")
        entry = parser_arxiv(feed)[0]
        assert entry["authors"] == ["Jane Doe", "John Smith"]

    def test_pdf_url_extracted_from_pdf_link(self):
        feed = _load_fixture("arxiv_sample.xml")
        entry = parser_arxiv(feed)[0]
        assert entry["pdf_url"] == "http://arxiv.org/pdf/2101.00001v1"

    def test_empty_feed_returns_empty_list(self):
        empty_feed = '<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>'
        assert parser_arxiv(empty_feed) == []


# ---------------------------------------------------------------------------
# parser_hal
# ---------------------------------------------------------------------------


class TestParserHal:

    def test_returns_one_entry_per_doc(self):
        feed = _load_fixture("hal_sample.json")
        result = parser_hal(feed)
        assert len(result) == 2

    def test_accepts_json_string(self):
        feed = _load_fixture("hal_sample.json")
        result = parser_hal(feed)
        assert result[0]["id"] == "hal-00000001"

    def test_accepts_already_parsed_dict(self):
        feed_dict = json.loads(_load_fixture("hal_sample.json"))
        result = parser_hal(feed_dict)
        assert result[0]["id"] == "hal-00000001"

    def test_entry_has_expected_fields(self):
        feed = _load_fixture("hal_sample.json")
        entry = parser_hal(feed)[0]
        assert entry["title"] == ["Sample HAL Title One"]
        assert entry["summary"] == ["This is the first sample HAL abstract."]
        assert entry["published_at"] == "2021-01-01"
        assert entry["uri"] == "https://hal.science/hal-00000001"

    def test_source_is_hal(self):
        feed = _load_fixture("hal_sample.json")
        for entry in parser_hal(feed):
            assert entry["source"] == "hal"

    def test_authors_extracted_as_list(self):
        feed = _load_fixture("hal_sample.json")
        entry = parser_hal(feed)[0]
        assert entry["authors"] == ["Jane Doe", "John Smith"]

    def test_missing_files_handled(self):
        feed = _load_fixture("hal_sample.json")
        entry = parser_hal(feed)[1]
        assert entry["pdf_url"] == []

    def test_empty_docs_returns_empty_list(self):
        empty_feed = json.dumps({"response": {"docs": []}})
        assert parser_hal(empty_feed) == []


# ---------------------------------------------------------------------------
# get_authors
# ---------------------------------------------------------------------------


class TestGetAuthors:

    def test_combines_forename_and_lastname(self):
        authors_list = {"Author": [{"ForeName": "Jane", "LastName": "Doe"}]}
        assert get_authors(authors_list) == ["Jane Doe"]

    def test_handles_missing_forename(self):
        authors_list = {"Author": [{"LastName": "Doe"}]}
        assert get_authors(authors_list) == ["Doe"]

    def test_skips_authors_with_no_name(self):
        authors_list = {"Author": [{"ForeName": "", "LastName": ""}]}
        assert get_authors(authors_list) == []

    def test_empty_authors_list(self):
        assert get_authors({}) == []


# ---------------------------------------------------------------------------
# format_pubmed_data
# ---------------------------------------------------------------------------


class TestFormatPubmedData:

    def test_returns_one_entry_per_article(self):
        xml = _load_fixture("pubmed_sample.xml")
        result = format_pubmed_data([xml])
        assert len(result) == 2

    def test_entry_has_expected_fields(self):
        xml = _load_fixture("pubmed_sample.xml")
        entry = format_pubmed_data([xml])[0]
        assert entry["title"] == "Sample PubMed Title"
        assert entry["summary"] == "This is a sample PubMed abstract."
        assert entry["id"] == "https://pubmed.ncbi.nlm.nih.gov/12345678/"

    def test_source_is_pubmed(self):
        xml = _load_fixture("pubmed_sample.xml")
        for entry in format_pubmed_data([xml]):
            assert entry["source"] == "PubMed"

    def test_pdf_url_is_none(self):
        xml = _load_fixture("pubmed_sample.xml")
        for entry in format_pubmed_data([xml]):
            assert entry["pdf_url"] is None

    def test_authors_extracted(self):
        xml = _load_fixture("pubmed_sample.xml")
        entry = format_pubmed_data([xml])[0]
        assert entry["authors"] == ["Jane Doe", "John Smith"]

    def test_handles_multiple_xml_batches(self):
        xml = _load_fixture("pubmed_sample.xml")
        result = format_pubmed_data([xml, xml])
        assert len(result) == 4
