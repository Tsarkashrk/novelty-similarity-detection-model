"""Input/output helpers."""

from __future__ import annotations

import csv
from pathlib import Path

from thesis_novelty.schemas import ThesisTopic


def load_topics_csv(path: str | Path) -> list[ThesisTopic]:
    """Load thesis topics from CSV.

    Expected columns: id, title, abstract, keywords, domain, supervisor_id, year, language.
    Only id and title are required.
    """

    csv_path = Path(path)
    with csv_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        return [ThesisTopic.from_mapping(row) for row in reader if row.get("title")]


def load_labelled_pairs_csv(path: str | Path) -> list[dict[str, str]]:
    csv_path = Path(path)
    with csv_path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))

