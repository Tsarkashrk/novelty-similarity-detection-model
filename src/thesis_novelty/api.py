"""FastAPI application for serving the novelty model."""

from __future__ import annotations

import os

from thesis_novelty.embeddings import HashingEmbeddingBackend, SentenceTransformerEmbeddingBackend
from thesis_novelty.io import load_topics_csv
from thesis_novelty.model import ThesisNoveltyModel
from thesis_novelty.schemas import ThesisTopic


def create_app():
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel, Field
    except ImportError as exc:
        raise ImportError(
            "FastAPI dependencies are not installed. "
            "Install them with: python3 -m pip install -e '.[api]'"
        ) from exc

    class TopicRequest(BaseModel):
        title: str = Field(..., min_length=3)
        abstract: str = ""
        keywords: list[str] = Field(default_factory=list)
        domain: str = ""
        language: str = ""

    data_path = os.getenv("THESIS_TOPICS_CSV", "data/sample_topics.csv")
    embedding_model = os.getenv("THESIS_EMBEDDING_MODEL", "")
    backend = (
        SentenceTransformerEmbeddingBackend(embedding_model)
        if embedding_model
        else HashingEmbeddingBackend()
    )
    model = ThesisNoveltyModel(embedding_backend=backend).fit(load_topics_csv(data_path))

    app = FastAPI(
        title="Thesis Novelty Detection API",
        version="0.1.0",
        description="Hybrid novelty scoring and duplicate detection for thesis topics.",
    )

    @app.get("/health")
    def health() -> dict[str, str | int]:
        return {
            "status": "ok",
            "topics": len(model.topics),
            "embedding_backend": type(backend).__name__,
        }

    @app.post("/assess")
    def assess_topic(payload: TopicRequest) -> dict:
        topic = ThesisTopic(
            id="api-query",
            title=payload.title,
            abstract=payload.abstract,
            keywords=payload.keywords,
            domain=payload.domain,
            language=payload.language,
        )
        return model.assess(topic).to_dict()

    return app

