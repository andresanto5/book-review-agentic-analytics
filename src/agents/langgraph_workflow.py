from __future__ import annotations

import logging
import time
from typing import Dict, Any, Optional

from langgraph.graph import END, START, StateGraph

from src.agents.langgraph_nodes import (
    build_ambiguous_response,
    build_composite_response,
    build_out_of_scope_response,
    generate_final_answer,
    interpret_query,
    run_semantic_tool,
    run_structured_tool,
)
from src.agents.langgraph_state import WorkflowState, initial_state


logger = logging.getLogger(__name__)


def _route_after_interpret(state: WorkflowState) -> str:
    """Route after interpret_query: out_of_scope, composite, ambiguous, or main pipeline."""
    if state.get("out_of_scope"):
        return "build_out_of_scope_response"
    if state.get("is_composite_query") or state.get("strategy") == "unsupported_composite":
        return "build_composite_response"
    if state.get("strategy") == "ambiguous":
        return "build_ambiguous_response"
    return "run_structured_tool"


def build_workflow() -> StateGraph:
    graph: StateGraph = StateGraph(WorkflowState)

    graph.add_node("interpret_query", interpret_query)
    graph.add_node("build_out_of_scope_response", build_out_of_scope_response)
    graph.add_node("build_composite_response", build_composite_response)
    graph.add_node("build_ambiguous_response", build_ambiguous_response)
    graph.add_node("run_structured_tool", run_structured_tool)
    graph.add_node("run_semantic_tool", run_semantic_tool)
    graph.add_node("generate_final_answer", generate_final_answer)

    graph.add_edge(START, "interpret_query")
    graph.add_conditional_edges(
        "interpret_query",
        _route_after_interpret,
        {
            "build_out_of_scope_response": "build_out_of_scope_response",
            "build_composite_response": "build_composite_response",
            "build_ambiguous_response": "build_ambiguous_response",
            "run_structured_tool": "run_structured_tool",
        },
    )
    graph.add_edge("build_out_of_scope_response", END)
    graph.add_edge("build_composite_response", END)
    graph.add_edge("build_ambiguous_response", END)
    graph.add_edge("run_structured_tool", "run_semantic_tool")
    graph.add_edge("run_semantic_tool", "generate_final_answer")
    graph.add_edge("generate_final_answer", END)

    return graph


_compiled_app = None


def get_compiled_workflow():
    global _compiled_app
    if _compiled_app is None:
        logger.info("Compiling LangGraph workflow.")
        graph = build_workflow()
        _compiled_app = graph.compile()
    return _compiled_app


def run_workflow(user_query: str, model_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the LangGraph workflow for a single user query.
    Returns the final WorkflowState as a plain dict.
    """
    app = get_compiled_workflow()
    state = initial_state(user_query, model_id=model_id)
    logger.info("Running workflow for query=%r model_id=%r", user_query, model_id)
    t0 = time.perf_counter()
    result: WorkflowState = app.invoke(state)  # type: ignore[assignment]
    elapsed = time.perf_counter() - t0
    logger.info(
        "Workflow finished in %.3fs. path_used=%s.",
        elapsed,
        result.get("path_used", []),
    )
    return dict(result)


