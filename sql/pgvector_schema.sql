CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS thesis_topics (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    abstract TEXT DEFAULT '',
    keywords TEXT[] DEFAULT '{}',
    domain TEXT DEFAULT '',
    supervisor_id TEXT DEFAULT '',
    year INTEGER,
    language TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- multilingual-e5-base has 768 dimensions.
-- Change vector(768) to match another embedding model if needed.
CREATE TABLE IF NOT EXISTS thesis_topic_embeddings (
    topic_id TEXT PRIMARY KEY REFERENCES thesis_topics(id) ON DELETE CASCADE,
    embedding vector(768) NOT NULL,
    model_name TEXT NOT NULL DEFAULT 'intfloat/multilingual-e5-base',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS thesis_topic_embeddings_hnsw_idx
ON thesis_topic_embeddings
USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS thesis_similarity_results (
    id BIGSERIAL PRIMARY KEY,
    query_topic_id TEXT NOT NULL REFERENCES thesis_topics(id) ON DELETE CASCADE,
    candidate_topic_id TEXT NOT NULL REFERENCES thesis_topics(id) ON DELETE CASCADE,
    semantic_similarity DOUBLE PRECISION NOT NULL,
    novelty_score DOUBLE PRECISION NOT NULL,
    duplicate_probability DOUBLE PRECISION NOT NULL,
    label TEXT NOT NULL CHECK (label IN ('duplicate', 'near_duplicate', 'novel')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

