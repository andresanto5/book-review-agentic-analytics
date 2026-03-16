from __future__ import annotations

import logging
from typing import Iterable, Sequence, Any

import pandas as pd
from psycopg import Connection

from src.repositories.base_repository import execute_batch


logger = logging.getLogger(__name__)


INSERT_REVIEW_SQL = """
INSERT INTO app.reviews (
    book_id_raw,
    title,
    price,
    user_id,
    profile_name,
    score,
    review_time_unix,
    review_summary,
    review_text,
    review_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
"""


def _to_python(value: Any) -> Any | None:
    if pd.isna(value):
        return None
    return value


def prepare_reviews_params(df: pd.DataFrame) -> Iterable[Sequence[object | None]]:
    for _, row in df.iterrows():
        yield (
            _to_python(row.get("book_id_raw")),
            _to_python(row.get("title")),
            _to_python(row.get("price")),
            _to_python(row.get("user_id")),
            _to_python(row.get("profile_name")),
            _to_python(row.get("score")),
            _to_python(row.get("review_time_unix")),
            _to_python(row.get("review_summary")),
            _to_python(row.get("review_text")),
            _to_python(row.get("review_time")),
        )


def insert_reviews(conn: Connection, df: pd.DataFrame, batch_size: int = 1_000) -> int:
    logger.info("Inserting reviews into database (rows=%d).", len(df))
    params = list(prepare_reviews_params(df))
    execute_batch(conn, INSERT_REVIEW_SQL, params, page_size=batch_size)
    logger.info("Finished inserting reviews.")
    return len(df)


