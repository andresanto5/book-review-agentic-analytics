import logging
from pathlib import Path
from typing import Iterable, List

import pandas as pd


logger = logging.getLogger(__name__)


EXPECTED_BOOKS_COLUMNS: List[str] = [
    "bookID",
    "title",
    "authors",
    "average_rating",
    "isbn",
    "isbn13",
    "language_code",
    "num_pages",
    "ratings_count",
    "text_reviews_count",
]


def _configure_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


def load_books_df(path: str | Path = "data/raw/books_data.csv") -> pd.DataFrame:
    _configure_logging()
    csv_path = Path(path)
    logger.info("Loading books data from '%s'", csv_path)

    if not csv_path.is_file():
        msg = f"Books CSV not found at {csv_path}"
        logger.error(msg)
        raise FileNotFoundError(msg)

    df = pd.read_csv(csv_path)
    logger.info("Loaded books dataframe with shape %s", df.shape)
    return df


def validate_books_columns(
    df: pd.DataFrame,
    expected_columns: Iterable[str] = EXPECTED_BOOKS_COLUMNS,
) -> None:
    expected_set = set(expected_columns)
    actual_set = set(df.columns)

    missing = expected_set - actual_set
    extra = actual_set - expected_set

    if missing:
        logger.warning("Missing expected book columns: %s", sorted(missing))
    else:
        logger.info("All expected book columns are present.")

    if extra:
        logger.info("Additional book columns found: %s", sorted(extra))


def summarize_books_df(df: pd.DataFrame) -> None:
    logger.info("Books dataframe shape: %s", df.shape)
    logger.info("Books dataframe columns: %s", list(df.columns))
    logger.info("Books dataframe dtypes:\n%s", df.dtypes)

    null_counts = df.isna().sum()
    null_percent = (null_counts / len(df) * 100).round(2)
    null_summary = pd.DataFrame(
        {"null_count": null_counts, "null_percent": null_percent}
    )
    logger.info("Books dataframe null summary:\n%s", null_summary)

    logger.info("First 5 rows of books dataframe:\n%s", df.head())


def main() -> None:
    df = load_books_df()
    validate_books_columns(df)
    summarize_books_df(df)


if __name__ == "__main__":
    main()

