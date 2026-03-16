from __future__ import annotations

import logging

from src.config.settings import db_settings
from src.processing.build_review_document import (
    add_review_document_column,
    save_review_documents,
)
from src.repositories.base_repository import get_connection
from src.repositories.review_document_repository import fetch_review_documents


logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


def run_build_review_document_pipeline() -> None:
    _configure_logging()
    logger.info(
        "Starting build-review-document pipeline using DSN %s",
        db_settings.dsn,
    )

    with get_connection() as conn:
        df = fetch_review_documents(conn)
        logger.info("Columns fetched from database: %s", list(df.columns))
        df_with_doc = add_review_document_column(df)
        save_review_documents(df_with_doc)
        logger.info("Exported %d review documents.", len(df_with_doc))
        logger.info("Final columns: %s", list(df_with_doc.columns))

    logger.info("Build-review-document pipeline completed.")


def main() -> None:
    run_build_review_document_pipeline()


if __name__ == "__main__":
    main()

