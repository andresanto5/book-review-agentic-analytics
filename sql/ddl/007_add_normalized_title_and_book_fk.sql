ALTER TABLE IF EXISTS app.books
    ADD COLUMN IF NOT EXISTS normalized_title TEXT;

ALTER TABLE IF EXISTS app.reviews
    ADD COLUMN IF NOT EXISTS normalized_title TEXT;

ALTER TABLE IF EXISTS app.reviews
    ADD COLUMN IF NOT EXISTS book_pk BIGINT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_reviews_book_pk'
    ) THEN
        ALTER TABLE app.reviews
            ADD CONSTRAINT fk_reviews_book_pk
            FOREIGN KEY (book_pk)
            REFERENCES app.books (book_pk);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_books_normalized_title
    ON app.books (normalized_title);

CREATE INDEX IF NOT EXISTS idx_reviews_normalized_title
    ON app.reviews (normalized_title);

