"""Hybrid novelty scoring and duplicate detection model."""

from __future__ import annotations

from thesis_novelty.config import ModelConfig
from thesis_novelty.embeddings import (
    EmbeddingBackend,
    HashingEmbeddingBackend,
    cosine_similarity,
)
from thesis_novelty.keyword_analysis import KeywordStats, clamp01
from thesis_novelty.preprocessing import extract_candidate_keywords
from thesis_novelty.schemas import (
    DuplicateLabel,
    NoveltyComponents,
    NoveltyResult,
    SimilarTopic,
    ThesisTopic,
)


class ThesisNoveltyModel:
    """Hybrid model for novelty assessment and duplicate detection."""

    def __init__(
        self,
        *,
        embedding_backend: EmbeddingBackend | None = None,
        config: ModelConfig | None = None,
    ) -> None:
        self.config = config or ModelConfig()
        self.config.validate()
        self.embedding_backend = embedding_backend or HashingEmbeddingBackend()
        self.topics: list[ThesisTopic] = []
        self.topic_embeddings: list[list[float]] = []
        self.keyword_stats = KeywordStats()

    def fit(self, topics: list[ThesisTopic]) -> "ThesisNoveltyModel":
        """Fit corpus statistics and precompute passage embeddings."""

        self.topics = list(topics)
        corpus_texts = [topic.embedding_text() for topic in self.topics]
        self.topic_embeddings = self.embedding_backend.encode(corpus_texts, input_type="passage")
        self.keyword_stats.fit(self.topics)
        return self

    def assess(self, topic: ThesisTopic, *, top_k: int | None = None) -> NoveltyResult:
        """Assess one topic against the fitted corpus."""

        if top_k is None:
            top_k = self.config.top_k
        if top_k <= 0:
            raise ValueError("top_k must be positive.")

        query_embedding = self.embedding_backend.encode(
            [topic.embedding_text()],
            input_type="query",
        )[0]
        ranked = self._rank_similar_topics(query_embedding, top_k=top_k)
        max_similarity = ranked[0].similarity if ranked else 0.0

        keywords = extract_candidate_keywords(topic.title, topic.abstract, topic.keywords)
        keyword_explanation = self.keyword_stats.keyword_uniqueness(keywords)
        domain_rarity = self.keyword_stats.domain_rarity(topic.domain, keywords)
        semantic_distance = 1.0 - max_similarity

        weights = self.config.weights.normalized()
        novelty_score = clamp01(
            weights.semantic_distance * semantic_distance
            + weights.keyword_uniqueness * keyword_explanation.uniqueness
            + weights.domain_rarity * domain_rarity
        )
        duplicate_probability = self._duplicate_probability(max_similarity, novelty_score)
        label = self._classify(max_similarity)

        return NoveltyResult(
            topic=topic,
            novelty_score=novelty_score,
            duplicate_probability=duplicate_probability,
            label=label,
            components=NoveltyComponents(
                semantic_similarity=max_similarity,
                semantic_distance=semantic_distance,
                keyword_uniqueness=keyword_explanation.uniqueness,
                domain_rarity=domain_rarity,
            ),
            similar_topics=ranked,
            rare_keywords=keyword_explanation.rare_keywords,
            common_keywords=keyword_explanation.common_keywords,
        )

    def assess_many(self, topics: list[ThesisTopic], *, top_k: int | None = None) -> list[NoveltyResult]:
        return [self.assess(topic, top_k=top_k) for topic in topics]

    def _rank_similar_topics(self, query_embedding: list[float], *, top_k: int) -> list[SimilarTopic]:
        if not self.topics:
            return []

        scored = [
            (
                topic,
                cosine_similarity(query_embedding, embedding),
            )
            for topic, embedding in zip(self.topics, self.topic_embeddings)
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return [
            SimilarTopic(
                topic_id=topic.id,
                title=topic.title,
                similarity=score,
                domain=topic.domain,
            )
            for topic, score in scored[:top_k]
        ]

    def _classify(self, similarity: float) -> DuplicateLabel:
        thresholds = self.config.thresholds
        if similarity >= thresholds.duplicate:
            return DuplicateLabel.DUPLICATE
        if similarity >= thresholds.near_duplicate:
            return DuplicateLabel.NEAR_DUPLICATE
        return DuplicateLabel.NOVEL

    @staticmethod
    def _duplicate_probability(max_similarity: float, novelty_score: float) -> float:
        return clamp01(0.80 * max_similarity + 0.20 * (1.0 - novelty_score))

