from __future__ import annotations

import logging
from typing import Any, Dict, List, TypedDict

from psycopg import Connection


logger = logging.getLogger(__name__)


class BookSummary(TypedDict):
    book_pk: int
    title: str
    publisher: str | None
    published_year: int | None
    review_count: int
    avg_score: float


class CategorySummary(TypedDict):
    category_pk: int
    category_name: str
    review_count: int
    avg_score: float
    score_stddev: float


def get_worst_rated_categories(
    conn: Connection, min_reviews: int = 100, limit: int = 10
) -> List[CategorySummary]:
    """
    Categories with lowest average score and at least min_reviews reviews.
    """
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
    ORDER BY avg_score ASC
    LIMIT %(limit)s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, {"min_reviews": min_reviews, "limit": limit})
        rows = cur.fetchall()

    results: List[CategorySummary] = [
        CategorySummary(
            category_pk=row[0],
            category_name=row[1],
            review_count=row[2],
            avg_score=round(float(row[3]) if row[3] is not None else 0.0, 2),
            score_stddev=float(row[4]) if row[4] is not None else 0.0,
        )
        for row in rows
    ]
    logger.info(
        "Tool get_worst_rated_categories(min_reviews=%d, limit=%d) returned %d rows.",
        min_reviews,
        limit,
        len(results),
    )
    return results


def get_top_books_by_review_volume(
    conn: Connection, limit: int = 10
) -> List[BookSummary]:
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
    with conn.cursor() as cur:
        cur.execute(sql, {"limit": limit})
        rows = cur.fetchall()

    results: List[BookSummary] = [
        BookSummary(
            book_pk=row[0],
            title=row[1],
            publisher=row[2],
            published_year=row[3],
            review_count=row[4],
            avg_score=round(float(row[5]) if row[5] is not None else 0.0, 2),
        )
        for row in rows
    ]
    logger.info("Tool get_top_books_by_review_volume returned %d rows.", len(results))
    return results


def get_top_books_by_avg_score(
    conn: Connection, min_reviews: int = 100, limit: int = 10
) -> List[BookSummary]:
    """
    Books with highest average score and at least min_reviews.
    Direct ranking by mean rating (no proxy interpretation).
    """
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
    HAVING COUNT(r.review_pk) >= %(min_reviews)s
    ORDER BY avg_score DESC, review_count DESC
    LIMIT %(limit)s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, {"min_reviews": min_reviews, "limit": limit})
        rows = cur.fetchall()

    results: List[BookSummary] = [
        BookSummary(
            book_pk=row[0],
            title=row[1],
            publisher=row[2],
            published_year=row[3],
            review_count=row[4],
            avg_score=round(float(row[5]) if row[5] is not None else 0.0, 2),
        )
        for row in rows
    ]
    logger.info(
        "Tool get_top_books_by_avg_score(min_reviews=%d, limit=%d) returned %d rows.",
        min_reviews,
        limit,
        len(results),
    )
    return results


def get_top_categories_by_avg_score(
    conn: Connection, min_reviews: int = 100, limit: int = 10
) -> List[CategorySummary]:
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
    with conn.cursor() as cur:
        cur.execute(sql, {"min_reviews": min_reviews, "limit": limit})
        rows = cur.fetchall()

    results: List[CategorySummary] = [
        CategorySummary(
            category_pk=row[0],
            category_name=row[1],
            review_count=row[2],
            avg_score=round(float(row[3]) if row[3] is not None else 0.0, 2),
            score_stddev=float(row[4]) if row[4] is not None else 0.0,
        )
        for row in rows
    ]
    logger.info(
        "Tool get_top_categories_by_avg_score returned %d rows.", len(results)
    )
    return results


def get_most_recommended_books(
    conn: Connection, min_reviews: int = 100, limit: int = 10
) -> List[BookSummary]:
    """
    Books with highest average score and at least min_reviews (proxy for
    'most recommended' / best reception). No sales data; uses reviews only.
    """
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
    HAVING COUNT(r.review_pk) >= %(min_reviews)s
    ORDER BY avg_score DESC, review_count DESC
    LIMIT %(limit)s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, {"min_reviews": min_reviews, "limit": limit})
        rows = cur.fetchall()

    results: List[BookSummary] = [
        BookSummary(
            book_pk=row[0],
            title=row[1],
            publisher=row[2],
            published_year=row[3],
            review_count=row[4],
            avg_score=round(float(row[5]) if row[5] is not None else 0.0, 2),
        )
        for row in rows
    ]
    logger.info(
        "Tool get_most_recommended_books(min_reviews=%d, limit=%d) returned %d rows.",
        min_reviews,
        limit,
        len(results),
    )
    return results


def get_most_polarized_books(
    conn: Connection, min_reviews: int = 50, limit: int = 10
) -> List[BookSummary]:
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
    with conn.cursor() as cur:
        cur.execute(sql, {"min_reviews": min_reviews, "limit": limit})
        rows = cur.fetchall()

    results: List[BookSummary] = [
        BookSummary(
            book_pk=row[0],
            title=row[1],
            publisher=row[2],
            published_year=row[3],
            review_count=row[4],
            avg_score=round(float(row[5]) if row[5] is not None else 0.0, 2),
        )
        for row in rows
    ]
    logger.info("Tool get_most_polarized_books returned %d rows.", len(results))
    return results


def get_most_criticized_books(
    conn: Connection, min_negative_reviews: int = 20, limit: int = 10
) -> List[BookSummary]:
    """
    Books with the highest number of negative reviews (score <= 2),
    with at least min_negative_reviews. This captures VOLUME of criticism,
    not just lowest average score.
    """
    sql = """
    SELECT
        b.book_pk,
        b.title,
        b.publisher,
        b.published_year,
        COUNT(CASE WHEN r.score <= 2 THEN 1 END) AS negative_review_count,
        COUNT(r.review_pk) AS review_count,
        AVG(r.score) AS avg_score
    FROM app.books b
    JOIN app.reviews r ON r.book_pk = b.book_pk
    WHERE r.book_pk IS NOT NULL
      AND r.score IS NOT NULL
    GROUP BY b.book_pk, b.title, b.publisher, b.published_year
    HAVING COUNT(CASE WHEN r.score <= 2 THEN 1 END) >= %(min_negative_reviews)s
    ORDER BY negative_review_count DESC, avg_score ASC
    LIMIT %(limit)s;
    """
    with conn.cursor() as cur:
        cur.execute(
            sql,
            {"min_negative_reviews": min_negative_reviews, "limit": limit},
        )
        rows = cur.fetchall()

    results: List[BookSummary] = [
        BookSummary(
            book_pk=row[0],
            title=row[1],
            publisher=row[2],
            published_year=row[3],
            review_count=row[5],
            avg_score=round(float(row[6]) if row[6] is not None else 0.0, 2),
        )
        for row in rows
    ]
    logger.info(
        "Tool get_most_criticized_books(min_negative_reviews=%d, limit=%d) returned %d rows.",
        min_negative_reviews,
        limit,
        len(results),
    )
    return results


def get_lowest_rated_books(
    conn: Connection, min_reviews: int = 100, limit: int = 10
) -> List[BookSummary]:
    """
    Books with lowest average score and at least min_reviews (proxy for least recommended).
    """
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
    HAVING COUNT(r.review_pk) >= %(min_reviews)s
    ORDER BY avg_score ASC, review_count DESC
    LIMIT %(limit)s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, {"min_reviews": min_reviews, "limit": limit})
        rows = cur.fetchall()
    results: List[BookSummary] = [
        BookSummary(
            book_pk=row[0],
            title=row[1],
            publisher=row[2],
            published_year=row[3],
            review_count=row[4],
            avg_score=round(float(row[5]) if row[5] is not None else 0.0, 2),
        )
        for row in rows
    ]
    logger.info(
        "Tool get_lowest_rated_books(min_reviews=%d, limit=%d) returned %d rows.",
        min_reviews, limit, len(results),
    )
    return results


class AuthorSummary(TypedDict):
    author_pk: int
    author_name: str
    review_count: int
    avg_score: float


def get_worst_rated_authors(
    conn: Connection, min_reviews: int = 30, limit: int = 10
) -> List[AuthorSummary]:
    """
    Authors with lowest average review score (across their books' reviews),
    with at least min_reviews reviews per author.
    """
    sql = """
    SELECT
        a.author_pk,
        a.author_name,
        COUNT(r.review_pk) AS review_count,
        AVG(r.score) AS avg_score
    FROM app.authors a
    JOIN app.book_authors ba ON ba.author_pk = a.author_pk
    JOIN app.books b ON b.book_pk = ba.book_pk
    JOIN app.reviews r ON r.book_pk = b.book_pk
    WHERE r.score IS NOT NULL
    GROUP BY a.author_pk, a.author_name
    HAVING COUNT(r.review_pk) >= %(min_reviews)s
    ORDER BY avg_score ASC, review_count DESC
    LIMIT %(limit)s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, {"min_reviews": min_reviews, "limit": limit})
        rows = cur.fetchall()
    results: List[AuthorSummary] = [
        AuthorSummary(
            author_pk=row[0],
            author_name=row[1],
            review_count=row[2],
            avg_score=round(float(row[3]) if row[3] is not None else 0.0, 2),
        )
        for row in rows
    ]
    logger.info(
        "Tool get_worst_rated_authors(min_reviews=%d, limit=%d) returned %d rows.",
        min_reviews,
        limit,
        len(results),
    )
    return results


def get_top_authors_by_avg_score(
    conn: Connection, min_reviews: int = 30, limit: int = 10
) -> List[AuthorSummary]:
    """
    Authors with highest average review score (across their books' reviews), min_reviews per author.
    """
    sql = """
    SELECT
        a.author_pk,
        a.author_name,
        COUNT(r.review_pk) AS review_count,
        AVG(r.score) AS avg_score
    FROM app.authors a
    JOIN app.book_authors ba ON ba.author_pk = a.author_pk
    JOIN app.books b ON b.book_pk = ba.book_pk
    JOIN app.reviews r ON r.book_pk = b.book_pk
    WHERE r.score IS NOT NULL
    GROUP BY a.author_pk, a.author_name
    HAVING COUNT(r.review_pk) >= %(min_reviews)s
    ORDER BY avg_score DESC, review_count DESC
    LIMIT %(limit)s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, {"min_reviews": min_reviews, "limit": limit})
        rows = cur.fetchall()
    results: List[AuthorSummary] = [
        AuthorSummary(
            author_pk=row[0],
            author_name=row[1],
            review_count=row[2],
            avg_score=round(float(row[3]) if row[3] is not None else 0.0, 2),
        )
        for row in rows
    ]
    logger.info(
        "Tool get_top_authors_by_avg_score(min_reviews=%d, limit=%d) returned %d rows.",
        min_reviews, limit, len(results),
    )
    return results


def get_top_authors_by_review_volume(
    conn: Connection, limit: int = 10
) -> List[AuthorSummary]:
    """
    Authors with highest number of reviews (across their books).
    """
    sql = """
    SELECT
        a.author_pk,
        a.author_name,
        COUNT(r.review_pk) AS review_count,
        AVG(r.score) AS avg_score
    FROM app.authors a
    JOIN app.book_authors ba ON ba.author_pk = a.author_pk
    JOIN app.books b ON b.book_pk = ba.book_pk
    JOIN app.reviews r ON r.book_pk = b.book_pk
    WHERE r.score IS NOT NULL
    GROUP BY a.author_pk, a.author_name
    ORDER BY review_count DESC, avg_score DESC
    LIMIT %(limit)s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, {"limit": limit})
        rows = cur.fetchall()
    results: List[AuthorSummary] = [
        AuthorSummary(
            author_pk=row[0],
            author_name=row[1],
            review_count=row[2],
            avg_score=float(row[3]) if row[3] is not None else 0.0,
        )
        for row in rows
    ]
    logger.info(
        "Tool get_top_authors_by_review_volume(limit=%d) returned %d rows.",
        limit, len(results),
    )
    return results


class ReviewerSummary(TypedDict):
    user_id: str
    profile_name: str | None
    review_count: int
    avg_score: float
    avg_review_length: float
    distinct_books: int


def get_top_reviewers_by_review_volume(
    conn: Connection, min_reviews: int = 5, limit: int = 10
) -> List[ReviewerSummary]:
    """
    Reviewers (users) with the highest number of reviews.
    Ignores null/empty user_id.
    """
    sql = """
    SELECT
        r.user_id,
        MAX(r.profile_name) AS profile_name,
        COUNT(r.review_pk) AS review_count,
        ROUND(AVG(r.score)::numeric, 2) AS avg_score,
        ROUND(AVG(LENGTH(COALESCE(r.review_text, '')))::numeric, 2) AS avg_review_length,
        COUNT(DISTINCT r.book_pk) AS distinct_books
    FROM app.reviews r
    WHERE r.user_id IS NOT NULL AND TRIM(r.user_id) <> ''
    GROUP BY r.user_id
    HAVING COUNT(r.review_pk) >= %(min_reviews)s
    ORDER BY review_count DESC
    LIMIT %(limit)s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, {"min_reviews": min_reviews, "limit": limit})
        rows = cur.fetchall()
    results: List[ReviewerSummary] = [
        ReviewerSummary(
            user_id=str(row[0]),
            profile_name=row[1],
            review_count=row[2],
            avg_score=round(float(row[3]) if row[3] is not None else 0.0, 2),
            avg_review_length=round(float(row[4]) if row[4] is not None else 0.0, 2),
            distinct_books=row[5] or 0,
        )
        for row in rows
    ]
    logger.info(
        "Tool get_top_reviewers_by_review_volume(min_reviews=%d, limit=%d) returned %d rows.",
        min_reviews, limit, len(results),
    )
    return results


def get_reviewers_with_longest_reviews(
    conn: Connection, min_reviews: int = 3, limit: int = 10
) -> List[ReviewerSummary]:
    """
    Reviewers with highest average review_text length (most detailed reviews).
    """
    sql = """
    SELECT
        r.user_id,
        MAX(r.profile_name) AS profile_name,
        COUNT(r.review_pk) AS review_count,
        ROUND(AVG(r.score)::numeric, 2) AS avg_score,
        ROUND(AVG(LENGTH(COALESCE(r.review_text, '')))::numeric, 2) AS avg_review_length,
        COUNT(DISTINCT r.book_pk) AS distinct_books
    FROM app.reviews r
    WHERE r.user_id IS NOT NULL AND TRIM(r.user_id) <> ''
    GROUP BY r.user_id
    HAVING COUNT(r.review_pk) >= %(min_reviews)s
    ORDER BY avg_review_length DESC
    LIMIT %(limit)s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, {"min_reviews": min_reviews, "limit": limit})
        rows = cur.fetchall()
    results: List[ReviewerSummary] = [
        ReviewerSummary(
            user_id=str(row[0]),
            profile_name=row[1],
            review_count=row[2],
            avg_score=round(float(row[3]) if row[3] is not None else 0.0, 2),
            avg_review_length=round(float(row[4]) if row[4] is not None else 0.0, 2),
            distinct_books=row[5] or 0,
        )
        for row in rows
    ]
    logger.info(
        "Tool get_reviewers_with_longest_reviews(min_reviews=%d, limit=%d) returned %d rows.",
        min_reviews, limit, len(results),
    )
    return results


def get_most_critical_reviewers(
    conn: Connection, min_reviews: int = 5, limit: int = 10
) -> List[ReviewerSummary]:
    """
    Reviewers with lowest average score (most critical).
    """
    sql = """
    SELECT
        r.user_id,
        MAX(r.profile_name) AS profile_name,
        COUNT(r.review_pk) AS review_count,
        ROUND(AVG(r.score)::numeric, 2) AS avg_score,
        ROUND(AVG(LENGTH(COALESCE(r.review_text, '')))::numeric, 2) AS avg_review_length,
        COUNT(DISTINCT r.book_pk) AS distinct_books
    FROM app.reviews r
    WHERE r.user_id IS NOT NULL AND TRIM(r.user_id) <> ''
      AND r.score IS NOT NULL
    GROUP BY r.user_id
    HAVING COUNT(r.review_pk) >= %(min_reviews)s
    ORDER BY avg_score ASC, review_count DESC
    LIMIT %(limit)s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, {"min_reviews": min_reviews, "limit": limit})
        rows = cur.fetchall()
    results: List[ReviewerSummary] = [
        ReviewerSummary(
            user_id=str(row[0]),
            profile_name=row[1],
            review_count=row[2],
            avg_score=round(float(row[3]) if row[3] is not None else 0.0, 2),
            avg_review_length=round(float(row[4]) if row[4] is not None else 0.0, 2),
            distinct_books=row[5] or 0,
        )
        for row in rows
    ]
    logger.info(
        "Tool get_most_critical_reviewers(min_reviews=%d, limit=%d) returned %d rows.",
        min_reviews, limit, len(results),
    )
    return results


def get_most_positive_reviewers(
    conn: Connection, min_reviews: int = 5, limit: int = 10
) -> List[ReviewerSummary]:
    """
    Reviewers with highest average score (most positive).
    """
    sql = """
    SELECT
        r.user_id,
        MAX(r.profile_name) AS profile_name,
        COUNT(r.review_pk) AS review_count,
        ROUND(AVG(r.score)::numeric, 2) AS avg_score,
        ROUND(AVG(LENGTH(COALESCE(r.review_text, '')))::numeric, 2) AS avg_review_length,
        COUNT(DISTINCT r.book_pk) AS distinct_books
    FROM app.reviews r
    WHERE r.user_id IS NOT NULL AND TRIM(r.user_id) <> ''
      AND r.score IS NOT NULL
    GROUP BY r.user_id
    HAVING COUNT(r.review_pk) >= %(min_reviews)s
    ORDER BY avg_score DESC, review_count DESC
    LIMIT %(limit)s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, {"min_reviews": min_reviews, "limit": limit})
        rows = cur.fetchall()
    results: List[ReviewerSummary] = [
        ReviewerSummary(
            user_id=str(row[0]),
            profile_name=row[1],
            review_count=row[2],
            avg_score=round(float(row[3]) if row[3] is not None else 0.0, 2),
            avg_review_length=round(float(row[4]) if row[4] is not None else 0.0, 2),
            distinct_books=row[5] or 0,
        )
        for row in rows
    ]
    logger.info(
        "Tool get_most_positive_reviewers(min_reviews=%d, limit=%d) returned %d rows.",
        min_reviews, limit, len(results),
    )
    return results


def get_most_diverse_reviewers(
    conn: Connection, min_reviews: int = 5, limit: int = 10
) -> List[ReviewerSummary]:
    """
    Reviewers with highest count of distinct books reviewed.
    """
    sql = """
    SELECT
        r.user_id,
        MAX(r.profile_name) AS profile_name,
        COUNT(r.review_pk) AS review_count,
        ROUND(AVG(r.score)::numeric, 2) AS avg_score,
        ROUND(AVG(LENGTH(COALESCE(r.review_text, '')))::numeric, 2) AS avg_review_length,
        COUNT(DISTINCT r.book_pk) AS distinct_books
    FROM app.reviews r
    WHERE r.user_id IS NOT NULL AND TRIM(r.user_id) <> ''
    GROUP BY r.user_id
    HAVING COUNT(r.review_pk) >= %(min_reviews)s
    ORDER BY distinct_books DESC, review_count DESC
    LIMIT %(limit)s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, {"min_reviews": min_reviews, "limit": limit})
        rows = cur.fetchall()
    results: List[ReviewerSummary] = [
        ReviewerSummary(
            user_id=str(row[0]),
            profile_name=row[1],
            review_count=row[2],
            avg_score=round(float(row[3]) if row[3] is not None else 0.0, 2),
            avg_review_length=round(float(row[4]) if row[4] is not None else 0.0, 2),
            distinct_books=row[5] or 0,
        )
        for row in rows
    ]
    logger.info(
        "Tool get_most_diverse_reviewers(min_reviews=%d, limit=%d) returned %d rows.",
        min_reviews, limit, len(results),
    )
    return results


class BookSearchResult(TypedDict):
    book_pk: int
    title: str
    publisher: str | None
    published_year: int | None
    review_count: int


class ReviewContext(TypedDict):
    review_pk: int
    book_pk: int
    title: str
    authors: str | None
    categories: str | None
    score: float | None
    review_summary: str | None
    review_text: str | None
    review_time: str | None


def get_book_review_context(
    conn: Connection, book_title: str, limit: int = 5
) -> List[ReviewContext]:
    """
    Fuzzy/fragment-based search:
    fetch a few review contexts for a given (partial, case-insensitive) book title.
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
    WHERE r.book_pk IS NOT NULL
      AND LOWER(bm.title) LIKE LOWER(%(pattern)s)
    ORDER BY r.review_time DESC NULLS LAST
    LIMIT %(limit)s;
    """
    pattern = f"%{book_title}%"
    with conn.cursor() as cur:
        cur.execute(sql, {"pattern": pattern, "limit": limit})
        rows = cur.fetchall()

    results: List[ReviewContext] = [
        ReviewContext(
            review_pk=row[0],
            book_pk=row[1],
            title=row[2],
            authors=row[3],
            categories=row[4],
            score=float(row[5]) if row[5] is not None else None,
            review_summary=row[6],
            review_text=row[7],
            review_time=row[8].isoformat() if row[8] is not None else None,
        )
        for row in rows
    ]
    logger.info(
        "Tool get_book_review_context (fragment search, title='%s') returned %d rows.",
        book_title, len(results),
    )
    return results


def search_books_by_title_fragment(
    conn: Connection, query: str, limit: int = 10
) -> List[BookSearchResult]:
    """
    Search books by title fragment (case-insensitive), returning candidates.
    """
    sql = """
    SELECT
        b.book_pk,
        b.title,
        b.publisher,
        b.published_year,
        COUNT(r.review_pk) AS review_count
    FROM app.books b
    LEFT JOIN app.reviews r ON r.book_pk = b.book_pk
    WHERE LOWER(b.title) LIKE LOWER(%(pattern)s)
    GROUP BY b.book_pk, b.title, b.publisher, b.published_year
    ORDER BY review_count DESC, b.title ASC
    LIMIT %(limit)s;
    """
    pattern = f"%{query}%"
    with conn.cursor() as cur:
        cur.execute(sql, {"pattern": pattern, "limit": limit})
        rows = cur.fetchall()

    results: List[BookSearchResult] = [
        BookSearchResult(
            book_pk=row[0],
            title=row[1],
            publisher=row[2],
            published_year=row[3],
            review_count=row[4] or 0,
        )
        for row in rows
    ]
    logger.info(
        "Tool search_books_by_title_fragment('%s') returned %d candidates.",
        query, len(results),
    )
    return results


def get_book_review_context_by_book_pk(
    conn: Connection, book_pk: int, limit: int = 5
) -> List[ReviewContext]:
    """
    Exact lookup by book_pk: fetch review contexts for a specific book.
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
        WHERE b.book_pk = %(book_pk)s
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
    WHERE r.book_pk = %(book_pk)s
    ORDER BY r.review_time DESC NULLS LAST
    LIMIT %(limit)s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, {"book_pk": book_pk, "limit": limit})
        rows = cur.fetchall()

    results: List[ReviewContext] = [
        ReviewContext(
            review_pk=row[0],
            book_pk=row[1],
            title=row[2],
            authors=row[3],
            categories=row[4],
            score=float(row[5]) if row[5] is not None else None,
            review_summary=row[6],
            review_text=row[7],
            review_time=row[8].isoformat() if row[8] is not None else None,
        )
        for row in rows
    ]
    logger.info(
        "Tool get_book_review_context_by_book_pk(book_pk=%d) returned %d rows.",
        book_pk, len(results),
    )
    return results


def resolve_book_candidates(
    conn: Connection, book_title: str, limit: int = 10
) -> List[BookSearchResult]:
    """
    High-level helper to resolve candidate books for a title query.
    Currently uses fragment search only, but can be extended later.
    """
    logger.info(
        "Tool resolve_book_candidates called with title='%s', limit=%d",
        book_title, limit,
    )
    return search_books_by_title_fragment(conn, query=book_title, limit=limit)



