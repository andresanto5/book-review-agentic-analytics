from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from src.config.settings import db_settings
from src.repositories.authors_repository import (
    extract_unique_authors,
    insert_authors,
    insert_book_authors,
)
from src.repositories.base_repository import (
    DDL_DIR,
    get_connection,
    run_ddl_files,
    truncate_app_tables,
)
from src.repositories.books_repository import insert_books
from src.repositories.categories_repository import (
    extract_unique_categories,
    insert_book_categories,
    insert_categories,
)
from src.repositories.reviews_repository import insert_reviews


logger = logging.getLogger(__name__)


BOOKS_PARQUET_PATH = Path("data/processed/books_clean.parquet")
REVIEWS_PARQUET_PATH = Path("data/processed/reviews_clean.parquet")


def _configure_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


def load_processed_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("Loading processed books from '%s'", BOOKS_PARQUET_PATH)
    books_df = pd.read_parquet(BOOKS_PARQUET_PATH)
    logger.info("Books dataframe loaded with shape %s", books_df.shape)

    logger.info("Loading processed reviews from '%s'", REVIEWS_PARQUET_PATH)
    reviews_df = pd.read_parquet(REVIEWS_PARQUET_PATH)
    logger.info("Reviews dataframe loaded with shape %s", reviews_df.shape)

    return books_df, reviews_df


def create_schema_and_tables() -> None:
    ddl_files = sorted(DDL_DIR.glob("*.sql"))
    if not ddl_files:
        raise FileNotFoundError(f"No DDL files found in {DDL_DIR}")

    with get_connection() as conn:
        logger.info("Running DDL files to ensure schema/tables exist.")
        run_ddl_files(conn, ddl_files)


def run_pipeline(full_reload: bool = True) -> None:
    _configure_logging()
    logger.info("Starting load-to-Postgres pipeline using DSN %s", db_settings.dsn)

    create_schema_and_tables()
    books_df, reviews_df = load_processed_data()

    with get_connection() as conn:
        if full_reload:
            logger.info("Full reload enabled: cleaning app schema tables before load.")
            truncate_app_tables(conn)

        logger.info("Loading books.")
        inserted_books = insert_books(conn, books_df)
        logger.info("Inserted %d books.", inserted_books)

        logger.info("Processing authors.")
        unique_authors = extract_unique_authors(books_df)
        authors_mapping = insert_authors(conn, unique_authors)
        logger.info("Processing book_authors relationships.")
        book_authors_count = insert_book_authors(conn, books_df, authors_mapping)
        logger.info("Inserted %d book_authors rows.", book_authors_count)

        logger.info("Processing categories.")
        unique_categories = extract_unique_categories(books_df)
        categories_mapping = insert_categories(conn, unique_categories)
        logger.info("Processing book_categories relationships.")
        book_categories_count = insert_book_categories(
            conn, books_df, categories_mapping
        )
        logger.info("Inserted %d book_categories rows.", book_categories_count)

        logger.info("Loading reviews.")
        inserted_reviews = insert_reviews(conn, reviews_df)
        logger.info("Inserted %d reviews.", inserted_reviews)

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM app.books")
            books_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM app.authors")
            authors_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM app.book_authors")
            book_authors_rel = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM app.categories")
            categories_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM app.book_categories")
            book_categories_rel = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM app.reviews")
            reviews_count = cur.fetchone()[0]

        logger.info("Final row counts:")
        logger.info("app.books: %d", books_count)
        logger.info("app.authors: %d", authors_count)
        logger.info("app.book_authors: %d", book_authors_rel)
        logger.info("app.categories: %d", categories_count)
        logger.info("app.book_categories: %d", book_categories_rel)
        logger.info("app.reviews: %d", reviews_count)

    logger.info("Load-to-Postgres pipeline completed.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load processed parquet data into Postgres (schema app)."
    )
    parser.add_argument(
        "--full-reload",
        action="store_true",
        help="Truncate app tables and restart identities before loading data.",
    )
    args = parser.parse_args()

    # Por padrão, consideramos full_reload=True para segurança em batch.
    full_reload = True if args.full_reload or True else False
    run_pipeline(full_reload=full_reload)


if __name__ == "__main__":
    main()

