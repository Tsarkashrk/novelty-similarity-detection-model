"""Keyword uniqueness and domain rarity features."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass

from thesis_novelty.preprocessing import extract_candidate_keywords, normalize_text
from thesis_novelty.schemas import ThesisTopic


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


@dataclass(frozen=True)
class KeywordExplanation:
    uniqueness: float
    rare_keywords: list[str]
    common_keywords: list[str]


class KeywordStats:
    """Corpus-level statistics for explainable novelty features."""

    def __init__(self) -> None:
        self.document_count = 0
        self.keyword_df: Counter[str] = Counter()
        self.domain_counts: Counter[str] = Counter()
        self.domain_keyword_counts: dict[str, Counter[str]] = defaultdict(Counter)

    def fit(self, topics: list[ThesisTopic]) -> "KeywordStats":
        self.document_count = len(topics)
        self.keyword_df.clear()
        self.domain_counts.clear()
        self.domain_keyword_counts.clear()

        for topic in topics:
            keywords = set(
                extract_candidate_keywords(
                    topic.title,
                    topic.abstract,
                    topic.keywords,
                    max_terms=24,
                )
            )
            domain = topic.normalized_domain
            if domain:
                self.domain_counts[domain] += 1
            for keyword in keywords:
                self.keyword_df[keyword] += 1
                if domain:
                    self.domain_keyword_counts[domain][keyword] += 1
        return self

    def keyword_uniqueness(self, keywords: list[str]) -> KeywordExplanation:
        if not keywords:
            return KeywordExplanation(uniqueness=0.5, rare_keywords=[], common_keywords=[])

        if self.document_count == 0:
            return KeywordExplanation(
                uniqueness=1.0,
                rare_keywords=keywords[:5],
                common_keywords=[],
            )

        max_idf = math.log((self.document_count + 1) / 1) + 1
        scored: list[tuple[str, float, int]] = []
        for keyword in keywords:
            df = self.keyword_df.get(keyword, 0)
            idf = math.log((self.document_count + 1) / (df + 1)) + 1
            scored.append((keyword, clamp01(idf / max_idf), df))

        uniqueness = sum(score for _, score, _ in scored) / len(scored)
        by_score = sorted(scored, key=lambda item: item[1], reverse=True)
        rare = [keyword for keyword, score, _ in by_score if score >= 0.70][:5]
        common = [keyword for keyword, score, _ in reversed(by_score) if score <= 0.45][:5]
        return KeywordExplanation(
            uniqueness=clamp01(uniqueness),
            rare_keywords=rare,
            common_keywords=common,
        )

    def domain_rarity(self, domain: str, keywords: list[str]) -> float:
        domain = normalize_text(domain)
        if self.document_count == 0:
            return 1.0
        if not domain:
            return 0.5

        domain_count = self.domain_counts.get(domain, 0)
        domain_component = 1.0 - (domain_count / self.document_count)

        if not keywords:
            return clamp01(domain_component)

        denominator = max(domain_count, 1)
        pair_scores = []
        for keyword in keywords:
            pair_count = self.domain_keyword_counts[domain].get(keyword, 0)
            pair_scores.append(1.0 - (pair_count / denominator))

        pair_component = sum(pair_scores) / len(pair_scores)
        return clamp01(0.4 * domain_component + 0.6 * pair_component)

