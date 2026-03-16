CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS app.review_embeddings (
    review_pk BIGINT PRIMARY KEY REFERENCES app.reviews(review_pk),
    book_pk BIGINT,
    embedding vector(384),
    model_name TEXT NOT NULL,
    embedding_dimension INT NOT NULL,
    pipeline_version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_review_embeddings_vector
ON app.review_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_review_embeddings_book_pk
ON app.review_embeddings (book_pk);

