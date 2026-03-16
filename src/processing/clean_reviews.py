from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List

import pandas as pd

from src.ingestion.load_reviews import load_reviews_df


logger = logging.getLogger(__name__)


RAW_REVIEWS_PATH = Path("data/raw/Books_rating.csv")
PROCESSED_REVIEWS_PATH = Path("data/processed/reviews_clean.parquet")


COLUMN_RENAME_MAP: dict[str, str] = {
    "Id": "book_id_raw",
    "Title": "title",
    "Price": "price",
    "User_id": "user_id",
    "profileName": "profile_name",
    "score": "score",
    "time": "review_time_unix",
    "summary": "review_summary",
    "text": "review_text",
}


def _configure_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


def _ensure_processed_dir() -> None:
    PROCESSED_REVIEWS_PATH.parent.mkdir(parents=True, exist_ok=True)


def _clean_string_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    for col in columns:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype("string")
                .str.strip()
                .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
            )
    return df


def summarize_reviews_df(df: pd.DataFrame) -> None:
    logger.info("Clean reviews dataframe shape: %s", df.shape)
    logger.info("Clean reviews dataframe columns: %s", list(df.columns))
    logger.info("Clean reviews dataframe dtypes:\n%s", df.dtypes)

    null_counts = df.isna().sum()
    null_percent = (null_counts / len(df) * 100).round(2)
    null_summary = pd.DataFrame(
        {"null_count": null_counts, "null_percent": null_percent}
    )
    logger.info("Clean reviews dataframe null summary:\n%s", null_summary)


def clean_reviews_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()

    df.rename(columns=COLUMN_RENAME_MAP, inplace=True)

    text_like_cols: List[str] = [
        "title",
        "profile_name",
        "review_summary",
        "review_text",
    ]
    df = _clean_string_columns(df, text_like_cols)

    if "score" in df.columns:
        df["score"] = pd.to_numeric(df["score"], errors="coerce").astype("float64")

    if "review_time_unix" in df.columns:
        df["review_time"] = pd.to_datetime(
            df["review_time_unix"], unit="s", errors="coerce", utc=True
        )

    return df


def process_reviews() -> Path:
    _configure_logging()
    logger.info("Starting reviews cleaning pipeline.")

    raw_df = load_reviews_df(RAW_REVIEWS_PATH)
    clean_df = clean_reviews_dataframe(raw_df)

    _ensure_processed_dir()
    logger.info("Saving cleaned reviews dataframe to '%s'", PROCESSED_REVIEWS_PATH)
    clean_df.to_parquet(PROCESSED_REVIEWS_PATH, index=False)

    summarize_reviews_df(clean_df)
    logger.info("Reviews cleaning pipeline completed.")
    return PROCESSED_REVIEWS_PATH


def main() -> None:
    process_reviews()


if __name__ == "__main__":
    main()

