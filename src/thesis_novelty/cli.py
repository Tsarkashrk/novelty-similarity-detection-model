"""Command-line interface for novelty assessment."""

from __future__ import annotations

import argparse
import json

from thesis_novelty.embeddings import HashingEmbeddingBackend, SentenceTransformerEmbeddingBackend
from thesis_novelty.io import load_topics_csv
from thesis_novelty.model import ThesisNoveltyModel
from thesis_novelty.schemas import ThesisTopic


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Assess thesis topic novelty.")
    parser.add_argument("--data", default="data/sample_topics.csv", help="CSV file with existing topics.")
    parser.add_argument("--title", required=True, help="New thesis topic title.")
    parser.add_argument("--abstract", default="", help="Optional abstract/description.")
    parser.add_argument(
        "--keywords",
        default="",
        help="Semicolon-separated or comma-separated keywords.",
    )
    parser.add_argument("--domain", default="", help="Domain or research area.")
    parser.add_argument("--language", default="", help="Language code.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of similar topics to return.")
    parser.add_argument(
        "--embedding-model",
        default="",
        help="SentenceTransformer model name. If omitted, deterministic hashing is used.",
    )
    return parser


def parse_keywords(raw: str) -> list[str]:
    if not raw:
        return []
    delimiter = ";" if ";" in raw else ","
    return [part.strip() for part in raw.split(delimiter) if part.strip()]


def main() -> None:
    args = build_parser().parse_args()
    topics = load_topics_csv(args.data)
    backend = (
        SentenceTransformerEmbeddingBackend(args.embedding_model)
        if args.embedding_model
        else HashingEmbeddingBackend()
    )
    model = ThesisNoveltyModel(embedding_backend=backend).fit(topics)
    query = ThesisTopic(
        id="query",
        title=args.title,
        abstract=args.abstract,
        keywords=parse_keywords(args.keywords),
        domain=args.domain,
        language=args.language,
    )
    result = model.assess(query, top_k=args.top_k)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

