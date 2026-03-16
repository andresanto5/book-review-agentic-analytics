from __future__ import annotations

import json
import logging
import time
from typing import Any, List

from src.agents.langgraph_state import WorkflowState
from src.agents import tools
from src.llm.bedrock_client import get_bedrock_client
from src.config.settings import mcp_settings
from src.mcp.client import call_tool_via_mcp
from src.repositories.base_repository import get_connection
from src.repositories.vector_repository import search_similar_reviews


logger = logging.getLogger(__name__)

"""
Nós de orquestração da LangGraph para o agente de analytics de reviews.

Este módulo concentra:
- interpretação da pergunta do usuário (entidade alvo, métrica, estratégia);
- escolha e execução de ferramentas estruturadas (SQL/MCP) ou semânticas (busca vetorial);
- construção dos prompts para o modelo de linguagem;
- geração da resposta final, sempre ancorada nos dados retornados pelas ferramentas.
"""


# Keywords that indicate the user is asking about data we do NOT have (sales, revenue, etc.)
OUT_OF_SCOPE_KEYWORDS = [
    "vendido", "vendidos", "venda", "vendas", "faturamento", "faturar", "fatura",
    "lucro", "lucros", "receita", "receitas", "estoque", "margem", "margens",
    "sold", "sales", "revenue", "profit", "profits", "stock", "margin", "margins",
    "earnings", "turnover", "market share", "sold units", "unidades vendidas",
]

SCOPE_DENIAL_MESSAGE = (
    "A base atual não contém dados de vendas, faturamento ou lucro. "
    "Posso, no entanto, informar livros com maior volume de reviews, melhor avaliação média ou maior polarização, "
    "que funcionam como proxies de engajamento e recepção do público."
)


def check_scope_or_capability(state: WorkflowState) -> WorkflowState:
    """
    Guardrail: detect if the user question is about data we do not have
    (sales, revenue, profit, stock, margin, etc.). If so, set out_of_scope and
    scope_message and do not run tools or Bedrock for the main path.
    """
    t0 = time.perf_counter()
    query = state.get("user_query", "")
    q = query.lower().strip()
    state.setdefault("path_used", []).append("check_scope_or_capability")

    hits = [kw for kw in OUT_OF_SCOPE_KEYWORDS if kw in q]
    out_of_scope = len(hits) > 0

    if out_of_scope:
        state["out_of_scope"] = True
        state["scope_message"] = SCOPE_DENIAL_MESSAGE
        logger.warning(
            "check_scope_or_capability: question classified as OUT OF SCOPE. query=%r, keyword_hits=%s",
            query,
            hits,
        )
    else:
        state["out_of_scope"] = False
        state["scope_message"] = None
        logger.info(
            "check_scope_or_capability: question within scope. query=%r",
            query,
        )
    logger.info(
        "check_scope_or_capability: node completed in %.3fs.",
        time.perf_counter() - t0,
    )
    return state


def build_out_of_scope_response(state: WorkflowState) -> WorkflowState:
    """When out_of_scope is True, set final_answer from scope_message."""
    t0 = time.perf_counter()
    state.setdefault("path_used", []).append("build_out_of_scope_response")
    state["final_answer"] = state.get("scope_message") or SCOPE_DENIAL_MESSAGE
    logger.info(
        "build_out_of_scope_response: completed in %.3fs (no tools/Bedrock).",
        time.perf_counter() - t0,
    )
    return state


# --- Interpret query: target entity, metric intent, strategy ---
TARGET_BOOK = ["book", "books", "livro", "livros"]
TARGET_CATEGORY = ["category", "categories", "categoria", "categorias", "gênero", "gêneros", "genero", "generos"]
TARGET_AUTHOR = ["author", "authors", "autor", "autores", "escritor", "escritores"]
TARGET_REVIEWER = [
    "reviewer", "reviewers", "usuário", "usuários", "usuarios", "leitores", "perfis",
    "user", "users",
    "opiniões relevantes", "opinioes relevantes", "usuários críticos", "usuarios criticos",
    "leitores mais detalhistas", "reviews mais detalhadas",
]

METRIC_BEST_RATED = [
    "melhor avaliado", "melhores avaliados", "mais bem avaliado", "mais bem avaliados",
    "melhor avaliada", "melhores avaliadas", "mais bem avaliada", "mais bem avaliadas",
    "highest rated", "best rated", "highest score", "maior média", "maior media",
    "melhor nota", "melhores notas", "average rating", "avg score", "média de avaliação",
    "melhor avaliação", "melhor avaliação média", "avaliação média",
]
METRIC_LOWEST_RATED = [
    "pior avaliado", "pior avaliação", "piores avaliações", "piores avaliados",
    "menor recomendação", "lowest rated", "worst rated",
    "least recommended", "pior nota", "notas ruins", "baixa avaliação",
    "menos recomendado", "menor média", "mal avaliado", "mal avaliados",
]
METRIC_MOST_REVIEWED = [
    "mais reviews", "mais avaliado", "mais comentado", "most reviewed", "highest volume",
    "maior volume", "maior quantidade", "mais resenhado", "mais resenhados", "most popular",
]
METRIC_MOST_POLARIZED = [
    "mais polarizado", "mais polarizados", "mais controverso", "maior divergência", "maior dispersão",
    "most polarized", "highest variance", "highest stddev", "polarizados", "controversos",
]
METRIC_RECOMMENDED = [
    "recomendado", "recomendados", "recomendada", "recomendadas", "recommend", "recommended",
    "mais recomendado", "mais recomendados",
]
METRIC_LEAST_RECOMMENDED = [
    "menos recomendado", "menor recomendação", "least recommended",
]
# Reviewer-level metrics (user/reviewer entity)
METRIC_LONGEST_REVIEWS = [
    "reviews mais longas", "reviews mais detalhadas", "mais detalhistas",
    "longest reviews", "most detailed reviews", "reviews mais longas",
    "escrevem reviews mais", "mais detalhadas",
]
METRIC_REVIEWER_CRITICAL = [
    "mais críticos", "mais criticos", "usuários críticos", "leitores mais críticos",
    "most critical", "harshest reviewers",
]
METRIC_REVIEWER_POSITIVE = [
    "mais positivos", "most positive", "melhor avaliadores",
]
METRIC_REVIEWER_DIVERSE = [
    "mais diversos", "mais livros diferentes", "diversidade de livros",
    "most diverse", "distinct books", "avaliaram mais livros",
]
# Vague "relevance" for interviews -> ambiguous reviewer
REVIEWER_VAGUE_RELEVANCE = [
    "opiniões relevantes", "opinioes relevantes", "relevantes para entrevistas",
    "relevantes para pesquisa", "relevance", "for interviews",
]
METRIC_COMPLAINT = [
    "reclamações", "reclamação", "reclamam", "reclamações negativas",
    "complaints", "criticisms", "negative feedback",
    "why people dislike", "do que reclamam", "principais críticas", "criticas",
]
METRIC_PRAISE = [
    "elogios", "elogio", "gostam", "praise", "positive feedback", "strengths",
    "why people like", "o que gostam", "principais elogios",
]
# Qualitative/semantic: check before structured metrics so "o que as avaliações falam" -> theme_summary
METRIC_THEME = [
    "resuma", "resumo", "summarize", "summary", "quais temas", "what do reviews say",
    "what do the reviews say", "quais opiniões", "temas principais", "themes", "opinions", "sentiment",
    "o que as avaliações falam", "o que as avaliações dizem", "o que os reviews dizem", "o que os reviews falam",
    "o que as reviews falam", "o que as reviews dizem", "o que falam sobre", "o que dizem sobre",
    "falam sobre o livro", "dizem sobre o livro", "avaliações falam", "reviews falam", "reviews say",
    "opiniões sobre", "temas nas avaliações", "temas nos reviews", "themes in the reviews",
]

# Explicit negative / criticized phrases (for worst_rated / most_criticized)
NEGATIVE_KEYWORDS = [
    "pior", "piores", "menor", "menos bem avaliado", "menos bem avaliados",
    "baixa avaliação", "avaliações ruins", "notas ruins", "mal avaliado", "mal avaliados",
]

CRITICIZED_KEYWORDS = [
    "mais criticado", "mais criticada", "mais criticados", "mais criticadas",
    "mais reclamado", "mais reclamados", "mais reclamações", "mais reclamadas",
    "livro mais criticado", "livro com mais críticas", "livros mais criticados",
]

# Optional: "e por quê" / "and why" -> hybrid
HYBRID_SUFFIX = [" e por quê", " e porque", " e por que", " and why", " and why?"]

# Phrases that indicate a composite/relational query (entity A in relation to entity B).
# No single structured tool answers these; we return a transparent message + suggestions.
COMPOSITE_RELATIONAL_PHRASES = [
    "categoria com o autor",
    "categoria com o autor que",
    "categorias com o autor",
    "qual a categoria com o autor",
    "qual o livro do autor",
    "livro do autor",
    "livros do autor",
    "categoria contém os livros",
    "categoria contém os livros mais",
    "qual categoria contém",
    "autor da categoria",
    "autores da categoria",
    "qual autor da categoria",
    "category with the author",
    "book by the author",
    "books by the author",
    "category that contains",
    "author in the category",
    "which category has the author",
]

COMPOSITE_RESPONSE_MESSAGE = (
    "A pergunta combina múltiplas entidades e relações analíticas que ainda não estão mapeadas "
    "para uma única tool estruturada. Posso responder separadamente: qual autor tem melhores avaliações, "
    "quais categorias têm melhor média, ou quais livros são mais polarizados."
)


def _count_target_entities_present(q: str) -> list[str]:
    """Return list of target entity types that appear in the query (book, category, author, reviewer)."""
    present: list[str] = []
    if any(t in q for t in TARGET_BOOK):
        present.append("book")
    if any(t in q for t in TARGET_CATEGORY):
        present.append("category")
    if any(t in q for t in TARGET_AUTHOR):
        present.append("author")
    if any(t in q for t in TARGET_REVIEWER):
        present.append("reviewer")
    return present


def _detect_composite_query(q: str) -> tuple[bool, str | None]:
    """
    Detect composite/relational queries that mix two entities or use relational phrasing.
    Returns (is_composite, reason).
    """
    # Multiple distinct target types in the same question
    present = _count_target_entities_present(q)
    if len(present) >= 2:
        return True, f"multiple_entities: {present!r}"

    # Relational phrases (X com/do/da Y, X that contains Y, etc.)
    for phrase in COMPOSITE_RELATIONAL_PHRASES:
        if phrase in q:
            return True, f"relational_phrase: {phrase!r}"

    return False, None


def _detect_target_entity(q: str) -> str:
    if any(t in q for t in TARGET_BOOK):
        return "book"
    if any(t in q for t in TARGET_CATEGORY):
        return "category"
    if any(t in q for t in TARGET_AUTHOR):
        return "author"
    if any(t in q for t in TARGET_REVIEWER):
        return "reviewer"
    return "general"


def _detect_metric_intent(q: str) -> str:
    # 1) Semantic/qualitative first so "o que as avaliações falam" -> theme_summary, not best_rated
    if any(t in q for t in METRIC_THEME):
        return "theme_summary"
    if any(t in q for t in METRIC_COMPLAINT):
        return "complaint_summary"
    if any(t in q for t in METRIC_PRAISE):
        return "praise_summary"

    # 2) Explicit negative / criticized before positive rankings
    if any(t in q for t in CRITICIZED_KEYWORDS):
        return "most_criticized"
    if any(t in q for t in METRIC_LOWEST_RATED) or any(t in q for t in NEGATIVE_KEYWORDS):
        return "worst_rated"

    # 3) Structured/ranking (positive / neutral)
    if any(t in q for t in METRIC_BEST_RATED):
        return "best_rated"
    if any(t in q for t in METRIC_MOST_REVIEWED):
        return "most_reviewed"
    if any(t in q for t in METRIC_MOST_POLARIZED):
        return "most_polarized"
    if any(t in q for t in METRIC_RECOMMENDED):
        return "recommended"
    if any(t in q for t in METRIC_LEAST_RECOMMENDED):
        return "least_recommended"
    # Reviewer-level metrics
    if any(t in q for t in METRIC_LONGEST_REVIEWS):
        return "longest_reviews"
    if any(t in q for t in METRIC_REVIEWER_CRITICAL):
        return "most_critical"
    if any(t in q for t in METRIC_REVIEWER_POSITIVE):
        return "most_positive"
    if any(t in q for t in METRIC_REVIEWER_DIVERSE):
        return "most_diverse"
    return "unknown"


def interpret_query(state: WorkflowState) -> WorkflowState:
    """
    Robust interpretation: scope, target_entity, metric_intent, strategy.
    Replaces simple keyword classify; sets out_of_scope, strategy, routing_reason, suggestions.
    """
    t0 = time.perf_counter()
    state.setdefault("path_used", []).append("interpret_query")
    query = state.get("user_query", "")
    q = query.lower().strip()

    # 1) Out of scope
    scope_hits = [kw for kw in OUT_OF_SCOPE_KEYWORDS if kw in q]
    if scope_hits:
        state["out_of_scope"] = True
        state["scope_message"] = SCOPE_DENIAL_MESSAGE
        state["strategy"] = "out_of_scope"
        state["routing_reason"] = f"out_of_scope: {scope_hits!r}"
        state["target_entity"] = None
        state["metric_intent"] = None
        state["intent"] = "out_of_scope"
        logger.warning(
            "interpret_query: OUT_OF_SCOPE query=%r hits=%s",
            query, scope_hits,
        )
        logger.info("interpret_query: completed in %.3fs.", time.perf_counter() - t0)
        return state

    state["out_of_scope"] = False
    state["scope_message"] = None
    state["is_composite_query"] = False
    state["composite_reason"] = None

    target = _detect_target_entity(q)
    metric = _detect_metric_intent(q)
    is_composite, composite_reason = _detect_composite_query(q)

    # 2) Composite/relational query: multiple entities or relational phrasing -> no single tool
    if is_composite:
        state["is_composite_query"] = True
        state["composite_reason"] = composite_reason
        state["strategy"] = "unsupported_composite"
        state["target_entity"] = target
        state["metric_intent"] = metric
        state["routing_reason"] = f"unsupported_composite: {composite_reason}"
        state["suggestions"] = [
            "Quais categorias têm maior média de avaliação?",
            "Qual autor tem melhor avaliação média?",
            "Quais são os livros mais polarizados?",
        ]
        state["intent"] = "unsupported_composite"
        logger.warning(
            "interpret_query: COMPOSITE/RELATIONAL query detected. query=%r composite_reason=%s",
            query,
            composite_reason,
        )
        logger.info("interpret_query: completed in %.3fs.", time.perf_counter() - t0)
        return state

    has_hybrid_suffix = any(s in q for s in HYBRID_SUFFIX)
    has_semantic_metric = metric in ("complaint_summary", "praise_summary", "theme_summary")
    has_structured_metric = metric in (
        "best_rated",
        "worst_rated",
        "most_criticized",
        "most_reviewed",
        "most_polarized",
        "recommended",
        "least_recommended",
        "longest_reviews",
        "most_critical",
        "most_positive",
        "most_diverse",
    )
    is_short_or_vague = len(q.split()) <= 5 and target == "general" and metric in ("unknown", "recommended")
    # Reviewer question with vague "relevance" (e.g. "opiniões relevantes para entrevistas") -> ambiguous
    is_reviewer_vague = (
        target == "reviewer"
        and (metric == "unknown" or any(phrase in q for phrase in REVIEWER_VAGUE_RELEVANCE))
    )

    # 3a) Ambiguous: reviewer question without clear criterion -> ask which reviewer metric
    if is_reviewer_vague:
        state["strategy"] = "ambiguous"
        state["target_entity"] = "reviewer"
        state["metric_intent"] = metric
        state["routing_reason"] = "ambiguous: reviewer question, criterion not specified"
        state["suggestions"] = [
            "Quais usuários têm mais reviews?",
            "Quais usuários escrevem reviews mais detalhadas?",
            "Quais usuários são mais críticos (menor média de nota)?",
            "Quais usuários são mais positivos (maior média de nota)?",
            "Quais usuários avaliaram mais livros diferentes?",
        ]
        state["intent"] = "ambiguous"
        logger.info(
            "interpret_query: AMBIGUOUS reviewer query=%r metric=%s (clarification).",
            query[:80], metric,
        )
        logger.info("interpret_query: completed in %.3fs.", time.perf_counter() - t0)
        return state

    # 3b) Ambiguous: very short, no clear target or only "recommended" with no entity
    if is_short_or_vague and metric in ("unknown", "recommended"):
        state["strategy"] = "ambiguous"
        state["target_entity"] = target
        state["metric_intent"] = metric
        state["routing_reason"] = "ambiguous: short or vague query, no clear target"
        state["suggestions"] = [
            "Você quer o livro melhor avaliado?",
            "Você quer a categoria melhor avaliada?",
            "Você quer os livros com mais reviews?",
        ]
        state["intent"] = "ambiguous"
        logger.info(
            "interpret_query: AMBIGUOUS query=%r target=%s metric=%s suggestions=%s",
            query, target, metric, state["suggestions"],
        )
        logger.info("interpret_query: completed in %.3fs.", time.perf_counter() - t0)
        return state

    # 4) Semantic-only: clear qualitative intent, no ranking
    if has_semantic_metric and not has_structured_metric:
        state["strategy"] = "semantic"
        state["target_entity"] = target
        state["metric_intent"] = metric
        state["routing_reason"] = f"semantic: metric={metric}"
        state["suggestions"] = []
        state["intent"] = "semantic"
        logger.info(
            "interpret_query: SEMANTIC strategy=semantic target_entity=%s metric_intent=%s query=%r",
            target, metric, query[:80],
        )
        logger.info("interpret_query: completed in %.3fs.", time.perf_counter() - t0)
        return state

    # 5) Hybrid: ranking + explanation (e.g. "mais polarizados e por quê")
    if has_structured_metric and (has_hybrid_suffix or has_semantic_metric):
        state["strategy"] = "hybrid"
        state["target_entity"] = target
        state["metric_intent"] = metric
        state["routing_reason"] = f"hybrid: structured metric + qualitative"
        state["suggestions"] = []
        state["intent"] = "hybrid"
        logger.info(
            "interpret_query: HYBRID query=%r target=%s metric=%s",
            query, target, metric,
        )
        logger.info("interpret_query: completed in %.3fs.", time.perf_counter() - t0)
        return state

    # 6) Structured: ranking/quantitative
    if has_structured_metric or (metric == "unknown" and target != "general"):
        state["strategy"] = "structured"
        state["target_entity"] = target
        # When metric is unknown but we have a target (e.g. "e os piores?"), prefer inherited or negative context
        if not has_structured_metric:
            last_metric = state.get("last_metric_intent")
            if last_metric in ("best_rated", "worst_rated", "most_reviewed", "most_polarized"):
                state["metric_intent"] = last_metric
            else:
                state["metric_intent"] = "best_rated"
        else:
            state["metric_intent"] = metric
        state["routing_reason"] = f"structured: target={target} metric={state['metric_intent']}"
        state["suggestions"] = []
        state["intent"] = "structured"
        logger.info(
            "interpret_query: STRUCTURED strategy=structured target_entity=%s metric_intent=%s query=%r",
            target, state["metric_intent"], query[:80],
        )
        logger.info("interpret_query: completed in %.3fs.", time.perf_counter() - t0)
        return state

    # 7) Default: do not fall back to semantic. Treat as ambiguous.
    state["strategy"] = "ambiguous"
    state["target_entity"] = target
    state["metric_intent"] = metric
    state["routing_reason"] = "ambiguous: no clear metric or target"
    state["suggestions"] = [
        "Você quer o livro melhor avaliado?",
        "Você quer a categoria melhor avaliada?",
        "Você quer os livros com mais reviews?",
    ]
    state["intent"] = "ambiguous"
    logger.info(
        "interpret_query: AMBIGUOUS (default) query=%r target=%s metric=%s",
        query, target, metric,
    )
    logger.info("interpret_query: completed in %.3fs.", time.perf_counter() - t0)
    return state


def build_ambiguous_response(state: WorkflowState) -> WorkflowState:
    """When strategy=ambiguous, set final_answer with suggestions, no tools/Bedrock."""
    t0 = time.perf_counter()
    state.setdefault("path_used", []).append("build_ambiguous_response")
    suggestions = state.get("suggestions") or [
        "Você quer o livro melhor avaliado?",
        "Você quer a categoria melhor avaliada?",
        "Você quer os livros com mais reviews?",
    ]
    lines = ["Sua pergunta pode ter mais de uma interpretação. Você pode reformular, por exemplo:"]
    for s in suggestions:
        lines.append(f"• {s}")
    state["final_answer"] = "\n".join(lines)
    logger.info(
        "build_ambiguous_response: completed in %.3fs. suggestions=%s",
        time.perf_counter() - t0, suggestions,
    )
    return state


def build_composite_response(state: WorkflowState) -> WorkflowState:
    """
    When is_composite_query / strategy=unsupported_composite, return transparent message
    and suggestions; do not call structured or semantic tools.
    """
    t0 = time.perf_counter()
    state.setdefault("path_used", []).append("build_composite_response")
    suggestions = state.get("suggestions") or [
        "Quais categorias têm maior média de avaliação?",
        "Qual autor tem melhor avaliação média?",
        "Quais são os livros mais polarizados?",
    ]
    lines = [COMPOSITE_RESPONSE_MESSAGE]
    if suggestions:
        lines.append("")
        lines.append("Reformulações possíveis:")
        for s in suggestions:
            lines.append(f"• {s}")
    state["final_answer"] = "\n".join(lines)
    logger.info(
        "build_composite_response: completed in %.3fs. is_composite_query=True composite_reason=%s",
        time.perf_counter() - t0,
        state.get("composite_reason"),
    )
    return state


def classify_intent(state: WorkflowState) -> WorkflowState:
    t0 = time.perf_counter()
    query = state.get("user_query", "")
    q = query.lower()
    intent = "semantic"

    structured_keywords = [
        # English
        "top ",
        "ranking",
        "highest",
        "average",
        "avg",
        "count",
        "volume",
        "most reviewed",
        "most reviews",
        "highest rated",
        "polarized",
        "categories",
        "category",
        "authors",
        "books",
        "rating",
        "ratings",
        "score",
        "scores",
        "recommend",
        "recommended",
        # Portuguese
        "maior",
        "maiores",
        "média",
        "médias",
        "melhor",
        "melhores",
        "quantidade",
        "volume",
        "categoria",
        "categorias",
        "autor",
        "autores",
        "livro",
        "livros",
        "polarizados",
        "nota",
        "notas",
        "avaliação",
        "avaliações",
        "recomendado",
        "recomendados",
        "recomendada",
        "recomendadas",
    ]

    semantic_keywords = [
        # English
        "why",
        "summarize",
        "summary",
        "themes",
        "opinions",
        "complaints",
        "praise",
        "what do reviews say",
        "what do the reviews say",
        "sentiment",
        # Portuguese
        "resuma",
        "resumo",
        "por que",
        "porque",
        "o que dizem",
        "opiniões",
        "reclamações",
        "elogios",
        "temas",
        "sentimento",
    ]

    structured_hits = [kw for kw in structured_keywords if kw in q]
    semantic_hits = [kw for kw in semantic_keywords if kw in q]

    if structured_hits and semantic_hits:
        intent = "hybrid"
    elif structured_hits:
        intent = "structured"
    else:
        intent = "semantic"

    logger.info(
        "classify_intent: query=%r, intent=%s, structured_hits=%s, semantic_hits=%s (%.3fs).",
        query,
        intent,
        structured_hits,
        semantic_hits,
        time.perf_counter() - t0,
    )
    state["intent"] = intent
    state.setdefault("path_used", []).append("classify_intent")
    return state


# Expected routing examples (strategy / target_entity / metric_intent / tool).
ROUTING_EXAMPLES = [
    ("Qual a categoria melhor avaliada?", "structured", "category", "best_rated", "get_top_categories_by_avg_score"),
    ("Qual o livro melhor avaliado?", "structured", "book", "best_rated", "get_best_rated_books"),
    ("Quais são os livros com mais reviews?", "structured", "book", "most_reviewed", "get_top_books_by_review_volume"),
    ("Quais são os livros mais polarizados e por quê?", "hybrid", "book", "most_polarized", "get_most_polarized_books"),
    ("Resuma as principais reclamações sobre Harry Potter", "semantic", "book", "complaint_summary", "search_similar_reviews"),
    ("Qual o mais vendido?", "out_of_scope", None, None, None),
    ("Qual o mais recomendado?", "ambiguous", "general", "recommended", None),
    ("Qual o livro com menor recomendação?", "structured", "book", "least_recommended", "get_lowest_rated_books"),
    ("Qual autor tem melhor avaliação média?", "structured", "author", "best_rated", "get_top_authors_by_avg_score"),
]


# Sentinel: when target is reviewer but no reviewer tool matches, do NOT use book/author tools.
REVIEWER_LIMITATION_TOOL = "_reviewer_limitation"


def _choose_structured_tool_from_interpret(
    target_entity: str | None, metric_intent: str | None
) -> tuple[str, str]:
    """Choose tool from interpret_query result (target_entity, metric_intent). Returns (tool_name, reason)."""
    target = target_entity or "general"
    metric = metric_intent or "unknown"
    # reviewer: only reviewer tools; never fall back to book/author
    if target == "reviewer":
        if metric == "most_reviewed":
            return "get_top_reviewers_by_review_volume", "reviewer+most_reviewed"
        if metric == "longest_reviews":
            return "get_reviewers_with_longest_reviews", "reviewer+longest_reviews"
        if metric in ("most_critical", "worst_rated"):
            return "get_most_critical_reviewers", "reviewer+most_critical"
        if metric in ("most_positive", "best_rated"):
            return "get_most_positive_reviewers", "reviewer+most_positive"
        if metric == "most_diverse":
            return "get_most_diverse_reviewers", "reviewer+most_diverse"
        return REVIEWER_LIMITATION_TOOL, "reviewer+no_matching_metric"
    # category + best_rated / worst_rated
    if target == "category":
        if metric == "best_rated":
            return "get_top_categories_by_avg_score", "category+best_rated"
        if metric == "worst_rated":
            return "get_worst_rated_categories", "category+worst_rated"
    # book
    if target == "book":
        if metric == "best_rated":
            return "get_best_rated_books", "book+best_rated"
        if metric in ("lowest_rated", "worst_rated"):
            return "get_lowest_rated_books", "book+worst_rated"
        if metric == "most_criticized":
            return "get_most_criticized_books", "book+most_criticized"
        if metric == "most_reviewed":
            return "get_top_books_by_review_volume", "book+most_reviewed"
        if metric == "most_polarized":
            return "get_most_polarized_books", "book+most_polarized"
        if metric == "recommended":
            return "get_most_recommended_books", "book+recommended"
        if metric == "least_recommended":
            return "get_lowest_rated_books", "book+least_recommended"
        if metric == "unknown":
            return "get_best_rated_books", "book+default_best_rated"
    # author
    if target == "author":
        if metric == "best_rated":
            return "get_top_authors_by_avg_score", "author+best_rated"
        if metric == "most_reviewed":
            return "get_top_authors_by_review_volume", "author+most_reviewed"
        if metric == "worst_rated":
            return "get_worst_rated_authors", "author+worst_rated"
        return "get_top_authors_by_avg_score", "author+default_best_rated"
    # general (e.g. "qual o mais recomendado?" after disambiguation we might get structured with general)
    if target == "general":
        if metric == "recommended":
            return "get_most_recommended_books", "general+recommended_proxy"
        if metric == "least_recommended":
            return "get_lowest_rated_books", "general+least_recommended_proxy"
    return "get_top_books_by_review_volume", "fallback_volume"


def _structured_tool_mcp_args(tool_name: str) -> dict:
    """Arguments for MCP tools/call (same defaults as direct tools)."""
    if tool_name == "get_top_categories_by_avg_score":
        return {"min_reviews": 100, "limit": 10}
    if tool_name == "get_most_polarized_books":
        return {"min_reviews": 50, "limit": 10}
    if tool_name in ("get_best_rated_books", "get_lowest_rated_books", "get_most_recommended_books"):
        return {"min_reviews": 100, "limit": 10}
    if tool_name in ("get_top_authors_by_avg_score", "get_worst_rated_authors"):
        return {"min_reviews": 30, "limit": 10}
    if tool_name == "get_worst_rated_categories":
        return {"min_reviews": 100, "limit": 10}
    if tool_name == "get_most_criticized_books":
        return {"min_negative_reviews": 20, "limit": 10}
    if tool_name == "get_top_authors_by_review_volume":
        return {"limit": 10}
    if tool_name == "get_top_reviewers_by_review_volume":
        return {"min_reviews": 5, "limit": 10}
    if tool_name == "get_reviewers_with_longest_reviews":
        return {"min_reviews": 3, "limit": 10}
    if tool_name in ("get_most_critical_reviewers", "get_most_positive_reviewers", "get_most_diverse_reviewers"):
        return {"min_reviews": 5, "limit": 10}
    return {"limit": 10}  # get_top_books_by_review_volume and fallback


def run_structured_tool(state: WorkflowState) -> WorkflowState:
    t0 = time.perf_counter()
    strategy = state.get("strategy")
    if strategy not in ("structured", "hybrid"):
        logger.info(
            "run_structured_tool: skipping strategy=%s (%.3fs).",
            strategy,
            time.perf_counter() - t0,
        )
        state.setdefault("path_used", []).append("run_structured_tool_skipped")
        return state

    target = state.get("target_entity")
    metric = state.get("metric_intent")
    tool_name, chosen_reason = _choose_structured_tool_from_interpret(target, metric)
    logger.info(
        "run_structured_tool: target=%s metric=%s -> tool=%s reason=%s",
        target,
        metric,
        tool_name,
        chosen_reason,
    )

    # Reviewer question but no matching reviewer metric -> do NOT call book/author tools
    if tool_name == REVIEWER_LIMITATION_TOOL:
        state["structured_results"] = {
            "tool": None,
            "rows": [],
            "limitation_message": (
                "A pergunta é sobre usuários/reviewers, mas não foi possível identificar qual critério usar. "
                "Especifique: mais reviews, reviews mais detalhadas, mais críticos, mais positivos ou mais diversidade de livros."
            ),
        }
        state.setdefault("path_used", []).append("run_structured_tool")
        return state

    mcp_args = _structured_tool_mcp_args(tool_name)
    mcp_result, mcp_error = call_tool_via_mcp(tool_name, mcp_args)
    if mcp_result is not None:
        result = mcp_result if isinstance(mcp_result, list) else [mcp_result]
        logger.info(
            "run_structured_tool: tool=%s rows=%d (real) in %.3fs strategy=structured (via MCP).",
            tool_name,
            len(result),
            time.perf_counter() - t0,
        )
    elif mcp_settings.fallback_to_local:
        logger.info(
            "run_structured_tool: MCP unavailable or failed (%s), using fallback (MCP_FALLBACK_TO_LOCAL=true).",
            mcp_error or "unknown",
        )
        with get_connection() as conn:
            if tool_name == "get_top_categories_by_avg_score":
                result = tools.get_top_categories_by_avg_score(
                    conn, min_reviews=100, limit=10
                )
            elif tool_name == "get_worst_rated_categories":
                result = tools.get_worst_rated_categories(
                    conn, min_reviews=100, limit=10
                )
            elif tool_name == "get_most_polarized_books":
                result = tools.get_most_polarized_books(
                    conn, min_reviews=50, limit=10
                )
            elif tool_name == "get_best_rated_books":
                result = tools.get_best_rated_books(
                    conn, min_reviews=100, limit=10
                )
            elif tool_name == "get_lowest_rated_books":
                result = tools.get_lowest_rated_books(
                    conn, min_reviews=100, limit=10
                )
            elif tool_name == "get_most_criticized_books":
                result = tools.get_most_criticized_books(
                    conn, min_negative_reviews=20, limit=10
                )
            elif tool_name == "get_most_recommended_books":
                result = tools.get_most_recommended_books(
                    conn, min_reviews=100, limit=10
                )
            elif tool_name == "get_top_authors_by_avg_score":
                result = tools.get_top_authors_by_avg_score(
                    conn, min_reviews=30, limit=10
                )
            elif tool_name == "get_worst_rated_authors":
                result = tools.get_worst_rated_authors(
                    conn, min_reviews=30, limit=10
                )
            elif tool_name == "get_top_authors_by_review_volume":
                result = tools.get_top_authors_by_review_volume(conn, limit=10)
            elif tool_name == "get_top_reviewers_by_review_volume":
                result = tools.get_top_reviewers_by_review_volume(
                    conn, min_reviews=5, limit=10
                )
            elif tool_name == "get_reviewers_with_longest_reviews":
                result = tools.get_reviewers_with_longest_reviews(
                    conn, min_reviews=3, limit=10
                )
            elif tool_name == "get_most_critical_reviewers":
                result = tools.get_most_critical_reviewers(
                    conn, min_reviews=5, limit=10
                )
            elif tool_name == "get_most_positive_reviewers":
                result = tools.get_most_positive_reviewers(
                    conn, min_reviews=5, limit=10
                )
            elif tool_name == "get_most_diverse_reviewers":
                result = tools.get_most_diverse_reviewers(
                    conn, min_reviews=5, limit=10
                )
            else:
                result = tools.get_top_books_by_review_volume(conn, limit=10)
        logger.info(
            "run_structured_tool: tool=%s rows=%d (real) in %.3fs (fallback local).",
            tool_name,
            len(result),
            time.perf_counter() - t0,
        )
    else:
        logger.warning(
            "run_structured_tool: MCP failed (%s) and MCP_FALLBACK_TO_LOCAL=false; no result.",
            mcp_error or "unknown",
        )
        result = []
    state["structured_results"] = {
        "tool": tool_name,
        "rows": result,
    }
    state.setdefault("path_used", []).append("run_structured_tool")
    return state


def run_semantic_tool(state: WorkflowState) -> WorkflowState:
    t0 = time.perf_counter()
    strategy = state.get("strategy")
    if strategy not in ("semantic", "hybrid"):
        logger.info(
            "run_semantic_tool: skipping strategy=%s (%.3fs).",
            strategy,
            time.perf_counter() - t0,
        )
        state.setdefault("path_used", []).append("run_semantic_tool_skipped")
        return state

    query = state.get("user_query", "")
    logger.info("run_semantic_tool: query=%r strategy=%s", query, strategy)

    mcp_result, mcp_error = call_tool_via_mcp(
        "search_similar_reviews",
        {"query_text": query, "top_k": 5},
    )
    if mcp_result is not None:
        results = mcp_result if isinstance(mcp_result, list) else [mcp_result]
        logger.info(
            "run_semantic_tool: tool=search_similar_reviews rows=%d (real) in %.3fs strategy=semantic (via MCP).",
            len(results),
            time.perf_counter() - t0,
        )
    elif mcp_settings.fallback_to_local:
        logger.info(
            "run_semantic_tool: MCP unavailable or failed (%s), using fallback (MCP_FALLBACK_TO_LOCAL=true).",
            mcp_error or "unknown",
        )
        with get_connection() as conn:
            results = search_similar_reviews(conn, query_text=query, top_k=5)
        logger.info(
            "run_semantic_tool: tool=search_similar_reviews rows=%d (real) in %.3fs (fallback local).",
            len(results),
            time.perf_counter() - t0,
        )
    else:
        logger.warning(
            "run_semantic_tool: MCP failed (%s) and MCP_FALLBACK_TO_LOCAL=false; no result.",
            mcp_error or "unknown",
        )
        results = []
    state["semantic_results"] = {
        "tool": "search_similar_reviews",
        "rows": results,
    }
    state.setdefault("path_used", []).append("run_semantic_tool")
    return state


def _summarize_results_for_prompt(
    structured_results: Any, semantic_results: Any
) -> str:
    parts: list[str] = []
    if structured_results:
        limitation = structured_results.get("limitation_message")
        if limitation:
            parts.append("Structured results: limitation (no tool called).\n")
            parts.append(limitation)
        else:
            rows = structured_results.get("rows", [])
            tool = structured_results.get("tool") or "unknown"
            parts.append(
                f"Structured results from tool '{tool}' (showing up to 5 rows):\n"
            )
            parts.append(
                json.dumps(rows[:5], indent=2, default=str)
            )
    if semantic_results:
        rows = semantic_results.get("rows", [])
        tool = semantic_results.get("tool")
        parts.append(
            f"\nSemantic results from tool '{tool}' (showing up to 5 rows):\n"
        )
        parts.append(
            json.dumps(rows[:5], indent=2, default=str)
        )
    return "\n".join(parts) if parts else "No tool results available."


def generate_final_answer(state: WorkflowState) -> WorkflowState:
    t0 = time.perf_counter()
    query = state.get("user_query", "")
    strategy = state.get("strategy") or state.get("intent") or "structured"
    structured = state.get("structured_results")
    semantic = state.get("semantic_results")
    tool_name = (structured or {}).get("tool") if structured else None
    logger.info(
        "generate_final_answer: query=%r strategy=%s tool=%s",
        query,
        strategy,
        tool_name,
    )

    # Reviewer limitation: no matching reviewer tool -> return message and skip LLM
    if structured and structured.get("limitation_message"):
        state["final_answer"] = structured["limitation_message"]
        logger.info(
            "generate_final_answer: returning reviewer limitation message (no LLM)."
        )
        state.setdefault("path_used", []).append("generate_final_answer")
        return state

    # Simple heuristic: if the question contains common Portuguese accents/words,
    # we treat the user language as pt-BR and build prompts in Portuguese.
    q_lower = query.lower()
    is_pt_br = any(
        token in q_lower
        for token in [
            " qual ",
            " quais ",
            " livro",
            "categoria",
            "autor",
            "avalia",
            "resuma",
            "reclama",
            "pior",
            "melhor",
            "mais vendido",
        ]
    ) or any(ch in q_lower for ch in ["á", "é", "í", "ó", "ú", "ã", "õ", "ç"])

    # Context from tools by strategy
    if strategy == "structured":
        tools_context = _summarize_results_for_prompt(structured, None)
    elif strategy == "semantic":
        tools_context = _summarize_results_for_prompt(None, semantic)
    else:  # hybrid or fallback
        tools_context = _summarize_results_for_prompt(structured, semantic)

    # When we used the "most recommended" proxy, make the interpretation transparent.
    recommended_proxy_note = ""
    if tool_name == "get_most_recommended_books":
        recommended_proxy_note = (
            "IMPORTANT: The user asked about 'most recommended' (or similar). "
            "We do not have sales or recommendation data. The results are a PROXY: "
            "books with highest average review score and a minimum number of reviews. "
            "Start your answer by briefly stating this interpretation in the user's language, "
            "e.g. 'Interpretando \"mais recomendado\" como livros com alta média de avaliação e volume mínimo de reviews, os principais resultados são...' "
            "or 'Interpreting \"most recommended\" as books with the highest average rating and sufficient reviews, the top results are...' "
            "Then present the ranking from the context.\n\n"
        )
    # When we used best-rated (by average score), state clearly: ranking by mean rating + min reviews.
    best_rated_note = ""
    if tool_name == "get_best_rated_books":
        best_rated_note = (
            "The results are a ranking by AVERAGE REVIEW SCORE (mean rating), with a minimum number of reviews per book. "
            "State this clearly in your answer: e.g. 'Ranking por média de avaliação (com mínimo de reviews):' or "
            "'Ranking by average rating (with a minimum review count):'. Do not use ambiguous language; the user asked for best-rated / highest-rated books.\n\n"
        )
    # Categories by avg score
    categories_avg_note = ""
    if tool_name == "get_top_categories_by_avg_score":
        categories_avg_note = (
            "The results are a ranking of CATEGORIES by AVERAGE REVIEW SCORE (mean rating), with a minimum number of reviews per category. "
            "State this clearly in your answer. Do not use ambiguous language.\n\n"
        )
    # Lowest rated / least recommended proxy
    lowest_rated_note = ""
    if tool_name == "get_lowest_rated_books":
        lowest_rated_note = (
            "The results are a ranking of books with LOWEST average review score (minimum review count). "
            "State clearly that this is a proxy for 'least recommended' or 'menor recomendação': e.g. "
            "'Interpretando menor recomendação como livros com menor média de avaliação (e mínimo de reviews)...'\n\n"
        )
    # Reviewer questions: ground only in reviewer-level rows; do not use book/author rows as user insights
    reviewer_grounding_note = ""
    if state.get("target_entity") == "reviewer":
        reviewer_grounding_note = (
            "The user asked about REVIEWERS/USERS (usuários, leitores, perfis). "
            "You MUST ground your answer ONLY in reviewer-level results (rows with user_id, profile_name, review_count, avg_score, etc.). "
            "Do NOT reinterpret book-level or author-level rows as user/reviewer insights. "
            "If the context contains only book or author rows and no reviewer rows, you MUST state explicitly that the available data does not support the requested reviewer analysis.\n\n"
        )

    # --- Data analyst grounding (strict data-only reasoning, no hallucinated statistics) ---
    DATA_ANALYST_GROUNDING_EN = (
        "You are a data analyst writing a brief analytical report. You perform DESCRIPTIVE ANALYTICS ONLY: "
        "you summarize and describe what the data shows. You do NOT perform statistical inference, "
        "hypothesis testing, or causal claims.\n\n"
        "STRICT RULES:\n"
        "1. Use ONLY the rows returned by the tools in the context below. Do not cite, infer, or assume anything not present in that context.\n"
        "2. If the available data is insufficient to answer the question analytically, say so explicitly (e.g. 'The data provided does not support an answer to this question' or 'Only N rows were returned; conclusions are limited').\n"
        "3. Do NOT invent metrics: if variance, standard deviation, correlation, or other statistics are not in the data, do not mention them. If a metric is missing, state that the dataset does not provide it.\n"
        "4. If the sample size is small (e.g. few rows), explicitly note that the conclusion may not be statistically meaningful or representative.\n"
        "5. Avoid unsupported causal or inferential language. Do NOT use phrases like 'this indicates', 'this suggests a trend', 'this implies' unless the data clearly and directly supports that claim. Prefer neutral descriptions: 'Based on the available data, these items have...' or 'The returned rows show...'.\n"
        "6. Distinguish clearly: you are describing what is in the results (descriptive), not drawing conclusions about populations or causes (inference).\n\n"
        "REQUIRED ANSWER STRUCTURE:\n"
        "1. Short title describing the analysis.\n"
        "2. Data summary: present the top rows returned by the tools (names, scores, counts as given).\n"
        "3. Objective interpretation: what the numbers/rows show, without extrapolation.\n"
        "4. Limitations: note dataset or sample limitations (e.g. small N, missing metrics, descriptive only).\n"
        "5. Optional insight: only if the data clearly supports it; otherwise omit.\n\n"
    )
    DATA_ANALYST_GROUNDING_PT_BR = (
        "Você é um analista de dados redigindo um breve relatório analítico. Você realiza apenas ANÁLISE DESCRITIVA: "
        "resume e descreve o que os dados mostram. Você NÃO realiza inferência estatística, testes de hipótese ou afirmações causais.\n\n"
        "REGRAS RÍGIDAS:\n"
        "1. Use APENAS as linhas retornadas pelas tools no contexto abaixo. Não cite, infira ou assuma nada que não esteja nesse contexto.\n"
        "2. Se os dados disponíveis forem insuficientes para responder à pergunta de forma analítica, diga isso explicitamente (ex.: 'Os dados fornecidos não permitem responder a esta pergunta' ou 'Apenas N linhas foram retornadas; as conclusões são limitadas').\n"
        "3. NÃO invente métricas: se variância, desvio padrão, correlação ou outras estatísticas não estiverem nos dados, não as mencione. Se uma métrica faltar, diga que o dataset não a fornece.\n"
        "4. Se o tamanho da amostra for pequeno (poucas linhas), mencione explicitamente que a conclusão pode não ser estatisticamente significativa ou representativa.\n"
        "5. Evite linguagem causal ou inferencial não suportada. NÃO use frases como 'isso indica', 'isso sugere uma tendência', 'isso implica' a menos que os dados apoiem claramente essa afirmação. Prefira descrições neutras: 'Com base nos dados disponíveis, estes itens têm...' ou 'As linhas retornadas mostram...'.\n"
        "6. Deixe claro: você está descrevendo o que está nos resultados (descritivo), não tirando conclusões sobre populações ou causas (inferência).\n\n"
        "ESTRUTURA OBRIGATÓRIA DA RESPOSTA:\n"
        "1. Título curto descrevendo a análise.\n"
        "2. Resumo dos dados: apresente as principais linhas retornadas pelas tools (nomes, scores, contagens conforme fornecidos).\n"
        "3. Interpretação objetiva: o que os números/linhas mostram, sem extrapolação.\n"
        "4. Limitações: cite limitações do dataset ou da amostra (ex.: N pequeno, métricas ausentes, apenas descritivo).\n"
        "5. Insight opcional: somente se os dados apoiarem claramente; caso contrário omita.\n\n"
    )

    if is_pt_br:
        grounding = DATA_ANALYST_GROUNDING_PT_BR
        lang_instruction = (
            "Responda INTEGRALMENTE em português do Brasil, exceto nomes próprios "
            "de livros, autores, editoras ou categorias.\n\n"
        )
    else:
        grounding = DATA_ANALYST_GROUNDING_EN
        lang_instruction = "Respond in the SAME LANGUAGE as the user question.\n\n"

    if is_pt_br:
        # Prompts em português: analista de dados + notas de tool + estratégia.
        if strategy == "structured":
            strategy_block = (
                "A pergunta foi classificada como ESTRUTURADA / QUANTITATIVA. "
                "Use APENAS os resultados estruturados fornecidos no contexto.\n\n"
            )
        elif strategy == "semantic":
            strategy_block = (
                "A pergunta foi classificada como SEMÂNTICA / QUALITATIVA. "
                "Use APENAS os trechos de reviews fornecidos no contexto. "
                "Resuma temas, opiniões, reclamações ou elogios presentes nos trechos; não invente conteúdo.\n\n"
            )
        else:  # hybrid
            strategy_block = (
                "A pergunta foi classificada como HÍBRIDA (ranking quantitativo + qualitativo). "
                "Use o contexto estruturado e semântico fornecido. "
                "Apresente primeiro o ranking com métricas; depois resuma temas/opiniões dos trechos semânticos, sem extrapolar.\n\n"
            )
        system_prompt = (
            grounding
            + recommended_proxy_note
            + best_rated_note
            + categories_avg_note
            + lowest_rated_note
            + reviewer_grounding_note
            + strategy_block
            + lang_instruction
        )
    else:
        # English (or other): data analyst grounding + tool notes + strategy.
        if strategy == "structured":
            strategy_block = (
                "The question has been classified as STRUCTURED / QUANTITATIVE. "
                "Use ONLY the structured results provided in the context.\n\n"
            )
        elif strategy == "semantic":
            strategy_block = (
                "The question has been classified as SEMANTIC / QUALITATIVE. "
                "Use ONLY the review snippets provided in the context. "
                "Summarize themes, opinions, complaints or praise present in the snippets; do not invent content.\n\n"
            )
        else:  # hybrid
            strategy_block = (
                "The question has been classified as HYBRID (quantitative ranking + qualitative). "
                "Use the structured and semantic context provided. "
                "Present the ranking with metrics first; then summarize themes/opinions from the semantic snippets without extrapolating.\n\n"
            )
        system_prompt = (
            grounding
            + recommended_proxy_note
            + best_rated_note
            + categories_avg_note
            + lowest_rated_note
            + reviewer_grounding_note
            + strategy_block
            + lang_instruction
        )

    user_prompt = (
        f"User question:\n{query}\n\n"
        f"Strategy: {strategy}\n\n"
        "Context from tools:\n"
        f"{tools_context}\n\n"
        "Please answer the user question above using ONLY this context."
    )

    client = get_bedrock_client()
    # If the user or API selected a specific model_id, honor it here.
    model_from_state = state.get("model_id")
    if model_from_state:
        client.model_id = model_from_state
    try:
        answer = client.generate_from_messages(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        state["final_answer"] = answer
        # Persist the effective model used (after any fallback).
        state["model_id"] = client.model_id
        logger.info(
            "generate_final_answer: Bedrock call succeeded. model_id_used=%s",
            client.model_id,
        )
    except RuntimeError as exc:
        msg = str(exc)
        logger.error("generate_final_answer: Bedrock call failed: %s", msg)
        errors = state.get("errors") or []
        errors.append(msg)
        state["errors"] = errors
        state["final_answer"] = (
            "The generative layer (Bedrock) failed temporarily, but the "
            "structured and semantic results above were retrieved "
            "successfully. Please try again later for a natural language "
            "summary."
        )

    logger.info(
        "generate_final_answer: node completed in %.3fs.",
        time.perf_counter() - t0,
    )
    state.setdefault("path_used", []).append("generate_final_answer")
    return state


def _debug_classify_examples() -> None:
    """
    Small helper to log classification of a few example queries.
    Not called automatically; use for manual debugging.
    """
    examples = {
        "Quais são as categorias com maior média de avaliação?": "structured",
        "Quais são os livros mais polarizados e por quê?": "hybrid",
        "Resuma as principais reclamações sobre Harry Potter": "semantic",
        "What are the categories with the highest average review scores?": "structured",
    }
    for text, expected in examples.items():
        state: WorkflowState = {"user_query": text}
        out = classify_intent(state)
        logger.info(
            "Example: %r -> intent=%s (expected=%s)",
            text,
            out.get("intent"),
            expected,
        )


def _debug_routing_examples() -> None:
    """
    Log interpret_query + tool for each ROUTING_EXAMPLES entry.
    Not called automatically; use for manual verification.
    """
    for query, exp_strategy, exp_target, exp_metric, exp_tool in ROUTING_EXAMPLES:
        state: WorkflowState = {"user_query": query}
        interpret_query(state)
        strategy = state.get("strategy")
        target = state.get("target_entity")
        metric = state.get("metric_intent")
        tool_name, reason = _choose_structured_tool_from_interpret(target, metric) if strategy in ("structured", "hybrid") else (None, "")
        ok = strategy == exp_strategy and (exp_tool is None or tool_name == exp_tool)
        logger.info(
            "Example: %r -> strategy=%s target=%s metric=%s tool=%s (expected: %s/%s/%s/%s) %s",
            query, strategy, target, metric, tool_name,
            exp_strategy, exp_target, exp_metric, exp_tool,
            "ok" if ok else "MISMATCH",
        )

