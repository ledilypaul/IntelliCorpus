from unittest.mock import MagicMock

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.dialects.postgresql.dml import OnConflictDoNothing, OnConflictDoUpdate

from database.postgres.crud import upsert_data

metadata = MetaData()
sample_table = Table(
    "sample",
    metadata,
    Column("id", String, primary_key=True),
    Column("title", String),
    Column("summary", String),
)


def _mock_engine():
    """Build a fake engine whose `begin()` context manager yields a fake connection.

    `upsert_data` only ever calls `engine.begin()` then `conn.execute(stmt)`,
    so we don't need a real database to verify which statement gets built.
    """
    engine = MagicMock()
    conn = MagicMock()
    engine.begin.return_value.__enter__.return_value = conn
    return engine, conn


def _executed_statement(conn):
    return conn.execute.call_args[0][0]


# ---------------------------------------------------------------------------
# upsert_data
# ---------------------------------------------------------------------------


class TestUpsertData:

    def test_executes_statement_once(self):
        engine, conn = _mock_engine()
        data = [{"id": "1", "title": "T", "summary": "S"}]
        upsert_data(data, ["id"], sample_table, engine)
        conn.execute.assert_called_once()

    def test_conflict_with_extra_columns_generates_do_update(self):
        engine, conn = _mock_engine()
        data = [{"id": "1", "title": "T", "summary": "S"}]
        upsert_data(data, ["id"], sample_table, engine)

        clause = _executed_statement(conn)._post_values_clause
        assert isinstance(clause, OnConflictDoUpdate)

    def test_do_update_targets_the_index_elements(self):
        engine, conn = _mock_engine()
        data = [{"id": "1", "title": "T", "summary": "S"}]
        upsert_data(data, ["id"], sample_table, engine)

        clause = _executed_statement(conn)._post_values_clause
        assert clause.inferred_target_elements == ["id"]

    def test_do_update_excludes_index_columns_from_set_clause(self):
        engine, conn = _mock_engine()
        data = [{"id": "1", "title": "T", "summary": "S"}]
        upsert_data(data, ["id"], sample_table, engine)

        clause = _executed_statement(conn)._post_values_clause
        updated_columns = {name for name, _ in clause.update_values_to_set}
        assert updated_columns == {"title", "summary"}
        assert "id" not in updated_columns

    def test_conflict_with_all_columns_indexed_generates_do_nothing(self):
        # update_dict ne contient que les colonnes de la table absentes de
        # index_elements ; s'il n'y en a aucune → on_conflict_do_nothing
        engine, conn = _mock_engine()
        data = [{"id": "1", "title": "T", "summary": "S"}]
        upsert_data(data, ["id", "title", "summary"], sample_table, engine)

        clause = _executed_statement(conn)._post_values_clause
        assert isinstance(clause, OnConflictDoNothing)

    def test_do_nothing_targets_the_index_elements(self):
        engine, conn = _mock_engine()
        data = [{"id": "1", "title": "T", "summary": "S"}]
        upsert_data(data, ["id", "title", "summary"], sample_table, engine)

        clause = _executed_statement(conn)._post_values_clause
        assert clause.inferred_target_elements == ["id", "title", "summary"]

    def test_composite_index_elements_supported(self):
        engine, conn = _mock_engine()
        data = [{"id": "1", "title": "T", "summary": "S"}]
        upsert_data(data, ["id", "title"], sample_table, engine)

        clause = _executed_statement(conn)._post_values_clause
        assert clause.inferred_target_elements == ["id", "title"]
        updated_columns = {name for name, _ in clause.update_values_to_set}
        assert updated_columns == {"summary"}
