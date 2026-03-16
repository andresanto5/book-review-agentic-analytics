from __future__ import annotations

from typing import Tuple

import pandas as pd


def parse_published_date_series(
    series: pd.Series,
) -> Tuple[pd.Series, pd.Series]:
    parsed = pd.to_datetime(series, errors="coerce", utc=True)
    year = parsed.dt.year
    return parsed, year

