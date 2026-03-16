from __future__ import annotations

import logging

from fastapi import APIRouter

from api.controllers.chat_controller import handle_chat
from api.schemas.chat_schema import ChatRequest, ChatResponse


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ask", response_model=ChatResponse)
async def chat_ask(payload: ChatRequest) -> ChatResponse:
    """
    Call the LangGraph + Bedrock workflow with a user question.
    """
    return handle_chat(payload)


