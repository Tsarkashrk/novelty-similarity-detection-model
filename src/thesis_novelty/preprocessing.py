"""Multilingual preprocessing helpers.

The functions are intentionally lightweight and deterministic. Heavy NLP pipelines can be added
later, but this module keeps the research prototype reproducible.
"""

from __future__ import annotations

import re
import unicodedata

TOKEN_RE = re.compile(r"[a-zа-яёәғқңөұүһі0-9]+", flags=re.IGNORECASE)

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "using",
    "with",
    "и",
    "в",
    "во",
    "для",
    "на",
    "по",
    "с",
    "со",
    "к",
    "ко",
    "от",
    "из",
    "при",
    "как",
    "или",
    "а",
    "о",
    "об",
    "the",
    "және",
    "мен",
    "үшін",
    "бойынша",
    "арқылы",
    "бір",
    "бұл",
}


def normalize_text(text: str | None) -> str:
    """Normalize text while preserving multilingual letters."""

    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("ё", "е").replace("Ё", "Е")
    text = text.lower()
    text = re.sub(r"[_/\\|+*=#@%$^~`\"'“”‘’.,:;!?()[\]{}<>-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str | None, *, remove_stopwords: bool = True) -> list[str]:
    """Tokenize Russian, Kazakh and English text."""

    normalized = normalize_text(text)
    tokens = TOKEN_RE.findall(normalized)
    if remove_stopwords:
        tokens = [token for token in tokens if token not in STOPWORDS and len(token) > 1]
    return tokens


def make_ngrams(tokens: list[str], n: int) -> list[str]:
    """Create token n-grams joined by a single space."""

    if n <= 0:
        raise ValueError("n must be positive.")
    if len(tokens) < n:
        return []
    return [" ".join(tokens[index : index + n]) for index in range(len(tokens) - n + 1)]


def extract_candidate_keywords(
    title: str,
    abstract: str = "",
    keywords: list[str] | None = None,
    *,
    max_terms: int = 16,
) -> list[str]:
    """Return provided keywords plus informative terms extracted from title and abstract."""

    candidates: list[str] = []
    for keyword in keywords or []:
        normalized = normalize_text(keyword)
        if normalized:
            candidates.append(normalized)

    tokens = tokenize(f"{title} {abstract}")
    candidates.extend(make_ngrams(tokens, 2))
    candidates.extend(tokens)

    seen: set[str] = set()
    unique: list[str] = []
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            unique.append(candidate)
        if len(unique) >= max_terms:
            break
    return unique

