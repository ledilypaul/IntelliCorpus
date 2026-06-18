from unittest.mock import MagicMock, patch

from ai_pipelines.ingest import _build_chunk_records, ingest_document, ingest_pending_documents
from models.postgres.corpus_schema import document_table


def _document():
    return {"id": "doc-1", "minio_path": "path/to/doc.pdf", "title": "Sample Paper"}


# ---------------------------------------------------------------------------
# _build_chunk_records
# ---------------------------------------------------------------------------


class TestBuildChunkRecords:

    def test_empty_chunks_returns_empty_list(self):
        assert _build_chunk_records("doc-1", [], []) == []

    def test_pairs_each_chunk_with_its_vector(self):
        chunks = ["first chunk", "second chunk"]
        vectors = [[0.1, 0.2], [0.3, 0.4]]
        records = _build_chunk_records("doc-1", chunks, vectors)
        assert records[0]["content"] == "first chunk"
        assert records[0]["embedding"] == [0.1, 0.2]
        assert records[1]["content"] == "second chunk"
        assert records[1]["embedding"] == [0.3, 0.4]

    def test_ids_are_unique_per_document_and_index(self):
        records = _build_chunk_records("doc-1", ["a", "b"], [[0.1], [0.2]])
        assert records[0]["id"] == "doc-1:0"
        assert records[1]["id"] == "doc-1:1"

    def test_chunk_index_matches_position(self):
        records = _build_chunk_records("doc-1", ["a", "b", "c"], [[0.1], [0.2], [0.3]])
        assert [r["chunk_index"] for r in records] == [0, 1, 2]

    def test_document_id_set_on_every_record(self):
        records = _build_chunk_records("doc-42", ["a"], [[0.1]])
        assert records[0]["document_id"] == "doc-42"

    def test_token_count_is_computed(self):
        records = _build_chunk_records("doc-1", ["hello world"], [[0.1]])
        assert records[0]["token_count"] > 0


# ---------------------------------------------------------------------------
# ingest_document
# ---------------------------------------------------------------------------


class TestIngestDocument:

    @patch("ai_pipelines.ingest.update_rag_status")
    @patch("ai_pipelines.ingest.extract_pdf")
    def test_extraction_failure_marks_document_failed(self, mock_extract, mock_update_status):
        mock_extract.return_value = {"status": "failed", "error": "corrupted pdf"}
        engine = MagicMock()

        result = ingest_document(engine, _document())

        assert result == "failed"
        mock_update_status.assert_called_once_with(engine, document_table, "doc-1", "failed")

    @patch("ai_pipelines.ingest.embed_batch")
    @patch("ai_pipelines.ingest.split_text")
    @patch("ai_pipelines.ingest.extract_pdf")
    def test_extraction_failure_skips_chunking_and_embedding(self, mock_extract, mock_split, mock_embed):
        mock_extract.return_value = {"status": "failed", "error": "corrupted pdf"}
        with patch("ai_pipelines.ingest.update_rag_status"):
            ingest_document(MagicMock(), _document())

        mock_split.assert_not_called()
        mock_embed.assert_not_called()

    @patch("ai_pipelines.ingest.update_rag_status")
    @patch("ai_pipelines.ingest.split_text")
    @patch("ai_pipelines.ingest.extract_pdf")
    def test_no_chunks_produced_marks_document_failed(self, mock_extract, mock_split, mock_update_status):
        mock_extract.return_value = {"status": "ok", "cleaned_text": "   "}
        mock_split.return_value = []
        engine = MagicMock()

        result = ingest_document(engine, _document())

        assert result == "failed"
        mock_update_status.assert_called_once_with(engine, document_table, "doc-1", "failed")

    @patch("ai_pipelines.ingest.update_rag_status")
    @patch("ai_pipelines.ingest.upsert_chunks")
    @patch("ai_pipelines.ingest.embed_batch")
    @patch("ai_pipelines.ingest.split_text")
    @patch("ai_pipelines.ingest.extract_pdf")
    def test_successful_pipeline_marks_document_embedded(
        self, mock_extract, mock_split, mock_embed, mock_upsert, mock_update_status
    ):
        mock_extract.return_value = {"status": "ok", "cleaned_text": "some cleaned text"}
        mock_split.return_value = ["chunk one", "chunk two"]
        mock_embed.return_value = [[0.1, 0.2], [0.3, 0.4]]
        engine = MagicMock()

        result = ingest_document(engine, _document())

        assert result == "embedded"
        mock_update_status.assert_called_once_with(engine, document_table, "doc-1", "embedded")

    @patch("ai_pipelines.ingest.update_rag_status")
    @patch("ai_pipelines.ingest.upsert_chunks")
    @patch("ai_pipelines.ingest.embed_batch")
    @patch("ai_pipelines.ingest.split_text")
    @patch("ai_pipelines.ingest.extract_pdf")
    def test_successful_pipeline_stores_built_chunk_records(
        self, mock_extract, mock_split, mock_embed, mock_upsert, mock_update_status
    ):
        mock_extract.return_value = {"status": "ok", "cleaned_text": "some cleaned text"}
        mock_split.return_value = ["chunk one", "chunk two"]
        mock_embed.return_value = [[0.1, 0.2], [0.3, 0.4]]

        ingest_document(MagicMock(), _document())

        stored_chunks = mock_upsert.call_args[0][0]
        assert len(stored_chunks) == 2
        assert stored_chunks[0]["document_id"] == "doc-1"
        assert stored_chunks[0]["content"] == "chunk one"
        assert stored_chunks[0]["embedding"] == [0.1, 0.2]

    @patch("ai_pipelines.ingest.update_rag_status")
    @patch("ai_pipelines.ingest.upsert_chunks")
    @patch("ai_pipelines.ingest.embed_batch")
    @patch("ai_pipelines.ingest.split_text")
    @patch("ai_pipelines.ingest.extract_pdf")
    def test_chunks_are_embedded_before_being_stored(
        self, mock_extract, mock_split, mock_embed, mock_upsert, mock_update_status
    ):
        mock_extract.return_value = {"status": "ok", "cleaned_text": "some cleaned text"}
        mock_split.return_value = ["chunk one", "chunk two"]
        mock_embed.return_value = [[0.1, 0.2], [0.3, 0.4]]

        ingest_document(MagicMock(), _document())

        mock_embed.assert_called_once_with(["chunk one", "chunk two"])


# ---------------------------------------------------------------------------
# ingest_pending_documents
# ---------------------------------------------------------------------------


class TestIngestPendingDocuments:

    @patch("ai_pipelines.ingest.get_articles_with_pdf")
    def test_no_documents_returns_zero_counts(self, mock_get_articles):
        mock_get_articles.return_value = []

        result = ingest_pending_documents(engine=MagicMock())

        assert result == {"embedded": 0, "failed": 0}

    @patch("ai_pipelines.ingest.ingest_document")
    @patch("ai_pipelines.ingest.get_articles_with_pdf")
    def test_counts_successes_and_failures(self, mock_get_articles, mock_ingest_document):
        mock_get_articles.return_value = [
            {"id": "doc-1", "title": "A", "minio_path": "a.pdf"},
            {"id": "doc-2", "title": "B", "minio_path": "b.pdf"},
            {"id": "doc-3", "title": "C", "minio_path": "c.pdf"},
        ]
        mock_ingest_document.side_effect = ["embedded", "embedded", "failed"]

        result = ingest_pending_documents(engine=MagicMock())

        assert result == {"embedded": 2, "failed": 1}
        assert mock_ingest_document.call_count == 3

    @patch("ai_pipelines.ingest.update_rag_status")
    @patch("ai_pipelines.ingest.ingest_document")
    @patch("ai_pipelines.ingest.get_articles_with_pdf")
    def test_exception_in_one_document_does_not_stop_the_batch(
        self, mock_get_articles, mock_ingest_document, mock_update_status
    ):
        mock_get_articles.return_value = [
            {"id": "doc-1", "title": "A", "minio_path": "a.pdf"},
            {"id": "doc-2", "title": "B", "minio_path": "b.pdf"},
        ]
        mock_ingest_document.side_effect = [RuntimeError("boom"), "embedded"]

        result = ingest_pending_documents(engine=MagicMock())

        assert result == {"embedded": 1, "failed": 1}
        assert mock_ingest_document.call_count == 2

    @patch("ai_pipelines.ingest.get_db_engine")
    @patch("ai_pipelines.ingest.get_articles_with_pdf")
    def test_uses_default_engine_when_none_provided(self, mock_get_articles, mock_get_db_engine):
        mock_get_articles.return_value = []
        mock_get_db_engine.return_value = MagicMock()

        ingest_pending_documents()

        mock_get_db_engine.assert_called_once()
