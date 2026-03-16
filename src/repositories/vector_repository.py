from __future__ import annotations

import logging
import time
from typing import Iterable, List, TypedDict

from psycopg import Connection

from src.embeddings.embedding_client import get_embedding_client


logger = logging.getLogger(__name__)


class ReviewEmbeddingRecord(TypedDict):
    review_pk: int
    book_pk: int
    embedding: List[float]
    model_name: str
    embedding_dimension: int
    pipeline_version: str | None


def _embedding_to_pgvector_literal(embedding: List[float]) -> str:
    """
    Convert a Python list of floats to pgvector text format: '[0.1, 0.2, ...]'.
    """
    return "[" + ", ".join(f"{x:.6f}" for x in embedding) + "]"


def truncate_review_embeddings(conn: Connection) -> None:
    logger.info("Truncating app.review_embeddings table.")
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE app.review_embeddings;")
    conn.commit()
    logger.info("app.review_embeddings truncated.")


def insert_embeddings(
    conn: Connection,
    records: Iterable[ReviewEmbeddingRecord],
    batch_size: int = 1_000,
) -> int:
    """
    Insert review embeddings into app.review_embeddings in batches.
    """
    sql = """
    INSERT INTO app.review_embeddings (
        review_pk,
        book_pk,
        embedding,
        model_name,
        embedding_dimension,
        pipeline_version
    )
    VALUES (
        %(review_pk)s,
        %(book_pk)s,
        %(embedding)s::vector,
        %(model_name)s,
        %(embedding_dimension)s,
        %(pipeline_version)s
    )
    ON CONFLICT (review_pk) DO UPDATE
        SET book_pk = EXCLUDED.book_pk,
            embedding = EXCLUDED.embedding,
            model_name = EXCLUDED.model_name,
            embedding_dimension = EXCLUDED.embedding_dimension,
            pipeline_version = EXCLUDED.pipeline_version;
    """
    total = 0
    batch: List[dict] = []
    with conn.cursor() as cur:
        for rec in records:
            row = {
                "review_pk": rec["review_pk"],
                "book_pk": rec["book_pk"],
                "embedding": _embedding_to_pgvector_literal(rec["embedding"]),
                "model_name": rec["model_name"],
                "embedding_dimension": rec["embedding_dimension"],
                "pipeline_version": rec["pipeline_version"],
            }
            batch.append(row)
            if len(batch) >= batch_size:
                cur.executemany(sql, batch)
                total += len(batch)
                logger.info("Inserted %d embeddings (cumulative=%d).", len(batch), total)
                batch.clear()
        if batch:
            cur.executemany(sql, batch)
            total += len(batch)
            logger.info("Inserted %d embeddings (cumulative=%d).", len(batch), total)
    conn.commit()
    logger.info("Finished inserting embeddings. Total=%d.", total)
    return total


def search_similar_reviews(
    conn: Connection,
    query_text: str,
    top_k: int = 5,
) -> List[dict]:
    """
    Semantic search over review embeddings.
    Returns a list of dicts with review/book metadata and similarity score.
    Uses singleton embedding client (model loaded once per process).
    """
    t0 = time.perf_counter()
    client = get_embedding_client()
    query_emb = client.embed_texts([query_text])[0]
    t_embed = time.perf_counter() - t0
    logger.info(
        "Semantic search: embedding step took %.3fs (query=%r, top_k=%d).",
        t_embed,
        query_text[:50] + "..." if len(query_text) > 50 else query_text,
        top_k,
    )
    emb_literal = _embedding_to_pgvector_literal(query_emb)

    sql = """
    SELECT
        r.review_pk,
        r.book_pk,
        b.title,
        r.score,
        r.review_summary,
        r.review_text,
        1 - (e.embedding <=> %(embedding)s::vector(384)) AS similarity
    FROM app.review_embeddings e
    JOIN app.reviews r ON r.review_pk = e.review_pk
    JOIN app.books b ON b.book_pk = r.book_pk
    ORDER BY e.embedding <=> %(embedding)s::vector(384)
    LIMIT %(top_k)s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, {"embedding": emb_literal, "top_k": top_k})
        rows = cur.fetchall()

    results: List[dict] = [
        {
            "review_pk": row[0],
            "book_pk": row[1],
            "title": row[2],
            "score": float(row[3]) if row[3] is not None else None,
            "review_summary": row[4],
            "review_text": row[5],
            "similarity": float(row[6]),
        }
        for row in rows
    ]
    t_total = time.perf_counter() - t0
    logger.info(
        "Semantic search completed in %.3fs total, %d results for query=%r.",
        t_total,
        len(results),
        query_text[:50] + "..." if len(query_text) > 50 else query_text,
    )
    return results


