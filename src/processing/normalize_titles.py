from __future__ import annotations

import re
from typing import Optional

import pandas as pd


_MULTI_SPACE_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)


def normalize_title(text: Optional[str]) -> Optional[str]:
    """
    Normalize a title for matching:
    - lowercase
    - trim
    - collapse multiple spaces
    - remove simple punctuation (keep letters/digits/underscore and spaces)
    """
    if text is None:
        return None

    text = text.strip()
    if not text:
        return None

    text = text.lower()
    text = _PUNCT_RE.sub(" ", text)
    text = _MULTI_SPACE_RE.sub(" ", text)
    text = text.strip()

    return text or None


def normalize_title_series(series: pd.Series) -> pd.Series:
    return series.astype("string").map(normalize_title)


