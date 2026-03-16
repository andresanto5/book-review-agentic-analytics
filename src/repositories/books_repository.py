from __future__ import annotations

import logging
from typing import Iterable, Sequence, Any

import pandas as pd
from psycopg import Connection

from src.repositories.base_repository import execute_batch


logger = logging.getLogger(__name__)


INSERT_BOOK_SQL = """
INSERT INTO app.books (
    title,
    description,
    image_url,
    preview_link,
    publisher,
    published_date_raw,
    info_link,
    ratings_count,
    published_date_parsed,
    published_year
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
) RETURNING book_pk
"""


def _to_python(value: Any) -> Any | None:
    # Converte pandas NA/NaN/NaT para None, mantendo tipos nativos.
    if pd.isna(value):
        return None
    return value


def prepare_books_params(df: pd.DataFrame) -> Iterable[Sequence[object | None]]:
    for _, row in df.iterrows():
        yield (
            _to_python(row.get("title")),
            _to_python(row.get("description")),
            _to_python(row.get("image_url")),
            _to_python(row.get("preview_link")),
            _to_python(row.get("publisher")),
            _to_python(row.get("published_date_raw")),
            _to_python(row.get("info_link")),
            _to_python(row.get("ratings_count")),
            _to_python(row.get("published_date_parsed")),
            _to_python(row.get("published_year")),
        )


def insert_books(conn: Connection, df: pd.DataFrame, batch_size: int = 1_000) -> int:
    logger.info("Inserting books into database (rows=%d).", len(df))
    params = list(prepare_books_params(df))
    execute_batch(conn, INSERT_BOOK_SQL, params, page_size=batch_size)
    logger.info("Finished inserting books.")
    return len(df)


