from __future__ import annotations

import logging
from pprint import pprint

from src.config.settings import db_settings
from src.agents.tools import (
    get_book_review_context,
    get_most_polarized_books,
    get_top_books_by_review_volume,
    get_top_categories_by_avg_score,
)
from src.repositories.base_repository import get_connection


logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


def run_tools_demo() -> None:
    _configure_logging()
    logger.info(
        "Starting tools demo using DSN %s",
        db_settings.dsn,
    )

    with get_connection() as conn:
        logger.info("Demo: get_top_books_by_review_volume(limit=10)")
        books_by_volume = get_top_books_by_review_volume(conn, limit=10)
        pprint(books_by_volume)

        logger.info(
            "Demo: get_top_categories_by_avg_score(min_reviews=100, limit=10)"
        )
        top_categories = get_top_categories_by_avg_score(
            conn, min_reviews=100, limit=10
        )
        pprint(top_categories)

        logger.info("Demo: get_most_polarized_books(min_reviews=50, limit=10)")
        polarized_books = get_most_polarized_books(
            conn, min_reviews=50, limit=10
        )
        pprint(polarized_books)

        logger.info(
            "Demo: get_book_review_context(book_title='Harry Potter', limit=5)"
        )
        book_contexts = get_book_review_context(
            conn, book_title="Harry Potter", limit=5
        )
        pprint(book_contexts)

    logger.info("Tools demo completed.")


def main() -> None:
    run_tools_demo()


if __name__ == "__main__":
    main()

