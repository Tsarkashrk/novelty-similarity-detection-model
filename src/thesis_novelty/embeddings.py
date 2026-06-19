"""Embedding backends and vector math."""

from __future__ import annotations

import hashlib
import math
from typing import Protocol, Sequence

from thesis_novelty.preprocessing import make_ngrams, normalize_text, tokenize


class EmbeddingBackend(Protocol):
    """Protocol implemented by all embedding backends."""

    dimension: int

    def encode(self, texts: Sequence[str], *, input_type: str = "passage") -> list[list[float]]:
        """Encode texts into normalized embedding vectors."""


def l2_normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Vectors must have the same dimension.")
    return max(0.0, min(1.0, sum(a * b for a, b in zip(left, right))))


class HashingEmbeddingBackend:
    """Deterministic fallback embeddings for local tests and reproducible demos.

    This backend is not a replacement for Sentence-BERT/E5 in the final experiment. It exists so
    the pipeline can be executed without downloading a large neural model.
    """

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    def encode(self, texts: Sequence[str], *, input_type: str = "passage") -> list[list[float]]:
        return [self._encode_one(text) for text in texts]

    def _encode_one(self, text: str) -> list[float]:
        tokens = tokenize(normalize_text(text))
        features = tokens + make_ngrams(tokens, 2)
        if not features:
            return [0.0] * self.dimension

        vector = [0.0] * self.dimension
        for feature in features:
            digest = hashlib.sha256(feature.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            weight = 1.4 if " " in feature else 1.0
            vector[index] += sign * weight
        return l2_normalize(vector)


class SentenceTransformerEmbeddingBackend:
    """SentenceTransformer backend for multilingual-e5 or MiniLM models."""

    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-base",
        *,
        query_prefix: str = "query: ",
        passage_prefix: str = "passage: ",
    ) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required for SentenceTransformerEmbeddingBackend. "
                "Install it with: python3 -m pip install -e '.[embeddings]'"
            ) from exc

        self.model_name = model_name
        self.query_prefix = query_prefix
        self.passage_prefix = passage_prefix
        self.model = SentenceTransformer(model_name)
        self.dimension = int(self.model.get_sentence_embedding_dimension())

    def encode(self, texts: Sequence[str], *, input_type: str = "passage") -> list[list[float]]:
        prefix = self.query_prefix if input_type == "query" else self.passage_prefix
        prepared = [prefix + normalize_text(text) for text in texts]
        embeddings = self.model.encode(
            prepared,
            normalize_embeddings=True,
            convert_to_numpy=False,
            show_progress_bar=False,
        )
        return [list(map(float, vector)) for vector in embeddings]

