from __future__ import annotations

import logging
from psycopg import Connection

from src.repositories.analytics_repository import (
    get_most_polarized_books,
    get_top_books_by_avg_score,
    get_top_books_by_review_volume,
    save_df_to_csv,
)


logger = logging.getLogger(__name__)


def run_book_insights(conn: Connection) -> None:
    logger.info("Running book insights.")

    top_by_volume = get_top_books_by_review_volume(conn, limit=100)
    save_df_to_csv(top_by_volume, "top_books_by_review_volume.csv")

    top_by_avg = get_top_books_by_avg_score(conn, min_reviews=30, limit=100)
    save_df_to_csv(top_by_avg, "top_books_by_avg_score.csv")

    polarized = get_most_polarized_books(conn, min_reviews=30, limit=100)
    save_df_to_csv(polarized, "most_polarized_books.csv")

