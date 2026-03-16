from __future__ import annotations

import logging
from psycopg import Connection

from src.repositories.analytics_repository import (
    get_review_length_stats,
    get_reviews_by_year,
    get_score_distribution,
    save_df_to_csv,
)


logger = logging.getLogger(__name__)


def run_distribution_insights(conn: Connection) -> None:
    logger.info("Running distribution insights.")

    score_dist = get_score_distribution(conn)
    save_df_to_csv(score_dist, "score_distribution.csv")

    length_stats = get_review_length_stats(conn)
    save_df_to_csv(length_stats, "review_length_stats.csv")

    reviews_by_year = get_reviews_by_year(conn)
    save_df_to_csv(reviews_by_year, "reviews_by_year.csv")

