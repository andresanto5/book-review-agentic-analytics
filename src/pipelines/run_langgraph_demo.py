from __future__ import annotations

import argparse
import logging
from pprint import pprint

from src.agents.langgraph_workflow import run_workflow


logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


DEFAULT_QUESTION = (
    "Which books are the most polarized and why?"
)


def main() -> None:
    _configure_logging()

    parser = argparse.ArgumentParser(
        description="Run LangGraph + Bedrock demo over the A3Data book review project."
    )
    parser.add_argument(
        "--question",
        type=str,
        default=None,
        help="User question to send to the workflow.",
    )
    args = parser.parse_args()

    user_query = args.question or DEFAULT_QUESTION
    print(f"User question: {user_query!r}\n")

    state = run_workflow(user_query)

    print(f"Intent detected: {state.get('intent')!r}")
    print(f"Path used: {state.get('path_used')}")
    print(f"Errors: {state.get('errors')}\n")

    structured = state.get("structured_results")
    semantic = state.get("semantic_results")

    print("Structured results (summary):")
    if structured and isinstance(structured, dict):
        tool = structured.get("tool")
        rows = structured.get("rows") or []
        print(f"  tool: {tool}")
        print(f"  rows: {len(rows)} (showing up to 3)")
        pprint(rows[:3])
    else:
        print("  None")

    print("\nSemantic results (summary):")
    if semantic and isinstance(semantic, dict):
        tool = semantic.get("tool")
        rows = semantic.get("rows") or []
        print(f"  tool: {tool}")
        print(f"  rows: {len(rows)} (showing up to 3)")
        pprint(rows[:3])
    else:
        print("  None")

    print("\nFinal answer:\n")
    print(state.get("final_answer"))


if __name__ == "__main__":
    main()

