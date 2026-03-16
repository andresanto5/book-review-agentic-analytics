from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, Sequence, List

import psycopg
from psycopg import Connection

from src.config.settings import db_settings


logger = logging.getLogger(__name__)


DDL_DIR = Path("sql/ddl")


def _configure_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


def get_connection() -> Connection:
    _configure_logging()
    logger.info("Opening database connection to %s", db_settings.dsn)
    return psycopg.connect(db_settings.dsn)


def run_ddl_files(conn: Connection, ddl_files: Sequence[Path]) -> None:
    with conn.cursor() as cur:
        for ddl_path in ddl_files:
            logger.info("Running DDL file '%s'", ddl_path)
            sql = ddl_path.read_text(encoding="utf-8")
            cur.execute(sql)
    conn.commit()


def execute_batch(
    conn: Connection,
    sql: str,
    params_seq: Iterable[Sequence[object | None]],
    page_size: int = 1_000,
) -> None:
    """
    Simple batching implementation using cursor.executemany.
    """
    with conn.cursor() as cur:
        batch: List[Sequence[object | None]] = []
        for params in params_seq:
            batch.append(params)
            if len(batch) >= page_size:
                cur.executemany(sql, batch)
                batch.clear()
        if batch:
            cur.executemany(sql, batch)
    conn.commit()


def truncate_app_tables(conn: Connection) -> None:
    """
    Truncate all tables in the app schema in a safe order,
    restarting identities and cascading to dependent objects.
    """
    logger.info("Truncating app schema tables for full reload.")
    sql = """
    TRUNCATE TABLE
        app.book_authors,
        app.book_categories,
        app.reviews,
        app.authors,
        app.categories,
        app.books
    RESTART IDENTITY CASCADE;
    """
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    logger.info("Truncate completed.")


