"""
MCP server exposing the project's controlled tools for MCP-compatible clients.
Reuses src.agents.tools; no business logic duplication.

Run as persistent process (for API integration):
  python -m mcp_server.server
  Uses MCP_SERVER_PORT (default 8001), transport streamable-http.
  API connects to http://127.0.0.1:8001/mcp

Run with stdio (for Cursor/Claude Desktop):
  python -m mcp_server.server stdio
"""
from __future__ import annotations

import logging
import os
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from src.agents import tools
from src.repositories.base_repository import get_connection


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp_server")

MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "127.0.0.1")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8001"))

mcp = FastMCP(
    "Book Review Tools",
    json_response=True,
    host=MCP_SERVER_HOST,
    port=MCP_SERVER_PORT,
)


def _with_connection(fn: Any, *args: Any, **kwargs: Any) -> Any:
    """Run a tool that expects (conn, ...); return JSON-serializable result."""
    conn = get_connection()
    try:
        result = fn(conn, *args, **kwargs)
        return _to_json_friendly(result)
    finally:
        conn.close()


def _to_json_friendly(obj: Any) -> Any:
    """Ensure result is JSON-serializable."""
    if isinstance(obj, list):
        return [_to_json_friendly(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _to_json_friendly(v) for k, v in obj.items()}
    if hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
        try:
            return list(obj)
        except Exception:
            pass
    return obj


# --- 10 MCP tools (reuse src.agents.tools) ---


@mcp.tool()
def get_top_categories_by_avg_score(
    min_reviews: int = 100,
    limit: int = 10,
) -> list[dict]:
    """Top categories by average review score (minimum reviews per category)."""
    logger.info("MCP tool get_top_categories_by_avg_score min_reviews=%s limit=%s", min_reviews, limit)
    return _with_connection(
        tools.get_top_categories_by_avg_score,
        min_reviews=min_reviews,
        limit=limit,
    )


@mcp.tool()
def get_top_books_by_review_volume(limit: int = 10) -> list[dict]:
    """Top books by number of reviews (review volume)."""
    logger.info("MCP tool get_top_books_by_review_volume limit=%s", limit)
    return _with_connection(tools.get_top_books_by_review_volume, limit=limit)


@mcp.tool()
def get_best_rated_books(
    min_reviews: int = 100,
    limit: int = 10,
) -> list[dict]:
    """Top books by average review score (best rated), with minimum review count."""
    logger.info("MCP tool get_best_rated_books min_reviews=%s limit=%s", min_reviews, limit)
    return _with_connection(
        tools.get_best_rated_books,
        min_reviews=min_reviews,
        limit=limit,
    )


@mcp.tool()
def get_lowest_rated_books(
    min_reviews: int = 100,
    limit: int = 10,
) -> list[dict]:
    """Books with lowest average score (proxy for least recommended), min review count."""
    logger.info("MCP tool get_lowest_rated_books min_reviews=%s limit=%s", min_reviews, limit)
    return _with_connection(
        tools.get_lowest_rated_books,
        min_reviews=min_reviews,
        limit=limit,
    )


@mcp.tool()
def get_most_polarized_books(
    min_reviews: int = 50,
    limit: int = 10,
) -> list[dict]:
    """Books with highest score variance (most polarized/controversial)."""
    logger.info("MCP tool get_most_polarized_books min_reviews=%s limit=%s", min_reviews, limit)
    return _with_connection(
        tools.get_most_polarized_books,
        min_reviews=min_reviews,
        limit=limit,
    )


@mcp.tool()
def get_most_recommended_books(
    min_reviews: int = 100,
    limit: int = 10,
) -> list[dict]:
    """Books with highest share of positive recommendations (most recommended)."""
    logger.info("MCP tool get_most_recommended_books min_reviews=%s limit=%s", min_reviews, limit)
    return _with_connection(
        tools.get_most_recommended_books,
        min_reviews=min_reviews,
        limit=limit,
    )


@mcp.tool()
def get_top_authors_by_avg_score(
    min_reviews: int = 30,
    limit: int = 10,
) -> list[dict]:
    """Authors with highest average review score (across their books' reviews)."""
    logger.info("MCP tool get_top_authors_by_avg_score min_reviews=%s limit=%s", min_reviews, limit)
    return _with_connection(
        tools.get_top_authors_by_avg_score,
        min_reviews=min_reviews,
        limit=limit,
    )


@mcp.tool()
def get_top_authors_by_review_volume(limit: int = 10) -> list[dict]:
    """Authors with highest number of reviews (across their books)."""
    logger.info("MCP tool get_top_authors_by_review_volume limit=%s", limit)
    return _with_connection(tools.get_top_authors_by_review_volume, limit=limit)


@mcp.tool()
def search_similar_reviews(
    query_text: str,
    top_k: int = 5,
) -> list[dict]:
    """Semantic search: find reviews similar to the given query text."""
    logger.info("MCP tool search_similar_reviews query=%r top_k=%s", query_text[:80], top_k)
    return _with_connection(
        tools.search_similar_reviews,
        query_text=query_text,
        top_k=top_k,
    )


@mcp.tool()
def resolve_book_candidates(
    book_title: str,
    limit: int = 10,
) -> list[dict]:
    """Resolve book candidates by title (fragment search). Returns matching books with metadata."""
    logger.info("MCP tool resolve_book_candidates book_title=%r limit=%s", book_title, limit)
    return _with_connection(
        tools.resolve_book_candidates,
        book_title=book_title,
        limit=limit,
    )


@mcp.tool()
def get_book_review_context_by_book_pk(
    book_pk: int,
    limit: int = 5,
) -> list[dict]:
    """Get review context for a book by its primary key (exact lookup)."""
    logger.info("MCP tool get_book_review_context_by_book_pk book_pk=%s limit=%s", book_pk, limit)
    return _with_connection(
        tools.get_book_review_context_by_book_pk,
        book_pk=book_pk,
        limit=limit,
    )


@mcp.tool()
def get_top_reviewers_by_review_volume(
    min_reviews: int = 5,
    limit: int = 10,
) -> list[dict]:
    """Reviewers (users) with the highest number of reviews."""
    logger.info("MCP tool get_top_reviewers_by_review_volume min_reviews=%s limit=%s", min_reviews, limit)
    return _with_connection(
        tools.get_top_reviewers_by_review_volume,
        min_reviews=min_reviews,
        limit=limit,
    )


@mcp.tool()
def get_reviewers_with_longest_reviews(
    min_reviews: int = 3,
    limit: int = 10,
) -> list[dict]:
    """Reviewers with highest average review text length (most detailed)."""
    logger.info("MCP tool get_reviewers_with_longest_reviews min_reviews=%s limit=%s", min_reviews, limit)
    return _with_connection(
        tools.get_reviewers_with_longest_reviews,
        min_reviews=min_reviews,
        limit=limit,
    )


@mcp.tool()
def get_most_critical_reviewers(
    min_reviews: int = 5,
    limit: int = 10,
) -> list[dict]:
    """Reviewers with lowest average score (most critical)."""
    logger.info("MCP tool get_most_critical_reviewers min_reviews=%s limit=%s", min_reviews, limit)
    return _with_connection(
        tools.get_most_critical_reviewers,
        min_reviews=min_reviews,
        limit=limit,
    )


@mcp.tool()
def get_most_positive_reviewers(
    min_reviews: int = 5,
    limit: int = 10,
) -> list[dict]:
    """Reviewers with highest average score (most positive)."""
    logger.info("MCP tool get_most_positive_reviewers min_reviews=%s limit=%s", min_reviews, limit)
    return _with_connection(
        tools.get_most_positive_reviewers,
        min_reviews=min_reviews,
        limit=limit,
    )


@mcp.tool()
def get_most_diverse_reviewers(
    min_reviews: int = 5,
    limit: int = 10,
) -> list[dict]:
    """Reviewers with highest count of distinct books reviewed."""
    logger.info("MCP tool get_most_diverse_reviewers min_reviews=%s limit=%s", min_reviews, limit)
    return _with_connection(
        tools.get_most_diverse_reviewers,
        min_reviews=min_reviews,
        limit=limit,
    )


def main() -> None:
    """Run the MCP server. Default: streamable-http (persistent). Use 'stdio' for Cursor/Claude."""
    use_stdio = len(sys.argv) > 1 and sys.argv[1].strip().lower() == "stdio"
    # Preload embedding model in this process so first semantic tool call is not slow
    import time as _time
    _t0 = _time.perf_counter()
    try:
        from src.embeddings.embedding_client import get_embedding_client
        get_embedding_client()
        logger.info(
            "MCP startup: embedding model preloaded in %.3fs (singleton ready for semantic MCP tools).",
            _time.perf_counter() - _t0,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "MCP startup: embedding model preload failed (will load on first semantic call): %s",
            exc,
        )
    if use_stdio:
        logger.info("Starting MCP server (stdio transport). Tools: 16 registered.")
        mcp.run(transport="stdio")
    else:
        logger.info(
            "Starting MCP server (streamable-http) at http://%s:%s/mcp . Tools: 16 registered.",
            MCP_SERVER_HOST,
            MCP_SERVER_PORT,
        )
        import asyncio
        asyncio.run(mcp.run_streamable_http_async())


if __name__ == "__main__":
    main()
