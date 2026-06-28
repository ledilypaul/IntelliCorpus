import uuid

from processing.cleaning_data import generate_deterministic_uuid, normalize_data
import polars as pl


# ---------------------------------------------------------------------------
# generate_deterministic_uuid
# ---------------------------------------------------------------------------


class TestGenerateDeterministicUuid:

    def test_uuid_matches_uuid5_of_url(self):
        url = "http://arxiv.org/abs/1234"
        df = pl.DataFrame({"id": [url]})
        result = generate_deterministic_uuid(df)
        expected = str(uuid.uuid5(uuid.NAMESPACE_URL, url))
        assert result["id"][0] == expected

    def test_original_url_preserved_in_uri_column(self):
        url = "http://arxiv.org/abs/1234"
        df = pl.DataFrame({"id": [url]})
        result = generate_deterministic_uuid(df)
        assert result["uri"][0] == url

    def test_missing_url_column_returns_unchanged(self):
        df = pl.DataFrame({"title": ["A title"]})
        result = generate_deterministic_uuid(df, url_column="id")
        assert "id" not in result.columns
        assert "uri" not in result.columns


# ---------------------------------------------------------------------------
# normalize_data
# ---------------------------------------------------------------------------


class TestNormalizeData:

    def test_empty_input_returns_empty_list(self):
        assert normalize_data([], "arXiv") == []

    def test_uuid_is_deterministic_across_calls(self):
        raw = [{"id": "http://arxiv.org/abs/1234", "title": "A title"}]
        result1 = normalize_data(raw, "arXiv")
        result2 = normalize_data(raw, "arXiv")
        assert result1[0]["id"] == result2[0]["id"]

    def test_uuid_matches_manual_uuid5_computation(self):
        url = "http://arxiv.org/abs/1234"
        raw = [{"id": url, "title": "A title"}]
        result = normalize_data(raw, "arXiv")
        expected = str(uuid.uuid5(uuid.NAMESPACE_URL, url))
        assert result[0]["id"] == expected

    def test_different_urls_produce_different_uuids(self):
        raw = [
            {"id": "http://arxiv.org/abs/1", "title": "Paper A"},
            {"id": "http://arxiv.org/abs/2", "title": "Paper B"},
        ]
        result = normalize_data(raw, "arXiv")
        assert result[0]["id"] != result[1]["id"]

    def test_calling_twice_on_same_raw_data_is_idempotent(self):
        raw = [{
            "id": "http://arxiv.org/abs/42",
            "title": "A title",
            "published_at": "2021-01-01T00:00:00Z",
            "updated": "should be dropped",
        }]
        result1 = normalize_data(raw, "arXiv", date_columns=["published_at"], columns_drop=["updated"])
        result2 = normalize_data(raw, "arXiv", date_columns=["published_at"], columns_drop=["updated"])
        assert result1 == result2

    def test_original_url_preserved_as_uri(self):
        url = "http://arxiv.org/abs/42"
        raw = [{"id": url, "title": "A title"}]
        result = normalize_data(raw, "arXiv")
        assert result[0]["uri"] == url

    def test_source_column_set(self):
        raw = [{"id": "http://example.com/1", "title": "A title"}]
        result = normalize_data(raw, "arXiv")
        assert result[0]["source"] == "arXiv"

    def test_columns_dropped(self):
        raw = [{"id": "http://example.com/1", "title": "A title", "extra": "drop me"}]
        result = normalize_data(raw, "arXiv", columns_drop=["extra"])
        assert "extra" not in result[0]
