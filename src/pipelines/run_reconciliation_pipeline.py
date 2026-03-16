from __future__ import annotations

import logging

from src.config.settings import db_settings
from src.repositories.base_repository import DDL_DIR, get_connection, run_ddl_files
from src.repositories.reconciliation_repository import (
    get_reconciliation_stats,
    link_reviews_to_books,
    populate_normalized_titles,
)


logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


def ensure_reconciliation_ddl() -> None:
    ddl_files = sorted(DDL_DIR.glob("*.sql"))
    if not ddl_files:
        raise FileNotFoundError(f"No DDL files found in {DDL_DIR}")

    with get_connection() as conn:
        logger.info("Running DDL files (including reconciliation DDL).")
        run_ddl_files(conn, ddl_files)


def run_reconciliation_pipeline() -> None:
    _configure_logging()
    logger.info(
        "Starting reconciliation pipeline using DSN %s",
        db_settings.dsn,
    )

    ensure_reconciliation_ddl()

    with get_connection() as conn:
        populate_normalized_titles(conn)
        linked = link_reviews_to_books(conn)
        logger.info("Total reviews linked to books in this run: %d", linked)
        get_reconciliation_stats(conn)

    logger.info("Reconciliation pipeline completed.")


def main() -> None:
    run_reconciliation_pipeline()


if __name__ == "__main__":
    main()

