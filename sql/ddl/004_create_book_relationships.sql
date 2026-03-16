CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.book_authors (
    book_pk BIGINT NOT NULL,
    author_pk BIGINT NOT NULL,
    PRIMARY KEY (book_pk, author_pk),
    FOREIGN KEY (book_pk) REFERENCES app.books (book_pk),
    FOREIGN KEY (author_pk) REFERENCES app.authors (author_pk)
);

CREATE TABLE IF NOT EXISTS app.book_categories (
    book_pk BIGINT NOT NULL,
    category_pk BIGINT NOT NULL,
    PRIMARY KEY (book_pk, category_pk),
    FOREIGN KEY (book_pk) REFERENCES app.books (book_pk),
    FOREIGN KEY (category_pk) REFERENCES app.categories (category_pk)
);

