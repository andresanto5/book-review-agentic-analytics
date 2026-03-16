from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List

import numpy as np
import pandas as pd

from src.ingestion.load_books import load_books_df
from src.processing.normalize_dates import parse_published_date_series
from src.processing.parse_authors import parse_authors_column
from src.processing.parse_categories import parse_categories_column


logger = logging.getLogger(__name__)


RAW_BOOKS_PATH = Path("data/raw/books_data.csv")
PROCESSED_BOOKS_PATH = Path("data/processed/books_clean.parquet")


COLUMN_RENAME_MAP: dict[str, str] = {
    "Title": "title",
    "description": "description",
    "authors": "authors",
    "image": "image_url",
    "previewLink": "preview_link",
    "publisher": "publisher",
    "publishedDate": "published_date_raw",
    "infoLink": "info_link",
    "categories": "categories",
    "ratingsCount": "ratings_count",
}


def _configure_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


def _ensure_processed_dir() -> None:
    PROCESSED_BOOKS_PATH.parent.mkdir(parents=True, exist_ok=True)


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


def summarize_books_df(df: pd.DataFrame) -> None:
    logger.info("Clean books dataframe shape: %s", df.shape)
    logger.info("Clean books dataframe columns: %s", list(df.columns))
    logger.info("Clean books dataframe dtypes:\n%s", df.dtypes)

    null_counts = df.isna().sum()
    null_percent = (null_counts / len(df) * 100).round(2)
    null_summary = pd.DataFrame(
        {"null_count": null_counts, "null_percent": null_percent}
    )
    logger.info("Clean books dataframe null summary:\n%s", null_summary)


def clean_books_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()

    df.rename(columns=COLUMN_RENAME_MAP, inplace=True)

    text_like_cols: List[str] = [
        "title",
        "description",
        "image_url",
        "preview_link",
        "publisher",
        "published_date_raw",
        "info_link",
    ]
    df = _clean_string_columns(df, text_like_cols)

    if "authors" in df.columns:
        df["authors"] = parse_authors_column(df, "authors")

    if "categories" in df.columns:
        df["categories"] = parse_categories_column(df, "categories")

    if "published_date_raw" in df.columns:
        parsed, year = parse_published_date_series(df["published_date_raw"])
        df["published_date_parsed"] = parsed
        df["published_year"] = year.astype("Int64")
    else:
        df["published_date_parsed"] = pd.NaT
        df["published_year"] = pd.Series(np.nan, index=df.index, dtype="Int64")

    return df


def process_books() -> Path:
    _configure_logging()
    logger.info("Starting books cleaning pipeline.")

    raw_df = load_books_df(RAW_BOOKS_PATH)
    clean_df = clean_books_dataframe(raw_df)

    _ensure_processed_dir()
    logger.info("Saving cleaned books dataframe to '%s'", PROCESSED_BOOKS_PATH)
    clean_df.to_parquet(PROCESSED_BOOKS_PATH, index=False)

    summarize_books_df(clean_df)
    logger.info("Books cleaning pipeline completed.")
    return PROCESSED_BOOKS_PATH


def main() -> None:
    process_books()


if __name__ == "__main__":
    main()

