from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        description="User question to send to the agentic workflow.",
    )
    model_id: Optional[str] = Field(
        default=None,
        description="Optional Bedrock model id to use for the final generation step.",
    )


class ChatResponse(BaseModel):
    question: str
    intent: Optional[str] = None
    path_used: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    structured_results: Optional[Any] = None
    semantic_results: Optional[Any] = None
    final_answer: Optional[str] = None
    out_of_scope: bool = False
    scope_message: Optional[str] = None
    strategy: Optional[str] = None
    target_entity: Optional[str] = None
    metric_intent: Optional[str] = None
    routing_reason: Optional[str] = None
    suggestions: List[str] = Field(default_factory=list)
    is_composite_query: bool = False
    composite_reason: Optional[str] = None
    # Execution metadata for frontend/demo
    structured_rows: int = Field(
        default=0,
        description="Number of rows in structured_results.rows (0 if none).",
    )
    semantic_rows: int = Field(
        default=0,
        description="Number of rows in semantic_results.rows (0 if none).",
    )
    total_time_ms: Optional[float] = Field(
        default=None,
        description="Total request processing time in milliseconds (controller-level).",
    )
    model_id: Optional[str] = Field(
        default=None,
        description="Bedrock model id effectively used for the final generation (after fallback, if any).",
    )


