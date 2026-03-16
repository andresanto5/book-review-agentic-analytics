from __future__ import annotations

import logging
from psycopg import Connection

from src.repositories.analytics_repository import (
    get_top_reviewers,
    save_df_to_csv,
)


logger = logging.getLogger(__name__)


def run_reviewer_insights(conn: Connection) -> None:
    logger.info("Running reviewer insights.")

    top_reviewers = get_top_reviewers(conn, min_reviews=30, limit=100)
    save_df_to_csv(top_reviewers, "top_reviewers.csv")

