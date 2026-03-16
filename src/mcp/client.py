"""
MCP client: call tools via a persistent MCP server (streamable-http).
Uses one reusable connection/session per process. Server must be running separately.
Sync API for LangGraph nodes; optional fallback to local tools when MCP unavailable.
"""
from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

from src.config.settings import mcp_settings

logger = logging.getLogger(__name__)

# Tools that return list of rows (we normalize to list[dict])
LIST_TOOLS = frozenset({
    "get_top_categories_by_avg_score",
    "get_top_books_by_review_volume",
    "get_best_rated_books",
    "get_lowest_rated_books",
    "get_most_polarized_books",
    "get_most_recommended_books",
    "get_top_authors_by_avg_score",
    "get_top_authors_by_review_volume",
    "search_similar_reviews",
    "resolve_book_candidates",
    "get_book_review_context_by_book_pk",
    "get_top_reviewers_by_review_volume",
    "get_reviewers_with_longest_reviews",
    "get_most_critical_reviewers",
    "get_most_positive_reviewers",
    "get_most_diverse_reviewers",
})


def is_mcp_available() -> bool:
    """True if MCP is enabled and transport/URL configured."""
    if not mcp_settings.enabled:
        return False
    if mcp_settings.transport != "streamable-http":
        return False
    if not (mcp_settings.server_url or "").strip():
        return False
    return True


def _unwrap_envelope(parsed: Any) -> tuple[Any, str]:
    """If parsed is a dict with result/data/rows containing a list, return that list and path label."""
    if isinstance(parsed, dict):
        for key in ("result", "data", "rows", "content"):
            if key in parsed and isinstance(parsed[key], list):
                return parsed[key], f"envelope.{key}"
    return parsed, "raw"


def _normalize_rows(parsed: Any, tool_name: str) -> list[dict]:
    """Ensure we always return list[dict] for tool results (consistent with workflow)."""
    if parsed is None:
        return []
    parsed, _ = _unwrap_envelope(parsed)
    if isinstance(parsed, list):
        return [x if isinstance(x, dict) else dict(x) for x in parsed]
    if isinstance(parsed, dict):
        return [parsed]
    return []


def _parse_call_result(result: Any) -> tuple[list[dict] | dict[str, Any] | None, str]:
    """
    Extract list/dict from MCP CallToolResult (content or structuredContent).
    Returns (parsed_value, parsing_path) for logging.
    Unwraps envelope dicts (result/data/rows) so list tools get the real list.
    """
    if result is None:
        return None, "none"
    # 1) structuredContent (server may send list or envelope here)
    if getattr(result, "structuredContent", None) is not None:
        raw = result.structuredContent
        unwrapped, path = _unwrap_envelope(raw)
        path_label = "structuredContent" + (f"({path})" if path != "raw" else "")
        return unwrapped, path_label
    # 2) content: list of ContentBlock (often one JSON per block or one block with full JSON)
    content = getattr(result, "content", None) or []
    texts: list[str] = []
    for block in content:
        if hasattr(block, "text"):
            texts.append(block.text)
    if not texts:
        return None, "content_empty"
    if len(texts) == 1:
        try:
            raw = json.loads(texts[0])
            unwrapped, path = _unwrap_envelope(raw)
            path_label = "content_single_block" + (f"({path})" if path != "raw" else "")
            return unwrapped, path_label
        except (json.JSONDecodeError, TypeError):
            return None, "content_single_block_parse_error"
    out: list[Any] = []
    for t in texts:
        try:
            out.append(json.loads(t))
        except (json.JSONDecodeError, TypeError):
            pass
    path_label = f"content_multi_block(n={len(out)})"
    return out if out else None, path_label


# --- Persistent session (one per process) ---
_loop: asyncio.AbstractEventLoop | None = None
_loop_thread: threading.Thread | None = None
_session: ClientSession | None = None
_http_context_cm = None  # streamable_http_client context manager (keep ref so it stays entered)
_lock = threading.Lock()
_connection_time_sec: float | None = None
_connected_at: float | None = None


def _run_loop() -> None:
    global _loop
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    _loop.run_forever()


def _get_loop() -> asyncio.AbstractEventLoop:
    global _loop, _loop_thread
    with _lock:
        if _loop is None:
            _loop_thread = threading.Thread(target=_run_loop, daemon=True)
            _loop_thread.start()
            while _loop is None:
                time.sleep(0.01)
    return _loop


async def _connect_async() -> tuple[ClientSession | None, str | None]:
    """Connect to MCP server (streamable-http). Returns (session, error). Keeps context open."""
    global _session, _http_context_cm, _connection_time_sec, _connected_at
    url = mcp_settings.server_url.strip()
    t0 = time.perf_counter()
    try:
        ctx = streamable_http_client(url)
        _http_context_cm = ctx  # keep ref so context is not closed by GC
        read_stream, write_stream, _ = await ctx.__aenter__()
        session = ClientSession(read_stream, write_stream)
        await session.__aenter__()
        await session.initialize()
        _session = session
        _connection_time_sec = time.perf_counter() - t0
        _connected_at = time.perf_counter()
        logger.info(
            "MCP client connected to %s in %.3fs (persistent session).",
            url,
            _connection_time_sec,
        )
        return _session, None
    except Exception as e:
        elapsed = time.perf_counter() - t0
        logger.warning("MCP client connection failed to %s in %.3fs: %s", url, elapsed, e)
        return None, str(e)


async def _call_tool_async(name: str, arguments: dict[str, Any] | None) -> tuple[list[dict] | dict[str, Any] | None, str | None]:
    """Call one tool using the persistent session. Returns (parsed_result, error)."""
    global _session
    args = arguments or {}
    if _session is None:
        session, err = await _connect_async()
        if session is None:
            return None, err or "connection failed"
    t0 = time.perf_counter()
    try:
        call_result = await _session.call_tool(name, arguments=args)
        elapsed = time.perf_counter() - t0
        if getattr(call_result, "isError", False):
            err = getattr(call_result, "content", None)
            err_msg = str(err) if err else "tools/call returned isError"
            return None, err_msg
        parsed, parsing_path = _parse_call_result(call_result)
        if name in LIST_TOOLS and parsed is not None:
            rows = _normalize_rows(parsed, name)
            logger.info(
                "MCP call_tool name=%s rows=%d elapsed=%.3fs parsing=%s persistent=yes",
                name,
                len(rows),
                elapsed,
                parsing_path,
            )
            return rows, None
        logger.info(
            "MCP call_tool name=%s elapsed=%.3fs parsing=%s persistent=yes",
            name,
            elapsed,
            parsing_path,
        )
        return parsed, None
    except Exception as e:
        _session = None
        elapsed = time.perf_counter() - t0
        logger.warning("MCP call_tool name=%s failed in %.3fs (session invalidated): %s", name, elapsed, e)
        return None, str(e)


def call_tool_via_mcp(
    name: str,
    arguments: dict[str, Any] | None = None,
) -> tuple[list[dict] | dict[str, Any] | None, str | None]:
    """
    Call tool via persistent MCP server. Returns (result, error).
    result: list[dict] for list tools; else dict or list. error: None on success.
    """
    if not is_mcp_available():
        return None, "MCP disabled or not configured"
    loop = _get_loop()
    future = asyncio.run_coroutine_threadsafe(
        _call_tool_async(name, arguments or {}),
        loop,
    )
    try:
        result, err = future.result(timeout=60)
    except Exception as e:
        logger.warning("MCP call_tool name=%s fallback=yes exception=%s", name, e, exc_info=True)
        return None, str(e)
    if err:
        logger.warning(
            "MCP call_tool name=%s fallback=yes error=%s",
            name,
            err,
        )
        return None, err
    return result, None


def get_mcp_connection_info() -> dict[str, Any]:
    """For logging: whether we have a persistent session and connection time."""
    return {
        "persistent_session": _session is not None,
        "connection_time_sec": _connection_time_sec,
        "connected_at": _connected_at,
    }
