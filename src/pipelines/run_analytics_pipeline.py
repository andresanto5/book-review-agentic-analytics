from __future__ import annotations

import logging

from src.config.settings import db_settings
from src.analytics.author_insights import run_author_insights
from src.analytics.book_insights import run_book_insights
from src.analytics.category_insights import run_category_insights
from src.analytics.distribution_insights import run_distribution_insights
from src.analytics.reviewer_insights import run_reviewer_insights
from src.repositories.base_repository import get_connection


logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


def run_analytics_pipeline() -> None:
    _configure_logging()
    logger.info(
        "Starting analytics pipeline using DSN %s",
        db_settings.dsn,
    )

    with get_connection() as conn:
        run_author_insights(conn)
        run_category_insights(conn)
        run_book_insights(conn)
        run_reviewer_insights(conn)
        run_distribution_insights(conn)

    logger.info("Analytics pipeline completed.")


def main() -> None:
    run_analytics_pipeline()


if __name__ == "__main__":
    main()

