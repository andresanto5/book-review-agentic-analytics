from __future__ import annotations

import logging
import time
from typing import Any, Dict

from fastapi import HTTPException

from api.schemas.chat_schema import ChatRequest, ChatResponse
from src.agents.langgraph_workflow import run_workflow


logger = logging.getLogger(__name__)


def handle_chat(request: ChatRequest) -> ChatResponse:
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    logger.info(
        "Received chat request: %r model_id_requested=%r",
        question,
        request.model_id,
    )
    t0 = time.perf_counter()

    try:
        state: Dict[str, Any] = run_workflow(question, model_id=request.model_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error while running LangGraph workflow: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Internal error while processing the question. Please try again later.",
        ) from exc

    elapsed = time.perf_counter() - t0

    # Count rows from structured/semantic results for both logging and response metadata
    structured = state.get("structured_results") or {}
    semantic = state.get("semantic_results") or {}
    struct_rows = len(structured.get("rows") or [])
    sem_rows = len(semantic.get("rows") or [])

    # Effective model id after any Bedrock fallback (set in workflow state by generate_final_answer)
    model_id_used = state.get("model_id")

    response = ChatResponse(
        question=question,
        intent=state.get("intent"),
        path_used=state.get("path_used") or [],
        errors=state.get("errors") or [],
        structured_results=state.get("structured_results"),
        semantic_results=state.get("semantic_results"),
        final_answer=state.get("final_answer"),
        out_of_scope=state.get("out_of_scope", False),
        scope_message=state.get("scope_message"),
        strategy=state.get("strategy"),
        target_entity=state.get("target_entity"),
        metric_intent=state.get("metric_intent"),
        routing_reason=state.get("routing_reason"),
        suggestions=state.get("suggestions") or [],
        is_composite_query=state.get("is_composite_query", False),
        composite_reason=state.get("composite_reason"),
        structured_rows=struct_rows,
        semantic_rows=sem_rows,
        total_time_ms=elapsed * 1000.0,
        model_id=model_id_used,
    )
    logger.info(
        (
            "Chat request completed in %.3fs. strategy=%s target_entity=%s "
            "metric_intent=%s tool_struct=%s rows_struct=%d tool_semantic=%s "
            "rows_semantic=%d path_used=%s model_id_requested=%s model_id_used=%s"
        ),
        elapsed,
        response.strategy,
        response.target_entity,
        response.metric_intent,
        (response.structured_results or {}).get("tool"),
        struct_rows,
        (response.semantic_results or {}).get("tool"),
        sem_rows,
        response.path_used,
        request.model_id,
        model_id_used,
    )
    if response.out_of_scope:
        logger.info("Out-of-scope response returned. scope_message=%s", response.scope_message)
    return response


