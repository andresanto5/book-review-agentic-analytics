from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Sequence, Tuple, Any

import numpy as np
import pandas as pd
from psycopg import Connection

from src.repositories.base_repository import execute_batch


logger = logging.getLogger(__name__)


INSERT_CATEGORY_SQL = """
INSERT INTO app.categories (category_name)
VALUES (%s)
ON CONFLICT (category_name) DO NOTHING
RETURNING category_pk, category_name
"""


INSERT_BOOK_CATEGORY_SQL = """
INSERT INTO app.book_categories (book_pk, category_pk)
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


def extract_unique_categories(df: pd.DataFrame) -> List[str]:
    categories_set: set[str] = set()
    for categories_list in df["categories"]:
        for name in _normalize_list_field(categories_list):
            categories_set.add(name)
    return sorted(categories_set)


def insert_categories(
    conn: Connection, unique_categories: Iterable[str]
) -> Dict[str, int]:
    logger.info("Inserting unique categories (count=%d).", len(list(unique_categories)))
    params = [(name,) for name in unique_categories]
    if not params:
        return {}

    with conn.cursor() as cur:
        execute_batch(conn, INSERT_CATEGORY_SQL, params)
        cur.execute("SELECT category_pk, category_name FROM app.categories")
        rows = cur.fetchall()

    mapping = {row[1]: row[0] for row in rows}
    logger.info("Categories mapping size: %d", len(mapping))
    return mapping


def prepare_book_category_params(
    df: pd.DataFrame, category_mapping: Dict[str, int]
) -> Iterable[Tuple[int, int]]:
    for book_idx, categories_list in zip(df.index, df["categories"]):
        book_pk = int(book_idx) + 1  # assuming sequential insertion order
        for name in _normalize_list_field(categories_list):
            category_pk = category_mapping.get(name)
            if category_pk is not None:
                yield (book_pk, category_pk)


def insert_book_categories(
    conn: Connection,
    df: pd.DataFrame,
    category_mapping: Dict[str, int],
    batch_size: int = 1_000,
) -> int:
    params = list(prepare_book_category_params(df, category_mapping))
    logger.info("Inserting book_categories relationships (rows=%d).", len(params))
    if params:
        execute_batch(conn, INSERT_BOOK_CATEGORY_SQL, params, page_size=batch_size)
    return len(params)


