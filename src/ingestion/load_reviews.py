import logging
from pathlib import Path
from typing import Iterable, List

import pandas as pd


logger = logging.getLogger(__name__)


EXPECTED_REVIEWS_COLUMNS: List[str] = [
    "User_id",
    "ISBN",
    "bookRating",
]


def _configure_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


def load_reviews_df(path: str | Path = "data/raw/Books_rating.csv") -> pd.DataFrame:
    _configure_logging()
    csv_path = Path(path)
    logger.info("Loading reviews data from '%s'", csv_path)

    if not csv_path.is_file():
        msg = f"Reviews CSV not found at {csv_path}"
        logger.error(msg)
        raise FileNotFoundError(msg)

    df = pd.read_csv(csv_path)
    logger.info("Loaded reviews dataframe with shape %s", df.shape)
    return df


def validate_reviews_columns(
    df: pd.DataFrame,
    expected_columns: Iterable[str] = EXPECTED_REVIEWS_COLUMNS,
) -> None:
    expected_set = set(expected_columns)
    actual_set = set(df.columns)

    missing = expected_set - actual_set
    extra = actual_set - expected_set

    if missing:
        logger.warning("Missing expected reviews columns: %s", sorted(missing))
    else:
        logger.info("All expected reviews columns are present.")

    if extra:
        logger.info("Additional reviews columns found: %s", sorted(extra))


def summarize_reviews_df(df: pd.DataFrame) -> None:
    logger.info("Reviews dataframe shape: %s", df.shape)
    logger.info("Reviews dataframe columns: %s", list(df.columns))
    logger.info("Reviews dataframe dtypes:\n%s", df.dtypes)

    null_counts = df.isna().sum()
    null_percent = (null_counts / len(df) * 100).round(2)
    null_summary = pd.DataFrame(
        {"null_count": null_counts, "null_percent": null_percent}
    )
    logger.info("Reviews dataframe null summary:\n%s", null_summary)

    logger.info("First 5 rows of reviews dataframe:\n%s", df.head())


def main() -> None:
    df = load_reviews_df()
    validate_reviews_columns(df)
    summarize_reviews_df(df)


if __name__ == "__main__":
    main()

