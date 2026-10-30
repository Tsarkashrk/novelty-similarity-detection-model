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
