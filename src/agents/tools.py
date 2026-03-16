from __future__ import annotations

import logging
from typing import List

from psycopg import Connection

from src.repositories.tool_repository import (
    AuthorSummary,
    BookSearchResult,
    BookSummary,
    CategorySummary,
    ReviewContext,
    ReviewerSummary,
    get_book_review_context as _get_book_review_context,
    get_book_review_context_by_book_pk as _get_book_review_context_by_book_pk,
    get_lowest_rated_books as _get_lowest_rated_books,
    get_most_critical_reviewers as _get_most_critical_reviewers,
    get_most_criticized_books as _get_most_criticized_books,
    get_most_diverse_reviewers as _get_most_diverse_reviewers,
    get_most_polarized_books as _get_most_polarized_books,
    get_most_positive_reviewers as _get_most_positive_reviewers,
    get_most_recommended_books as _get_most_recommended_books,
    get_reviewers_with_longest_reviews as _get_reviewers_with_longest_reviews,
    get_top_authors_by_avg_score as _get_top_authors_by_avg_score,
    get_top_authors_by_review_volume as _get_top_authors_by_review_volume,
    get_top_books_by_avg_score as _get_top_books_by_avg_score,
    get_top_books_by_review_volume as _get_top_books_by_review_volume,
    get_top_categories_by_avg_score as _get_top_categories_by_avg_score,
    get_top_reviewers_by_review_volume as _get_top_reviewers_by_review_volume,
    get_worst_rated_authors as _get_worst_rated_authors,
    get_worst_rated_categories as _get_worst_rated_categories,
    resolve_book_candidates as _resolve_book_candidates,
    search_books_by_title_fragment as _search_books_by_title_fragment,
)
from src.repositories.vector_repository import (
    search_similar_reviews as _search_similar_reviews,
)


logger = logging.getLogger(__name__)

"""
Funções de ferramenta estruturada utilizadas pelo agente de analytics.

Cada função aqui:
- recebe uma conexão com o banco e parâmetros simples;
- delega a consulta para o módulo de repositórios (`tool_repository`);
- retorna objetos tipados (TypedDict) prontos para serem serializados em JSON
  e consumidos pela LangGraph ou pelo servidor MCP.
"""


def get_top_books_by_review_volume(
    conn: Connection, limit: int = 10
) -> List[BookSummary]:
    logger.info(
        "Agent tool get_top_books_by_review_volume called with limit=%d", limit
    )
    return _get_top_books_by_review_volume(conn, limit=limit)


def get_lowest_rated_books(
    conn: Connection, min_reviews: int = 100, limit: int = 10
) -> List[BookSummary]:
    """
    Books with lowest average score and minimum review count (proxy for least recommended).
    """
    logger.info(
        "Agent tool get_lowest_rated_books called with min_reviews=%d, limit=%d",
        min_reviews,
        limit,
    )
    return _get_lowest_rated_books(conn, min_reviews=min_reviews, limit=limit)


def get_most_criticized_books(
    conn: Connection, min_negative_reviews: int = 20, limit: int = 10
) -> List[BookSummary]:
    """
    Books with the highest number of negative reviews (score <= 2),
    with at least min_negative_reviews. This is distinct from worst_rated:
    here we rank by VOLUME of criticism, not by lowest average score.
    """
    logger.info(
        "Agent tool get_most_criticized_books called with min_negative_reviews=%d, limit=%d",
        min_negative_reviews,
        limit,
    )
    return _get_most_criticized_books(
        conn, min_negative_reviews=min_negative_reviews, limit=limit
    )


def get_best_rated_books(
    conn: Connection, min_reviews: int = 100, limit: int = 10
) -> List[BookSummary]:
    """
    Books with highest average score and minimum review count.
    Use for 'melhor avaliado', 'highest rated', 'best rated', etc.
    """
    logger.info(
        "Agent tool get_best_rated_books called with min_reviews=%d, limit=%d",
        min_reviews,
        limit,
    )
    return _get_top_books_by_avg_score(
        conn, min_reviews=min_reviews, limit=limit
    )


def get_top_categories_by_avg_score(
    conn: Connection, min_reviews: int = 100, limit: int = 10
) -> List[CategorySummary]:
    logger.info(
        "Agent tool get_top_categories_by_avg_score called with min_reviews=%d, limit=%d",
        min_reviews,
        limit,
    )
    return _get_top_categories_by_avg_score(
        conn, min_reviews=min_reviews, limit=limit
    )


def get_worst_rated_categories(
    conn: Connection, min_reviews: int = 100, limit: int = 10
) -> List[CategorySummary]:
    """
    Categories with lowest average score and minimum review count.
    """
    logger.info(
        "Agent tool get_worst_rated_categories called with min_reviews=%d, limit=%d",
        min_reviews,
        limit,
    )
    return _get_worst_rated_categories(
        conn, min_reviews=min_reviews, limit=limit
    )


def get_most_recommended_books(
    conn: Connection, min_reviews: int = 100, limit: int = 10
) -> List[BookSummary]:
    """
    Books with highest average score and minimum review count (proxy for
    'most recommended'). Uses only review data; no sales.
    """
    logger.info(
        "Agent tool get_most_recommended_books called with min_reviews=%d, limit=%d",
        min_reviews,
        limit,
    )
    return _get_most_recommended_books(
        conn, min_reviews=min_reviews, limit=limit
    )


def get_top_authors_by_avg_score(
    conn: Connection, min_reviews: int = 30, limit: int = 10
) -> List[AuthorSummary]:
    logger.info(
        "Agent tool get_top_authors_by_avg_score called with min_reviews=%d, limit=%d",
        min_reviews,
        limit,
    )
    return _get_top_authors_by_avg_score(
        conn, min_reviews=min_reviews, limit=limit
    )


def get_worst_rated_authors(
    conn: Connection, min_reviews: int = 30, limit: int = 10
) -> List[AuthorSummary]:
    """
    Authors with lowest average review score (across their books' reviews),
    with at least min_reviews per author.
    """
    logger.info(
        "Agent tool get_worst_rated_authors called with min_reviews=%d, limit=%d",
        min_reviews,
        limit,
    )
    return _get_worst_rated_authors(
        conn, min_reviews=min_reviews, limit=limit
    )


def get_top_authors_by_review_volume(
    conn: Connection, limit: int = 10
) -> List[AuthorSummary]:
    logger.info(
        "Agent tool get_top_authors_by_review_volume called with limit=%d", limit
    )
    return _get_top_authors_by_review_volume(conn, limit=limit)


def get_most_polarized_books(
    conn: Connection, min_reviews: int = 50, limit: int = 10
) -> List[BookSummary]:
    logger.info(
        "Agent tool get_most_polarized_books called with min_reviews=%d, limit=%d",
        min_reviews,
        limit,
    )
    return _get_most_polarized_books(conn, min_reviews=min_reviews, limit=limit)


def search_books_by_title_fragment(
    conn: Connection, query: str, limit: int = 10
) -> List[BookSearchResult]:
    logger.info(
        "Agent tool search_books_by_title_fragment called (fragment search) with query='%s', limit=%d",
        query,
        limit,
    )
    return _search_books_by_title_fragment(conn, query=query, limit=limit)


def get_book_review_context_by_book_pk(
    conn: Connection, book_pk: int, limit: int = 5
) -> List[ReviewContext]:
    logger.info(
        "Agent tool get_book_review_context_by_book_pk called (exact lookup) with book_pk=%d, limit=%d",
        book_pk,
        limit,
    )
    return _get_book_review_context_by_book_pk(conn, book_pk=book_pk, limit=limit)


def get_book_review_context(
    conn: Connection, book_title: str, limit: int = 5
) -> List[ReviewContext]:
    logger.info(
        "Agent tool get_book_review_context called (fragment search) with title='%s', limit=%d",
        book_title,
        limit,
    )
    return _get_book_review_context(conn, book_title=book_title, limit=limit)


def resolve_book_candidates(
    conn: Connection, book_title: str, limit: int = 10
) -> List[BookSearchResult]:
    logger.info(
        "Agent tool resolve_book_candidates called with title='%s', limit=%d",
        book_title,
        limit,
    )
    return _resolve_book_candidates(conn, book_title=book_title, limit=limit)


def search_similar_reviews(
    conn: Connection,
    query_text: str,
    top_k: int = 5,
) -> List[dict]:
    """
    Semantic search over review embeddings. Returns reviews similar to the query.
    """
    logger.info(
        "Agent tool search_similar_reviews called with query=%r, top_k=%d",
        query_text[:80],
        top_k,
    )
    return _search_similar_reviews(conn, query_text=query_text, top_k=top_k)


def get_top_reviewers_by_review_volume(
    conn: Connection, min_reviews: int = 5, limit: int = 10
) -> List[ReviewerSummary]:
    """Reviewers (users) with the highest number of reviews."""
    logger.info(
        "Agent tool get_top_reviewers_by_review_volume called with min_reviews=%d limit=%d",
        min_reviews,
        limit,
    )
    return _get_top_reviewers_by_review_volume(
        conn, min_reviews=min_reviews, limit=limit
    )


def get_reviewers_with_longest_reviews(
    conn: Connection, min_reviews: int = 3, limit: int = 10
) -> List[ReviewerSummary]:
    """Reviewers with highest average review text length (most detailed)."""
    logger.info(
        "Agent tool get_reviewers_with_longest_reviews called with min_reviews=%d limit=%d",
        min_reviews,
        limit,
    )
    return _get_reviewers_with_longest_reviews(
        conn, min_reviews=min_reviews, limit=limit
    )


def get_most_critical_reviewers(
    conn: Connection, min_reviews: int = 5, limit: int = 10
) -> List[ReviewerSummary]:
    """Reviewers with lowest average score (most critical)."""
    logger.info(
        "Agent tool get_most_critical_reviewers called with min_reviews=%d limit=%d",
        min_reviews,
        limit,
    )
    return _get_most_critical_reviewers(
        conn, min_reviews=min_reviews, limit=limit
    )


def get_most_positive_reviewers(
    conn: Connection, min_reviews: int = 5, limit: int = 10
) -> List[ReviewerSummary]:
    """Reviewers with highest average score (most positive)."""
    logger.info(
        "Agent tool get_most_positive_reviewers called with min_reviews=%d limit=%d",
        min_reviews,
        limit,
    )
    return _get_most_positive_reviewers(
        conn, min_reviews=min_reviews, limit=limit
    )


def get_most_diverse_reviewers(
    conn: Connection, min_reviews: int = 5, limit: int = 10
) -> List[ReviewerSummary]:
    """Reviewers with highest count of distinct books reviewed."""
    logger.info(
        "Agent tool get_most_diverse_reviewers called with min_reviews=%d limit=%d",
        min_reviews,
        limit,
    )
    return _get_most_diverse_reviewers(
        conn, min_reviews=min_reviews, limit=limit
    )
