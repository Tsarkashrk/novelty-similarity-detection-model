"""Build a silver-labelled thesis-topic novelty dataset from OpenAlex metadata.

OpenAlex provides real dissertation metadata, but it does not provide labels for
duplicate / near-duplicate / novel thesis-topic pairs. This script therefore
creates a reproducible *silver-labelled* dataset:

1. Fetch real dissertation-like records from OpenAlex.
2. Convert them into thesis topic records.
3. Create controlled duplicate and near-duplicate variants.
4. Create novel pairs by pairing topics from different domains with low lexical overlap.

The output is suitable for prototype evaluation and threshold tuning. It should
be described as silver-labelled or weakly supervised, not as expert-labelled.
"""

from __future__ import annotations

import csv
import json
import random
import re
import ssl
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "openalex_silver"
RAW_DIR = OUT_DIR / "raw"
TOPICS_CSV = OUT_DIR / "openalex_thesis_topics.csv"
PAIRS_CSV = OUT_DIR / "openalex_labelled_pairs.csv"
README = OUT_DIR / "README.md"

OPENALEX_URL = "https://api.openalex.org/works"
RANDOM_SEED = 42

QUERIES = [
    "artificial intelligence education",
    "machine learning education technology",
    "semantic similarity natural language processing",
    "thesis management academic supervision",
    "student project management platform",
    "recommender system academic supervisor",
    "duplicate detection text similarity",
    "learning analytics student performance",
    "knowledge graph education",
    "multilingual natural language processing",
]


@dataclass(frozen=True)
class Topic:
    id: str
    title: str
    abstract: str
    keywords: list[str]
    domain: str
    year: int | str
    language: str
    source: str
    source_id: str
    doi: str
    url: str
    is_synthetic: bool = False
    derived_from: str = ""


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9а-яёәғқңөұүһі]+", " ", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def tokens(text: str) -> set[str]:
    stop = {
        "a",
        "an",
        "and",
        "for",
        "in",
        "of",
        "on",
        "the",
        "to",
        "using",
        "with",
        "by",
        "study",
        "analysis",
        "approach",
        "method",
    }
    return {tok for tok in normalize_text(text).split() if len(tok) > 2 and tok not in stop}


def jaccard(left: str, right: str) -> float:
    left_tokens = tokens(left)
    right_tokens = tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def abstract_from_inverted_index(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    positions: list[tuple[int, str]] = []
    for word, indices in index.items():
        for idx in indices:
            positions.append((idx, word))
    positions.sort()
    words = [word for _, word in positions]
    return " ".join(words[:1200])


def fetch_openalex(query: str, *, per_page: int = 25) -> dict[str, Any]:
    params = {
        "filter": "type:dissertation",
        "search": query,
        "per-page": str(per_page),
        "select": ",".join(
            [
                "id",
                "doi",
                "title",
                "display_name",
                "publication_year",
                "language",
                "abstract_inverted_index",
                "primary_topic",
                "topics",
                "concepts",
            ]
        ),
    }
    url = OPENALEX_URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "thesis-novelty-dataset-builder/0.1 (mailto:example@example.com)"
        },
    )
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(request, timeout=40, context=context) as response:
        return json.loads(response.read().decode("utf-8"))


def topic_domain(work: dict[str, Any]) -> str:
    primary = work.get("primary_topic") or {}
    if primary.get("display_name"):
        return primary["display_name"]
    topics = work.get("topics") or []
    if topics and topics[0].get("display_name"):
        return topics[0]["display_name"]
    concepts = work.get("concepts") or []
    if concepts and concepts[0].get("display_name"):
        return concepts[0]["display_name"]
    return "General academic research"


def topic_keywords(work: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for item in (work.get("topics") or [])[:4]:
        name = item.get("display_name")
        if name:
            names.append(name)
    for item in (work.get("concepts") or [])[:8]:
        name = item.get("display_name")
        if name and name not in names:
            names.append(name)
    return names[:8]


def clean_title(work: dict[str, Any]) -> str:
    title = work.get("title") or work.get("display_name") or ""
    title = re.sub(r"\s+", " ", title).strip()
    return title


def collect_topics() -> list[Topic]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    by_normalized_title: dict[str, Topic] = {}
    topic_counter = 1
    for query in QUERIES:
        print(f"Fetching OpenAlex dissertations for query: {query}")
        payload = fetch_openalex(query)
        raw_path = RAW_DIR / f"{normalize_text(query).replace(' ', '_')}.json"
        raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        time.sleep(0.2)

        for work in payload.get("results", []):
            title = clean_title(work)
            if len(title) < 25:
                continue
            normalized = normalize_text(title)
            if normalized in by_normalized_title:
                continue
            abstract = abstract_from_inverted_index(work.get("abstract_inverted_index"))
            source_id = work.get("id") or ""
            topic = Topic(
                id=f"OA{topic_counter:04d}",
                title=title,
                abstract=abstract,
                keywords=topic_keywords(work),
                domain=topic_domain(work),
                year=work.get("publication_year") or "",
                language=work.get("language") or "",
                source="OpenAlex",
                source_id=source_id,
                doi=work.get("doi") or "",
                url=source_id,
            )
            by_normalized_title[normalized] = topic
            topic_counter += 1

    topics = list(by_normalized_title.values())
    topics.sort(key=lambda item: item.id)
    return topics


def duplicate_variant(topic: Topic, index: int) -> Topic:
    return Topic(
        id=f"DUP{index:04d}",
        title=topic.title,
        abstract=topic.abstract,
        keywords=topic.keywords,
        domain=topic.domain,
        year=topic.year,
        language=topic.language,
        source="OpenAlex-derived",
        source_id=topic.source_id,
        doi=topic.doi,
        url=topic.url,
        is_synthetic=True,
        derived_from=topic.id,
    )


def near_duplicate_title(title: str) -> str:
    replacements = [
        (r"\bAn analysis of\b", "A study of"),
        (r"\bAnalysis of\b", "Study of"),
        (r"\bA study of\b", "An investigation of"),
        (r"\bstudy of\b", "analysis of"),
        (r"\busing\b", "based on"),
        (r"\bfor\b", "to support"),
        (r"\bin\b", "within"),
        (r"\band\b", "with"),
        (r"\bdevelopment of\b", "design of"),
        (r"\bapplication of\b", "use of"),
    ]
    new_title = title
    for pattern, replacement in replacements:
        updated = re.sub(pattern, replacement, new_title, count=1, flags=re.IGNORECASE)
        if updated != new_title:
            new_title = updated
            break
    if new_title == title:
        new_title = f"Semantic and methodological study of {title[0].lower() + title[1:]}"
    return new_title


def near_duplicate_variant(topic: Topic, index: int) -> Topic:
    keywords = topic.keywords[:3] if topic.keywords else []
    return Topic(
        id=f"NEAR{index:04d}",
        title=near_duplicate_title(topic.title),
        abstract="",
        keywords=keywords,
        domain=topic.domain,
        year=topic.year,
        language=topic.language,
        source="OpenAlex-derived",
        source_id=topic.source_id,
        doi=topic.doi,
        url=topic.url,
        is_synthetic=True,
        derived_from=topic.id,
    )


def build_dataset(real_topics: list[Topic]) -> tuple[list[Topic], list[dict[str, str]]]:
    rng = random.Random(RANDOM_SEED)
    if len(real_topics) < 40:
        raise RuntimeError("Not enough OpenAlex topics were collected to build the dataset.")

    selected = real_topics[:160]
    pairs: list[dict[str, str]] = []
    all_topics: list[Topic] = list(selected)

    duplicate_sources = selected[:30]
    near_sources = selected[30:70]

    for idx, topic in enumerate(duplicate_sources, start=1):
        variant = duplicate_variant(topic, idx)
        all_topics.append(variant)
        pairs.append(
            {
                "query_id": variant.id,
                "candidate_id": topic.id,
                "label": "duplicate",
                "label_source": "silver_exact_variant",
                "confidence": "0.98",
                "rationale": "Synthetic duplicate variant generated from the same OpenAlex dissertation record.",
            }
        )

    for idx, topic in enumerate(near_sources, start=1):
        variant = near_duplicate_variant(topic, idx)
        all_topics.append(variant)
        pairs.append(
            {
                "query_id": variant.id,
                "candidate_id": topic.id,
                "label": "near_duplicate",
                "label_source": "silver_paraphrase_variant",
                "confidence": "0.85",
                "rationale": "Controlled title paraphrase with the same domain, abstract and keywords.",
            }
        )

    novel_pairs = []
    attempts = 0
    while len(novel_pairs) < 60 and attempts < 10000:
        attempts += 1
        left, right = rng.sample(selected, 2)
        if left.domain == right.domain:
            continue
        if jaccard(left.title + " " + " ".join(left.keywords), right.title + " " + " ".join(right.keywords)) > 0.08:
            continue
        pair_key = tuple(sorted([left.id, right.id]))
        if pair_key in novel_pairs:
            continue
        novel_pairs.append(pair_key)
        pairs.append(
            {
                "query_id": left.id,
                "candidate_id": right.id,
                "label": "novel",
                "label_source": "silver_distant_domain_pair",
                "confidence": "0.75",
                "rationale": "Different OpenAlex domains and low lexical overlap between titles and keywords.",
            }
        )

    rng.shuffle(pairs)
    return all_topics, pairs


def write_topics(topics: list[Topic]) -> None:
    fieldnames = [
        "id",
        "title",
        "abstract",
        "keywords",
        "domain",
        "supervisor_id",
        "year",
        "language",
        "source",
        "source_id",
        "doi",
        "url",
        "is_synthetic",
        "derived_from",
    ]
    with TOPICS_CSV.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for topic in topics:
            writer.writerow(
                {
                    "id": topic.id,
                    "title": topic.title,
                    "abstract": topic.abstract,
                    "keywords": ";".join(topic.keywords),
                    "domain": topic.domain,
                    "supervisor_id": "",
                    "year": topic.year,
                    "language": topic.language,
                    "source": topic.source,
                    "source_id": topic.source_id,
                    "doi": topic.doi,
                    "url": topic.url,
                    "is_synthetic": str(topic.is_synthetic).lower(),
                    "derived_from": topic.derived_from,
                }
            )


def write_pairs(pairs: list[dict[str, str]]) -> None:
    fieldnames = ["query_id", "candidate_id", "label", "label_source", "confidence", "rationale"]
    with PAIRS_CSV.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(pairs)


def write_readme(topics: list[Topic], pairs: list[dict[str, str]]) -> None:
    counts: dict[str, int] = {}
    for pair in pairs:
        counts[pair["label"]] = counts.get(pair["label"], 0) + 1
    real_count = sum(1 for topic in topics if not topic.is_synthetic)
    synthetic_count = len(topics) - real_count
    README.write_text(
        f"""# OpenAlex Silver-labelled Thesis Topic Dataset

This folder contains a reproducible silver-labelled dataset for thesis topic
novelty assessment and duplicate detection.

## Source choice

OpenAlex was used because it provides a stable public API, structured metadata,
dissertation filtering, titles, abstracts when available, publication years,
language metadata, and topic/concept metadata. NDLTD and OATD are highly relevant
for thesis records, but they are less convenient for reproducible automated
collection in this prototype.

## Files

- `openalex_thesis_topics.csv`: topic records derived from OpenAlex dissertation metadata.
- `openalex_labelled_pairs.csv`: silver-labelled topic pairs.
- `raw/`: raw OpenAlex API responses used to build the dataset.

## Dataset size

- Total topic records: {len(topics)}
- Real OpenAlex records: {real_count}
- Controlled synthetic variants: {synthetic_count}
- Total labelled pairs: {len(pairs)}
- Duplicate pairs: {counts.get("duplicate", 0)}
- Near-duplicate pairs: {counts.get("near_duplicate", 0)}
- Novel pairs: {counts.get("novel", 0)}

## Important limitation

The labels are silver labels, not expert human labels. Duplicate and
near-duplicate examples are controlled variants derived from real OpenAlex
dissertation records. Novel examples are pairs from different OpenAlex domains
with low lexical overlap. This dataset is appropriate for prototype validation,
threshold tuning, and methodology demonstration. For a final dissertation or
publication, a subset should be manually reviewed by domain experts.

## Recommended usage

Use this dataset as an intermediate benchmark before collecting real university
thesis topics. Report results as preliminary and clearly state the labelling
strategy.
""",
        encoding="utf-8",
    )


def main() -> None:
    real_topics = collect_topics()
    topics, pairs = build_dataset(real_topics)
    write_topics(topics)
    write_pairs(pairs)
    write_readme(topics, pairs)
    print(f"Wrote {TOPICS_CSV}")
    print(f"Wrote {PAIRS_CSV}")
    print(f"Topics: {len(topics)}")
    print(f"Pairs: {len(pairs)}")


if __name__ == "__main__":
    main()
