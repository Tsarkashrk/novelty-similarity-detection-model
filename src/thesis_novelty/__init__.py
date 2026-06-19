"""Hybrid thesis topic novelty and duplicate detection."""

from thesis_novelty.config import DuplicateThresholds, ModelConfig, NoveltyWeights
from thesis_novelty.embeddings import HashingEmbeddingBackend, SentenceTransformerEmbeddingBackend
from thesis_novelty.model import ThesisNoveltyModel
from thesis_novelty.schemas import DuplicateLabel, NoveltyResult, ThesisTopic

__all__ = [
    "DuplicateLabel",
    "DuplicateThresholds",
    "HashingEmbeddingBackend",
    "ModelConfig",
    "NoveltyResult",
    "NoveltyWeights",
    "SentenceTransformerEmbeddingBackend",
    "ThesisNoveltyModel",
    "ThesisTopic",
]

