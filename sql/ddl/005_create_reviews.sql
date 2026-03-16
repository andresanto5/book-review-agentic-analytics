CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.reviews (
    review_pk BIGSERIAL PRIMARY KEY,
    book_id_raw TEXT,
    title TEXT,
    price NUMERIC,
    user_id TEXT,
    profile_name TEXT,
    score DOUBLE PRECISION,
    review_time_unix BIGINT,
    review_summary TEXT,
    review_text TEXT,
    review_time TIMESTAMPTZ
);

