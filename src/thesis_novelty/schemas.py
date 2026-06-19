"""Dataclasses used by the novelty model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from thesis_novelty.preprocessing import normalize_text


class DuplicateLabel(str, Enum):
    """Model classification labels."""

    DUPLICATE = "duplicate"
    NEAR_DUPLICATE = "near_duplicate"
    NOVEL = "novel"


@dataclass(frozen=True)
class ThesisTopic:
    """A thesis or master project topic."""

    id: str
    title: str
    abstract: str = ""
    keywords: list[str] = field(default_factory=list)
    domain: str = ""
    supervisor_id: str = ""
    year: int | None = None
    language: str = ""

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "ThesisTopic":
        keywords = data.get("keywords") or []
        if isinstance(keywords, str):
            keywords = [part.strip() for part in keywords.split(";") if part.strip()]
        year_value = data.get("year")
        try:
            year = int(year_value) if year_value not in (None, "") else None
        except ValueError:
            year = None
        return cls(
            id=str(data.get("id") or data.get("topic_id") or ""),
            title=str(data.get("title") or ""),
            abstract=str(data.get("abstract") or ""),
            keywords=list(keywords),
            domain=str(data.get("domain") or ""),
            supervisor_id=str(data.get("supervisor_id") or ""),
            year=year,
            language=str(data.get("language") or ""),
        )

    @property
    def normalized_domain(self) -> str:
        return normalize_text(self.domain)

    def embedding_text(self) -> str:
        keyword_text = ", ".join(self.keywords)
        # Title and keywords are usually the strongest duplicate signals in thesis topics.
        parts = [self.title, self.title, keyword_text, keyword_text, self.abstract, self.domain]
        return normalize_text(" ".join(part for part in parts if part))


@dataclass(frozen=True)
class SimilarTopic:
    """A nearest topic with similarity details."""

    topic_id: str
    title: str
    similarity: float
    domain: str = ""


@dataclass(frozen=True)
class NoveltyComponents:
    """Explainable components of the final novelty score."""

    semantic_similarity: float
    semantic_distance: float
    keyword_uniqueness: float
    domain_rarity: float


@dataclass(frozen=True)
class NoveltyResult:
    """Final model result for one assessed topic."""

    topic: ThesisTopic
    novelty_score: float
    duplicate_probability: float
    label: DuplicateLabel
    components: NoveltyComponents
    similar_topics: list[SimilarTopic]
    rare_keywords: list[str]
    common_keywords: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": {
                "id": self.topic.id,
                "title": self.topic.title,
                "abstract": self.topic.abstract,
                "keywords": self.topic.keywords,
                "domain": self.topic.domain,
                "supervisor_id": self.topic.supervisor_id,
                "year": self.topic.year,
                "language": self.topic.language,
            },
            "novelty_score": round(self.novelty_score, 4),
            "duplicate_probability": round(self.duplicate_probability, 4),
            "label": self.label.value,
            "components": {
                "semantic_similarity": round(self.components.semantic_similarity, 4),
                "semantic_distance": round(self.components.semantic_distance, 4),
                "keyword_uniqueness": round(self.components.keyword_uniqueness, 4),
                "domain_rarity": round(self.components.domain_rarity, 4),
            },
            "similar_topics": [
                {
                    "topic_id": item.topic_id,
                    "title": item.title,
                    "similarity": round(item.similarity, 4),
                    "domain": item.domain,
                }
                for item in self.similar_topics
            ],
            "rare_keywords": self.rare_keywords,
            "common_keywords": self.common_keywords,
        }
