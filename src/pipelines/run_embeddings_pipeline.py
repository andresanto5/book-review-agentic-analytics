from __future__ import annotations

import argparse
import logging
import math
import time
from pathlib import Path
from typing import Iterable, List, Set

import pandas as pd

from src.config.settings import db_settings
from src.embeddings.embedding_client import get_embedding_client
from src.repositories.base_repository import get_connection
from src.repositories.vector_repository import (
    ReviewEmbeddingRecord,
    insert_embeddings,
    truncate_review_embeddings,
)


logger = logging.getLogger(__name__)


REVIEW_DOCUMENTS_PARQUET = Path("data/processed/review_documents.parquet")
PIPELINE_VERSION = "v1"


def _configure_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


def _run_review_embeddings_ddl() -> None:
    ddl_path = Path("sql/ddl/008_create_review_embeddings.sql")
    if not ddl_path.is_file():
        raise FileNotFoundError(f"DDL file not found: {ddl_path}")

    sql = ddl_path.read_text(encoding="utf-8")
    with get_connection() as conn:
        logger.info("Running DDL from '%s'.", ddl_path)
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        logger.info("DDL executed.")


def _yield_batches(
    df: pd.DataFrame, batch_size: int
) -> Iterable[tuple[int, pd.DataFrame]]:
    total = len(df)
    num_batches = math.ceil(total / batch_size) if batch_size > 0 else 1
    for i in range(num_batches):
        start = i * batch_size
        end = min(start + batch_size, total)
        yield i + 1, df.iloc[start:end]


def _get_existing_review_pks(conn: Connection) -> Set[int]:
    with conn.cursor() as cur:
        cur.execute("SELECT review_pk FROM app.review_embeddings;")
        rows = cur.fetchall()
    existing = {int(r[0]) for r in rows}
    logger.info("Found %d existing review_embeddings rows.", len(existing))
    return existing


def run_embeddings_pipeline(
    limit: int | None,
    batch_size: int,
    truncate: bool,
    incremental: bool,
) -> None:
    _configure_logging()
    start_time = time.perf_counter()
    logger.info("Starting embedding pipeline using DSN %s", db_settings.dsn)
    logger.info("Review documents source: %s", REVIEW_DOCUMENTS_PARQUET)

    _run_review_embeddings_ddl()

    df = pd.read_parquet(REVIEW_DOCUMENTS_PARQUET)
    logger.info("Loaded review_documents parquet with shape %s", df.shape)

    if limit is not None and limit > 0:
        df = df.head(limit)
        logger.info("Applying limit=%d. New shape=%s", limit, df.shape)

    if truncate and incremental:
        logger.warning(
            "--truncate and --incremental used together; running full refresh (truncate takes precedence)."
        )
        incremental = False

    client = get_embedding_client()
    logger.info(
        "Using embedding model '%s' (dimension=%d).",
        client.model_name,
        client.embedding_dimension,
    )

    with get_connection() as conn:
        if truncate:
            truncate_review_embeddings(conn)

        if incremental:
            existing_pks = _get_existing_review_pks(conn)
            before = len(df)
            df = df[~df["review_pk"].isin(existing_pks)]
            after = len(df)
            logger.info(
                "Incremental mode: filtered out %d already-embedded reviews. To process=%d.",
                before - after,
                after,
            )

        total_docs = len(df)
        if total_docs == 0:
            logger.info("No documents to process after filtering. Exiting.")
            return

        logger.info("Total documents to embed: %d", total_docs)
        logger.info("Embedding batch size: %d", batch_size)

        processed = 0
        inserted_total = 0

        for batch_idx, batch_df in _yield_batches(df, batch_size):
            batch_start_time = time.perf_counter()
            texts: List[str] = batch_df["review_document"].astype(str).tolist()
            review_pks: List[int] = batch_df["review_pk"].astype(int).tolist()
            book_pks: List[int] = batch_df["book_pk"].astype(int).tolist()

            embeddings = client.embed_texts(texts, batch_size=batch_size)

            records: List[ReviewEmbeddingRecord] = [
                {
                    "review_pk": r_pk,
                    "book_pk": b_pk,
                    "embedding": emb,
                    "model_name": client.model_name,
                    "embedding_dimension": client.embedding_dimension,
                    "pipeline_version": PIPELINE_VERSION,
                }
                for r_pk, b_pk, emb in zip(review_pks, book_pks, embeddings)
            ]

            inserted = insert_embeddings(conn, records, batch_size=batch_size)
            batch_elapsed = time.perf_counter() - batch_start_time
            processed += len(batch_df)
            inserted_total += inserted

            elapsed_total = time.perf_counter() - start_time
            docs_per_sec = processed / elapsed_total if elapsed_total > 0 else 0.0
            remaining = total_docs - processed
            eta_sec = remaining / docs_per_sec if docs_per_sec > 0 else float("inf")

            logger.info(
                "Processed batch %d: %d docs, %.2fs, %.1f docs/s, cumulative processed=%d, cumulative inserted=%d, ETA=%.1fs",
                batch_idx,
                len(batch_df),
                batch_elapsed,
                docs_per_sec,
                processed,
                inserted_total,
                eta_sec,
            )

    total_elapsed = time.perf_counter() - start_time
    logger.info(
        "Embedding pipeline completed. Total processed=%d, total inserted=%d, total time=%.2fs (%.1f docs/s).",
        processed,
        inserted_total,
        total_elapsed,
        processed / total_elapsed if total_elapsed > 0 else 0.0,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate and store embeddings for review_documents using pgvector."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N documents from the parquet file (for testing).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=128,
        help="Batch size for embedding generation and insertion.",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Truncate app.review_embeddings before inserting (full refresh).",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Only embed reviews that do not yet have embeddings.",
    )
    args = parser.parse_args()

    run_embeddings_pipeline(
        limit=args.limit,
        batch_size=args.batch_size,
        truncate=args.truncate,
        incremental=args.incremental,
    )


if __name__ == "__main__":
    main()

