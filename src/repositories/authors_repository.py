from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Sequence, Tuple, Any

import numpy as np
import pandas as pd
from psycopg import Connection

from src.repositories.base_repository import execute_batch


logger = logging.getLogger(__name__)


INSERT_AUTHOR_SQL = """
INSERT INTO app.authors (author_name)
VALUES (%s)
ON CONFLICT (author_name) DO NOTHING
RETURNING author_pk, author_name
"""


INSERT_BOOK_AUTHOR_SQL = """
INSERT INTO app.book_authors (book_pk, author_pk)
VALUES (%s, %s)
ON CONFLICT DO NOTHING
"""


def _normalize_list_field(value: Any) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, (list, tuple, set, np.ndarray)):
        iterable = value
    else:
        iterable = [value]
    result: list[str] = []
    for item in iterable:
        name = str(item).strip()
        if name:
            result.append(name)
    return result


def extract_unique_authors(df: pd.DataFrame) -> List[str]:
    authors_set: set[str] = set()
    for authors_list in df["authors"]:
        for author in _normalize_list_field(authors_list):
            authors_set.add(author)
    return sorted(authors_set)


def insert_authors(conn: Connection, unique_authors: Iterable[str]) -> Dict[str, int]:
    logger.info("Inserting unique authors (count=%d).", len(list(unique_authors)))
    params = [(name,) for name in unique_authors]
    if not params:
        return {}

    with conn.cursor() as cur:
        execute_batch(conn, INSERT_AUTHOR_SQL, params)
        cur.execute("SELECT author_pk, author_name FROM app.authors")
        rows = cur.fetchall()

    mapping = {row[1]: row[0] for row in rows}
    logger.info("Authors mapping size: %d", len(mapping))
    return mapping


def prepare_book_author_params(
    df: pd.DataFrame, author_mapping: Dict[str, int]
) -> Iterable[Tuple[int, int]]:
    for book_idx, authors_list in zip(df.index, df["authors"]):
        book_pk = int(book_idx) + 1  # assuming sequential insertion order
        for name in _normalize_list_field(authors_list):
            author_pk = author_mapping.get(name)
            if author_pk is not None:
                yield (book_pk, author_pk)


def insert_book_authors(
    conn: Connection,
    df: pd.DataFrame,
    author_mapping: Dict[str, int],
    batch_size: int = 1_000,
) -> int:
    params = list(prepare_book_author_params(df, author_mapping))
    logger.info("Inserting book_authors relationships (rows=%d).", len(params))
    if params:
        execute_batch(conn, INSERT_BOOK_AUTHOR_SQL, params, page_size=batch_size)
    return len(params)


