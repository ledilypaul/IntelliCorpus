import math

import pytest
from ai_pipelines.embedders import EMBEDDING_DIM, _get_model, embed, embed_batch


def _norm(vector: list[float]) -> float:
    return math.sqrt(sum(x ** 2 for x in vector))


# ---------------------------------------------------------------------------
# _get_model  (singleton)
# ---------------------------------------------------------------------------


class TestGetModel:

    def test_returns_same_instance_on_every_call(self):
        assert _get_model() is _get_model()


# ---------------------------------------------------------------------------
# embed_batch
# ---------------------------------------------------------------------------


class TestEmbedBatch:

    def test_empty_list_returns_empty_list(self):
        assert embed_batch([]) == []

    def test_returns_as_many_vectors_as_texts(self):
        texts = ["hello", "world", "machine learning"]
        result = embed_batch(texts)
        assert len(result) == len(texts)

    def test_each_vector_has_correct_dimension(self):
        result = embed_batch(["some text"])
        assert len(result[0]) == EMBEDDING_DIM

    def test_each_element_is_a_float(self):
        result = embed_batch(["test"])
        assert all(isinstance(x, float) for x in result[0])

    def test_normalize_true_yields_unit_norm(self):
        result = embed_batch(["normalized text"], normalize=True)
        assert math.isclose(_norm(result[0]), 1.0, abs_tol=1e-5)

    def test_normalize_false_does_not_raise(self):
        # all-MiniLM-L6-v2 produces near-unit vectors natively;
        # we just verify the parameter is accepted without error.
        result = embed_batch(["text without explicit normalization"], normalize=False)
        assert len(result[0]) == EMBEDDING_DIM

    def test_output_order_matches_input_order(self):
        texts = ["first", "second", "third"]
        result = embed_batch(texts)
        singles = [embed(t) for t in texts]
        for vec, single in zip(result, singles):
            assert vec == pytest.approx(single, abs=1e-6)

    def test_different_texts_produce_different_vectors(self):
        result = embed_batch(["cat", "car"])
        assert result[0] != result[1]

    def test_same_text_produces_same_vector(self):
        text = "reproducibility"
        r1 = embed_batch([text])[0]
        r2 = embed_batch([text])[0]
        assert r1 == pytest.approx(r2, abs=1e-6)


# ---------------------------------------------------------------------------
# embed
# ---------------------------------------------------------------------------


class TestEmbed:

    def test_returns_vector_with_correct_dimension(self):
        result = embed("hello")
        assert len(result) == EMBEDDING_DIM

    def test_all_elements_are_floats(self):
        result = embed("test")
        assert all(isinstance(x, float) for x in result)

    def test_normalize_true_yields_unit_norm(self):
        result = embed("normalized text", normalize=True)
        assert math.isclose(_norm(result), 1.0, abs_tol=1e-5)

    def test_consistent_with_embed_batch(self):
        text = "consistency between embed and embed_batch"
        assert embed(text) == pytest.approx(embed_batch([text])[0], abs=1e-6)

    def test_different_texts_produce_different_vectors(self):
        assert embed("cat") != embed("car")

    def test_is_deterministic(self):
        text = "determinism"
        assert embed(text) == pytest.approx(embed(text), abs=1e-6)
