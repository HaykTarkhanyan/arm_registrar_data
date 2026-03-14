"""
Unified filtering logic with configurable match mode.
"""

import pandas as pd
from typing import Optional


def filter_data(
    df: pd.DataFrame,
    surname: Optional[str] = None,
    name: Optional[str] = None,
    patronymic: Optional[str] = None,
    age_min: Optional[int] = None,
    age_max: Optional[int] = None,
    region: Optional[str] = None,
    community: Optional[str] = None,
    residence: Optional[str] = None,
    address: Optional[str] = None,
    precinct: Optional[int] = None,
    polling_station: Optional[str] = None,
    match_mode: str = "exact",
) -> pd.DataFrame:
    """
    Filter the dataframe based on provided criteria.

    Parameters
    ----------
    match_mode : str
        "exact" for case-insensitive exact matching,
        "partial" for case-insensitive substring matching.
    """
    result = df.copy()

    text_fields = {
        'surname': surname,
        'name': name,
        'patronymic': patronymic,
        'region': region,
        'community': community,
        'residence': residence,
        'address': address,
        'polling_station': polling_station,
    }

    for col, value in text_fields.items():
        if value:
            value = value.strip()
            if match_mode == "partial":
                result = result[
                    result[col].str.contains(value, case=False, na=False, regex=False)
                ]
            else:
                result = result[result[col].str.lower() == value.lower()]

    if precinct is not None:
        result = result[result['precinct'] == precinct]

    if age_min is not None:
        result = result[result['age'] >= age_min]

    if age_max is not None:
        result = result[result['age'] <= age_max]

    return result
