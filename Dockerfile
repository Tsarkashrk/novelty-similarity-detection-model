FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install .

FROM base AS test
COPY tests ./tests
COPY data/sample_topics.csv data/sample_pairs.csv ./data/

FROM base AS runtime
RUN useradd --create-home --uid 10001 appuser
USER appuser
ENTRYPOINT ["thesis-novelty"]

FROM base AS api
RUN python -m pip install ".[api]" \
    && useradd --create-home --uid 10001 appuser
COPY data/sample_topics.csv ./data/sample_topics.csv
USER appuser
EXPOSE 8000
CMD ["uvicorn", "thesis_novelty.api:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
