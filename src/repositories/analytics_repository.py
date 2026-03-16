from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

import pandas as pd
from psycopg import Connection


logger = logging.getLogger(__name__)


ANALYTICS_DIR = Path("data/processed/analytics")


def ensure_analytics_dir() -> None:
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)


def save_df_to_csv(df: pd.DataFrame, filename: str) -> Path:
    ensure_analytics_dir()
    output_path = ANALYTICS_DIR / filename
    df.to_csv(output_path, index=False)
    logger.info("Saved %d rows to '%s'.", len(df), output_path)
    return output_path


def fetch_dataframe(conn: Connection, sql: str, params: Dict[str, Any] | None = None) -> pd.DataFrame:
    return pd.read_sql_query(sql, conn, params=params)


def get_top_authors_by_avg_score(conn: Connection, min_reviews: int = 30, limit: int = 100) -> pd.DataFrame:
    sql = """
    SELECT
        a.author_pk,
        a.author_name,
        COUNT(r.review_pk) AS review_count,
        AVG(r.score) AS avg_score,
        STDDEV_POP(r.score) AS score_stddev
    FROM app.authors a
    JOIN app.book_authors ba ON a.author_pk = ba.author_pk
    JOIN app.books b ON b.book_pk = ba.book_pk
    JOIN app.reviews r ON r.book_pk = b.book_pk
    WHERE r.book_pk IS NOT NULL
      AND r.score IS NOT NULL
    GROUP BY a.author_pk, a.author_name
    HAVING COUNT(r.review_pk) >= %(min_reviews)s
    ORDER BY avg_score DESC
    LIMIT %(limit)s;
    """
    return fetch_dataframe(conn, sql, {"min_reviews": min_reviews, "limit": limit})


def get_top_authors_by_review_volume(conn: Connection, limit: int = 100) -> pd.DataFrame:
    sql = """
    SELECT
        a.author_pk,
        a.author_name,
        COUNT(r.review_pk) AS review_count,
        AVG(r.score) AS avg_score
    FROM app.authors a
    JOIN app.book_authors ba ON a.author_pk = ba.author_pk
    JOIN app.books b ON b.book_pk = ba.book_pk
    JOIN app.reviews r ON r.book_pk = b.book_pk
    WHERE r.book_pk IS NOT NULL
      AND r.score IS NOT NULL
    GROUP BY a.author_pk, a.author_name
    ORDER BY review_count DESC
    LIMIT %(limit)s;
    """
    return fetch_dataframe(conn, sql, {"limit": limit})


def get_most_polarized_authors(conn: Connection, min_reviews: int = 30, limit: int = 100) -> pd.DataFrame:
    sql = """
    SELECT
        a.author_pk,
        a.author_name,
        COUNT(r.review_pk) AS review_count,
        AVG(r.score) AS avg_score,
        STDDEV_POP(r.score) AS score_stddev
    FROM app.authors a
    JOIN app.book_authors ba ON a.author_pk = ba.author_pk
    JOIN app.books b ON b.book_pk = ba.book_pk
    JOIN app.reviews r ON r.book_pk = b.book_pk
    WHERE r.book_pk IS NOT NULL
      AND r.score IS NOT NULL
    GROUP BY a.author_pk, a.author_name
    HAVING COUNT(r.review_pk) >= %(min_reviews)s
    ORDER BY score_stddev DESC
    LIMIT %(limit)s;
    """
    return fetch_dataframe(conn, sql, {"min_reviews": min_reviews, "limit": limit})


def get_top_categories_by_avg_score(conn: Connection, min_reviews: int = 30, limit: int = 100) -> pd.DataFrame:
    sql = """
    SELECT
        c.category_pk,
        c.category_name,
        COUNT(r.review_pk) AS review_count,
        AVG(r.score) AS avg_score,
        STDDEV_POP(r.score) AS score_stddev
    FROM app.categories c
    JOIN app.book_categories bc ON c.category_pk = bc.category_pk
    JOIN app.books b ON b.book_pk = bc.book_pk
    JOIN app.reviews r ON r.book_pk = b.book_pk
    WHERE r.book_pk IS NOT NULL
      AND r.score IS NOT NULL
    GROUP BY c.category_pk, c.category_name
    HAVING COUNT(r.review_pk) >= %(min_reviews)s
    ORDER BY avg_score DESC
    LIMIT %(limit)s;
    """
    return fetch_dataframe(conn, sql, {"min_reviews": min_reviews, "limit": limit})


def get_top_categories_by_review_volume(conn: Connection, limit: int = 100) -> pd.DataFrame:
    sql = """
    SELECT
        c.category_pk,
        c.category_name,
        COUNT(r.review_pk) AS review_count,
        AVG(r.score) AS avg_score
    FROM app.categories c
    JOIN app.book_categories bc ON c.category_pk = bc.category_pk
    JOIN app.books b ON b.book_pk = bc.book_pk
    JOIN app.reviews r ON r.book_pk = b.book_pk
    WHERE r.book_pk IS NOT NULL
      AND r.score IS NOT NULL
    GROUP BY c.category_pk, c.category_name
    ORDER BY review_count DESC
    LIMIT %(limit)s;
    """
    return fetch_dataframe(conn, sql, {"limit": limit})


def get_most_polarized_categories(conn: Connection, min_reviews: int = 30, limit: int = 100) -> pd.DataFrame:
    sql = """
    SELECT
        c.category_pk,
        c.category_name,
        COUNT(r.review_pk) AS review_count,
        AVG(r.score) AS avg_score,
        STDDEV_POP(r.score) AS score_stddev
    FROM app.categories c
    JOIN app.book_categories bc ON c.category_pk = bc.category_pk
    JOIN app.books b ON b.book_pk = bc.book_pk
    JOIN app.reviews r ON r.book_pk = b.book_pk
    WHERE r.book_pk IS NOT NULL
      AND r.score IS NOT NULL
    GROUP BY c.category_pk, c.category_name
    HAVING COUNT(r.review_pk) >= %(min_reviews)s
    ORDER BY score_stddev DESC
    LIMIT %(limit)s;
    """
    return fetch_dataframe(conn, sql, {"min_reviews": min_reviews, "limit": limit})


def get_top_books_by_review_volume(conn: Connection, limit: int = 100) -> pd.DataFrame:
    sql = """
    SELECT
        b.book_pk,
        b.title,
        b.publisher,
        b.published_year,
        COUNT(r.review_pk) AS review_count,
        AVG(r.score) AS avg_score
    FROM app.books b
    JOIN app.reviews r ON r.book_pk = b.book_pk
    WHERE r.book_pk IS NOT NULL
      AND r.score IS NOT NULL
    GROUP BY b.book_pk, b.title, b.publisher, b.published_year
    ORDER BY review_count DESC
    LIMIT %(limit)s;
    """
    return fetch_dataframe(conn, sql, {"limit": limit})


def get_top_books_by_avg_score(conn: Connection, min_reviews: int = 30, limit: int = 100) -> pd.DataFrame:
    sql = """
    SELECT
        b.book_pk,
        b.title,
        b.publisher,
        b.published_year,
        COUNT(r.review_pk) AS review_count,
        AVG(r.score) AS avg_score,
        STDDEV_POP(r.score) AS score_stddev
    FROM app.books b
    JOIN app.reviews r ON r.book_pk = b.book_pk
    WHERE r.book_pk IS NOT NULL
      AND r.score IS NOT NULL
    GROUP BY b.book_pk, b.title, b.publisher, b.published_year
    HAVING COUNT(r.review_pk) >= %(min_reviews)s
    ORDER BY avg_score DESC
    LIMIT %(limit)s;
    """
    return fetch_dataframe(conn, sql, {"min_reviews": min_reviews, "limit": limit})


def get_most_polarized_books(conn: Connection, min_reviews: int = 30, limit: int = 100) -> pd.DataFrame:
    sql = """
    SELECT
        b.book_pk,
        b.title,
        b.publisher,
        b.published_year,
        COUNT(r.review_pk) AS review_count,
        AVG(r.score) AS avg_score,
        STDDEV_POP(r.score) AS score_stddev
    FROM app.books b
    JOIN app.reviews r ON r.book_pk = b.book_pk
    WHERE r.book_pk IS NOT NULL
      AND r.score IS NOT NULL
    GROUP BY b.book_pk, b.title, b.publisher, b.published_year
    HAVING COUNT(r.review_pk) >= %(min_reviews)s
    ORDER BY score_stddev DESC
    LIMIT %(limit)s;
    """
    return fetch_dataframe(conn, sql, {"min_reviews": min_reviews, "limit": limit})


def get_top_reviewers(conn: Connection, min_reviews: int = 30, limit: int = 100) -> pd.DataFrame:
    sql = """
    SELECT
        r.user_id,
        COALESCE(r.profile_name, '') AS profile_name,
        COUNT(r.review_pk) AS review_count,
        AVG(r.score) AS avg_score,
        STDDEV_POP(r.score) AS score_stddev,
        AVG(CHAR_LENGTH(COALESCE(r.review_text, ''))) AS avg_review_length
    FROM app.reviews r
    WHERE r.book_pk IS NOT NULL
      AND r.score IS NOT NULL
    GROUP BY r.user_id, COALESCE(r.profile_name, '')
    HAVING COUNT(r.review_pk) >= %(min_reviews)s
    ORDER BY review_count DESC, avg_score DESC
    LIMIT %(limit)s;
    """
    return fetch_dataframe(conn, sql, {"min_reviews": min_reviews, "limit": limit})


def get_score_distribution(conn: Connection) -> pd.DataFrame:
    sql = """
    SELECT
        r.score,
        COUNT(*) AS review_count
    FROM app.reviews r
    WHERE r.book_pk IS NOT NULL
      AND r.score IS NOT NULL
    GROUP BY r.score
    ORDER BY r.score;
    """
    return fetch_dataframe(conn, sql)


def get_review_length_stats(conn: Connection) -> pd.DataFrame:
    sql = """
    SELECT
        COUNT(*) AS review_count,
        AVG(len) AS avg_length,
        STDDEV_POP(len) AS std_length,
        MIN(len) AS min_length,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY len) AS p25_length,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY len) AS median_length,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY len) AS p75_length,
        MAX(len) AS max_length
    FROM (
        SELECT CHAR_LENGTH(COALESCE(review_text, '')) AS len
        FROM app.reviews r
        WHERE r.book_pk IS NOT NULL
    ) t;
    """
    return fetch_dataframe(conn, sql)


def get_reviews_by_year(conn: Connection) -> pd.DataFrame:
    sql = """
    SELECT
        EXTRACT(YEAR FROM r.review_time) AS review_year,
        COUNT(*) AS review_count,
        AVG(r.score) AS avg_score
    FROM app.reviews r
    WHERE r.book_pk IS NOT NULL
      AND r.review_time IS NOT NULL
      AND r.score IS NOT NULL
    GROUP BY EXTRACT(YEAR FROM r.review_time)
    ORDER BY review_year;
    """
    return fetch_dataframe(conn, sql)


