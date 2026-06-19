"""Configuration objects for the hybrid novelty model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NoveltyWeights:
    """Weights used in the final novelty score formula."""

    semantic_distance: float = 0.60
    keyword_uniqueness: float = 0.25
    domain_rarity: float = 0.15

    def normalized(self) -> "NoveltyWeights":
        total = self.semantic_distance + self.keyword_uniqueness + self.domain_rarity
        if total <= 0:
            raise ValueError("At least one novelty weight must be positive.")
        return NoveltyWeights(
            semantic_distance=self.semantic_distance / total,
            keyword_uniqueness=self.keyword_uniqueness / total,
            domain_rarity=self.domain_rarity / total,
        )


@dataclass(frozen=True)
class DuplicateThresholds:
    """Cosine similarity thresholds for duplicate classification."""

    duplicate: float = 0.90
    near_duplicate: float = 0.75

    def validate(self) -> None:
        if not 0 <= self.near_duplicate <= self.duplicate <= 1:
            raise ValueError(
                "Thresholds must satisfy 0 <= near_duplicate <= duplicate <= 1."
            )


@dataclass(frozen=True)
class ModelConfig:
    """Top-level model settings."""

    weights: NoveltyWeights = NoveltyWeights()
    thresholds: DuplicateThresholds = DuplicateThresholds()
    top_k: int = 5
    e5_query_prefix: str = "query: "
    e5_passage_prefix: str = "passage: "

    def validate(self) -> None:
        self.thresholds.validate()
        if self.top_k <= 0:
            raise ValueError("top_k must be positive.")
        self.weights.normalized()

