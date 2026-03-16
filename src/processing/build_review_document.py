from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd


logger = logging.getLogger(__name__)


REVIEW_DOCUMENTS_PARQUET = Path("data/processed/review_documents.parquet")
REVIEW_DOCUMENTS_SAMPLE_CSV = Path("data/processed/review_documents_sample.csv")


def _configure_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


def _ensure_output_dirs() -> None:
    REVIEW_DOCUMENTS_PARQUET.parent.mkdir(parents=True, exist_ok=True)


def build_review_document_text(row: pd.Series) -> str:
    title = row.get("title") or ""
    authors = row.get("authors") or ""
    categories = row.get("categories") or ""
    score = row.get("score")
    score_str = "" if pd.isna(score) else str(score)
    summary = row.get("review_summary") or ""
    review = row.get("review_text") or ""

    parts = [
        f"Title: {title}",
        f"Authors: {authors}",
        f"Categories: {categories}",
        f"Score: {score_str}",
        f"Summary: {summary}",
        f"Review: {review}",
    ]
    return "\n".join(parts)


def add_review_document_column(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Building review_document text field for %d rows.", len(df))
    df = df.copy()
    df["review_document"] = df.apply(build_review_document_text, axis=1)
    avg_len = df["review_document"].str.len().mean() if not df.empty else 0.0
    logger.info("Average review_document length (chars): %.2f", avg_len)
    return df


def save_review_documents(df: pd.DataFrame) -> None:
    _ensure_output_dirs()
    logger.info(
        "Saving full review_documents dataframe to '%s'.",
        REVIEW_DOCUMENTS_PARQUET,
    )
    df.to_parquet(REVIEW_DOCUMENTS_PARQUET, index=False)

    sample_size = min(100, len(df))
    if sample_size > 0:
        sample_df = df.sample(n=sample_size, random_state=42)
    else:
        sample_df = df.copy()

    logger.info(
        "Saving sample (%d rows) of review_documents to '%s'.",
        len(sample_df),
        REVIEW_DOCUMENTS_SAMPLE_CSV,
    )
    sample_df.to_csv(REVIEW_DOCUMENTS_SAMPLE_CSV, index=False)


