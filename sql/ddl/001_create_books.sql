CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.books (
    book_pk BIGSERIAL PRIMARY KEY,
    title TEXT,
    description TEXT,
    image_url TEXT,
    preview_link TEXT,
    publisher TEXT,
    published_date_raw TEXT,
    info_link TEXT,
    ratings_count BIGINT,
    published_date_parsed TIMESTAMPTZ,
    published_year INT
);

