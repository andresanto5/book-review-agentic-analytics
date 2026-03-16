from __future__ import annotations

import logging
import time
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers.chat import router as chat_router
from api.routers.health import router as health_router


logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    app = FastAPI(
        title="Book Review Agentic API",
        version="0.1.0",
        description=(
            "API para consulta agentic controlada sobre a base de avaliações "
            "de livros (PostgreSQL + pgvector + LangGraph + Amazon Bedrock)."
        ),
    )

    # CORS para permitir o frontend Vite (http://localhost:5173) acessar /chat/ask e /health
    frontend_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=frontend_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(chat_router)

    @app.on_event("startup")
    async def on_startup() -> None:  # pragma: no cover
        logger.info("Starting Book Review Agentic API...")
        t0 = time.perf_counter()
        try:
            from src.embeddings.embedding_client import get_embedding_client
            get_embedding_client()
            logger.info(
                "Startup: embedding model preloaded in %.3fs (ready for first semantic request).",
                time.perf_counter() - t0,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Startup: embedding model preload failed (will load on first use): %s",
                exc,
            )
        try:
            from src.mcp.client import is_mcp_available
            from src.config.settings import mcp_settings
            if is_mcp_available():
                logger.info(
                    "Startup: MCP enabled (persistent client to %s). Fallback local=%s.",
                    mcp_settings.server_url,
                    mcp_settings.fallback_to_local,
                )
            else:
                logger.info("Startup: MCP disabled (tools will use local only).")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Startup: MCP check failed: %s", exc)
        logger.info("Book Review Agentic API startup complete.")

    @app.on_event("shutdown")
    async def on_shutdown() -> None:  # pragma: no cover
        logger.info("Shutting down Book Review Agentic API...")

    return app


app = create_app()

