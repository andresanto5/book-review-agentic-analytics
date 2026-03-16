from __future__ import annotations

import logging

import pandas as pd
from psycopg import Connection


logger = logging.getLogger(__name__)


def fetch_review_documents(conn: Connection) -> pd.DataFrame:
    """
    Fetch consolidated review + book metadata for reconciled reviews.
    One row per review_pk.
    """
    sql = """
    WITH book_meta AS (
        SELECT
            b.book_pk,
            b.title,
            STRING_AGG(DISTINCT a.author_name, '; ' ORDER BY a.author_name) AS authors,
            STRING_AGG(DISTINCT c.category_name, '; ' ORDER BY c.category_name) AS categories
        FROM app.books b
        LEFT JOIN app.book_authors ba ON b.book_pk = ba.book_pk
        LEFT JOIN app.authors a ON a.author_pk = ba.author_pk
        LEFT JOIN app.book_categories bc ON b.book_pk = bc.book_pk
        LEFT JOIN app.categories c ON c.category_pk = bc.category_pk
        GROUP BY b.book_pk, b.title
    )
    SELECT
        r.review_pk,
        r.book_pk,
        bm.title,
        bm.authors,
        bm.categories,
        r.score,
        r.review_summary,
        r.review_text,
        r.review_time
    FROM app.reviews r
    JOIN book_meta bm ON bm.book_pk = r.book_pk
    WHERE r.book_pk IS NOT NULL;
    """
    logger.info("Fetching consolidated review documents from database.")
    df = pd.read_sql_query(sql, conn)
    logger.info("Fetched %d review rows.", len(df))
    return df


