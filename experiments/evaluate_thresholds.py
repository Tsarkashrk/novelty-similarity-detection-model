"""Evaluate duplicate classification thresholds on labelled topic pairs."""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from thesis_novelty.config import DuplicateThresholds, ModelConfig
from thesis_novelty.embeddings import HashingEmbeddingBackend, SentenceTransformerEmbeddingBackend
from thesis_novelty.io import load_labelled_pairs_csv, load_topics_csv
from thesis_novelty.model import ThesisNoveltyModel
from thesis_novelty.schemas import DuplicateLabel, ThesisTopic


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topics", default="data/sample_topics.csv")
    parser.add_argument("--pairs", default="data/sample_pairs.csv")
    parser.add_argument("--embedding-model", default="")
    parser.add_argument("--duplicate-threshold", type=float, default=0.90)
    parser.add_argument("--near-duplicate-threshold", type=float, default=0.75)
    return parser.parse_args()


def precision_recall_f1(confusion: dict[str, Counter[str]], label: str) -> tuple[float, float, float]:
    true_positive = confusion[label][label]
    predicted_positive = sum(row[label] for row in confusion.values())
    actual_positive = sum(confusion[label].values())
    precision = true_positive / predicted_positive if predicted_positive else 0.0
    recall = true_positive / actual_positive if actual_positive else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return precision, recall, f1


def main() -> None:
    args = parse_args()
    topics = load_topics_csv(args.topics)
    by_id = {topic.id: topic for topic in topics}

    backend = (
        SentenceTransformerEmbeddingBackend(args.embedding_model)
        if args.embedding_model
        else HashingEmbeddingBackend()
    )
    config = ModelConfig(
        thresholds=DuplicateThresholds(
            duplicate=args.duplicate_threshold,
            near_duplicate=args.near_duplicate_threshold,
        )
    )
    model = ThesisNoveltyModel(embedding_backend=backend, config=config).fit(topics)
    confusion: dict[str, Counter[str]] = defaultdict(Counter)

    for row in load_labelled_pairs_csv(args.pairs):
        query = by_id[row["query_id"]]
        expected = row["label"]
        corpus = [
            topic
            for topic in topics
            if topic.id != query.id and topic.id == row["candidate_id"]
        ]
        if not corpus:
            candidate = by_id[row["candidate_id"]]
            corpus = [candidate]

        pair_model = ThesisNoveltyModel(embedding_backend=backend, config=config).fit(corpus)
        assessed_query = ThesisTopic(
            id=query.id,
            title=query.title,
            abstract=query.abstract,
            keywords=query.keywords,
            domain=query.domain,
            language=query.language,
        )
        predicted = pair_model.assess(assessed_query, top_k=1).label.value
        confusion[expected][predicted] += 1

    labels = [item.value for item in DuplicateLabel]
    print("Confusion matrix")
    print("actual\\predicted," + ",".join(labels))
    for actual in labels:
        print(actual + "," + ",".join(str(confusion[actual][predicted]) for predicted in labels))

    print("\nMetrics")
    macro_f1 = 0.0
    for label in labels:
        precision, recall, f1 = precision_recall_f1(confusion, label)
        macro_f1 += f1
        print(
            f"{label}: precision={precision:.3f} recall={recall:.3f} f1={f1:.3f}"
        )
    print(f"macro_f1={macro_f1 / len(labels):.3f}")


if __name__ == "__main__":
    main()

