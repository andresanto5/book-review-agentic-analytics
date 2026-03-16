from __future__ import annotations

from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict


class WorkflowState(TypedDict, total=False):
    user_query: str
    intent: str
    structured_results: Optional[Any]
    semantic_results: Optional[Any]
    final_answer: Optional[str]
    path_used: List[str]
    errors: List[str]
    out_of_scope: bool
    scope_message: Optional[str]
    strategy: Optional[str]  # structured / semantic / hybrid / out_of_scope / ambiguous / unsupported_composite
    target_entity: Optional[str]
    metric_intent: Optional[str]
    routing_reason: Optional[str]
    suggestions: List[str]
    is_composite_query: bool
    composite_reason: Optional[str]
    # LLM / execution metadata
    model_id: Optional[str]


def initial_state(user_query: str, model_id: Optional[str] = None) -> WorkflowState:
    return WorkflowState(
        user_query=user_query,
        intent="",
        structured_results=None,
        semantic_results=None,
        final_answer=None,
        path_used=[],
        errors=[],
        out_of_scope=False,
        scope_message=None,
        strategy=None,
        target_entity=None,
        metric_intent=None,
        routing_reason=None,
        suggestions=[],
        is_composite_query=False,
        composite_reason=None,
        model_id=model_id,
    )

