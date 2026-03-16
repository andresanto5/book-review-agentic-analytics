from __future__ import annotations

import logging
from typing import List, Tuple

from psycopg import Connection


logger = logging.getLogger(__name__)


def populate_normalized_titles(conn: Connection) -> None:
    with conn.cursor() as cur:
        logger.info("Populating normalized_title for app.books.")
        cur.execute(
            """
            UPDATE app.books
            SET normalized_title = lower(
                regexp_replace(
                    regexp_replace(
                        trim(title),
                        '[^\\w\\s]',
                        ' ',
                        'g'
                    ),
                    '\\s+',
                    ' ',
                    'g'
                )
            )
            """
        )
        logger.info("Updated %d book rows with normalized_title.", cur.rowcount)

        logger.info("Populating normalized_title for app.reviews.")
        cur.execute(
            """
            UPDATE app.reviews
            SET normalized_title = lower(
                regexp_replace(
                    regexp_replace(
                        trim(title),
                        '[^\\w\\s]',
                        ' ',
                        'g'
                    ),
                    '\\s+',
                    ' ',
                    'g'
                )
            )
            """
        )
        logger.info("Updated %d review rows with normalized_title.", cur.rowcount)

    conn.commit()


def link_reviews_to_books(conn: Connection) -> int:
    with conn.cursor() as cur:
        logger.info("Linking reviews to books via normalized_title.")
        cur.execute(
            """
            UPDATE app.reviews r
            SET book_pk = b.book_pk
            FROM app.books b
            WHERE r.book_pk IS NULL
              AND r.normalized_title IS NOT NULL
              AND b.normalized_title IS NOT NULL
              AND r.normalized_title = b.normalized_title
            """
        )
        updated = cur.rowcount
        logger.info("Linked %d reviews to books.", updated)

    conn.commit()
    return updated


def get_reconciliation_stats(conn: Connection) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM app.books")
        total_books = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM app.reviews")
        total_reviews = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM app.reviews WHERE book_pk IS NOT NULL")
        reconciled_reviews = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM app.reviews WHERE book_pk IS NULL")
        unreconciled_reviews = cur.fetchone()[0]

        match_percent = (
            (reconciled_reviews / total_reviews * 100.0) if total_reviews else 0.0
        )

        logger.info("Reconciliation summary:")
        logger.info("Total books: %d", total_books)
        logger.info("Total reviews: %d", total_reviews)
        logger.info("Reconciled reviews: %d", reconciled_reviews)
        logger.info("Unreconciled reviews: %d", unreconciled_reviews)
        logger.info("Match percentage: %.2f%%", match_percent)

        # Duplicates in books
        cur.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT normalized_title
                FROM app.books
                WHERE normalized_title IS NOT NULL
                GROUP BY normalized_title
                HAVING COUNT(*) > 1
            ) sub
            """
        )
        duplicate_books_titles = cur.fetchone()[0]
        logger.info(
            "Number of duplicated normalized_title values in books: %d",
            duplicate_books_titles,
        )

        # Duplicates in reviews
        cur.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT normalized_title
                FROM app.reviews
                WHERE normalized_title IS NOT NULL
                GROUP BY normalized_title
                HAVING COUNT(*) > 1
            ) sub
            """
        )
        duplicate_review_titles = cur.fetchone()[0]
        logger.info(
            "Number of duplicated normalized_title values in reviews: %d",
            duplicate_review_titles,
        )

        # Sample of unreconciled reviews
        cur.execute(
            """
            SELECT book_id_raw, title, normalized_title, score
            FROM app.reviews
            WHERE book_pk IS NULL
              AND normalized_title IS NOT NULL
            LIMIT 10
            """
        )
        samples: List[Tuple] = cur.fetchall()
        if samples:
            logger.info("Sample of unreconciled reviews (up to 10 rows):")
            for row in samples:
                logger.info(
                    "book_id_raw=%s, title=%s, normalized_title=%s, score=%s",
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                )
        else:
            logger.info("No unreconciled reviews with non-null normalized_title found.")


