import ast
from typing import List, Sequence

import pandas as pd


def parse_categories_cell(value: object) -> List[str] | None:
    if value is None:
        return None
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]

    text = str(value).strip()
    if not text:
        return None

    try:
        parsed = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return [text]

    if isinstance(parsed, Sequence) and not isinstance(parsed, (str, bytes)):
        cleaned = [str(v).strip() for v in parsed if str(v).strip()]
        return cleaned or None

    return [str(parsed).strip()] if str(parsed).strip() else None


def parse_categories_column(df: pd.DataFrame, column: str = "categories") -> pd.Series:
    if column not in df.columns:
        raise KeyError(f"Column '{column}' not found in dataframe.")
    return df[column].apply(parse_categories_cell)

