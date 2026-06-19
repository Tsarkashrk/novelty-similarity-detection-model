import unittest

from thesis_novelty.config import DuplicateThresholds, ModelConfig
from thesis_novelty.embeddings import HashingEmbeddingBackend
from thesis_novelty.model import ThesisNoveltyModel
from thesis_novelty.schemas import DuplicateLabel, ThesisTopic


def build_model() -> ThesisNoveltyModel:
    topics = [
        ThesisTopic(
            id="A",
            title="Semantic similarity model for thesis topic duplicate detection",
            abstract="The system uses embeddings and cosine similarity for thesis topic novelty.",
            keywords=["semantic similarity", "duplicate detection", "thesis management"],
            domain="education technology",
        ),
        ThesisTopic(
            id="B",
            title="Federated learning for privacy preserving medical analytics",
            abstract="The model trains local nodes without centralizing sensitive patient data.",
            keywords=["federated learning", "privacy", "medical analytics"],
            domain="healthcare AI",
        ),
    ]
    config = ModelConfig(thresholds=DuplicateThresholds(duplicate=0.88, near_duplicate=0.55))
    return ThesisNoveltyModel(
        embedding_backend=HashingEmbeddingBackend(dimension=256),
        config=config,
    ).fit(topics)


class ThesisNoveltyModelTest(unittest.TestCase):
    def test_duplicate_topic_is_detected(self) -> None:
        model = build_model()
        query = ThesisTopic(
            id="Q",
            title="Semantic similarity model for thesis topic duplicate detection",
            abstract="The system uses embeddings and cosine similarity for thesis topic novelty.",
            keywords=["semantic similarity", "duplicate detection", "thesis management"],
            domain="education technology",
        )

        result = model.assess(query)

        self.assertEqual(result.label, DuplicateLabel.DUPLICATE)
        self.assertGreaterEqual(result.components.semantic_similarity, 0.88)
        self.assertEqual(result.similar_topics[0].topic_id, "A")

    def test_unrelated_topic_has_higher_novelty(self) -> None:
        model = build_model()
        query = ThesisTopic(
            id="Q",
            title="Kazakh NLP system for morphology-aware semantic search",
            abstract="The research uses multilingual embeddings for Kazakh text retrieval.",
            keywords=["Kazakh NLP", "semantic search", "morphology"],
            domain="natural language processing",
        )

        result = model.assess(query)

        self.assertEqual(result.label, DuplicateLabel.NOVEL)
        self.assertGreater(result.novelty_score, 0.50)
        self.assertGreater(result.components.keyword_uniqueness, 0.50)


if __name__ == "__main__":
    unittest.main()
