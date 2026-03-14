"""
Shared utility functions: zodiac signs, generations, birthday helpers,
name rarity, Armenian validation, and geographic coordinate mapping.
"""

from datetime import date
import re
import pandas as pd


# Armenian character validation pattern
ARMENIAN_PATTERN = re.compile(r'^[\u0531-\u0556\u0561-\u0587\s\-]+$')

ZODIAC_BOUNDARIES = [
    (1, 20, "Capricorn", "\u2651"),
    (2, 19, "Aquarius", "\u2652"),
    (3, 20, "Pisces", "\u2653"),
    (4, 20, "Aries", "\u2648"),
    (5, 21, "Taurus", "\u2649"),
    (6, 21, "Gemini", "\u264A"),
    (7, 22, "Cancer", "\u264B"),
    (8, 23, "Leo", "\u264C"),
    (9, 23, "Virgo", "\u264D"),
    (10, 23, "Libra", "\u264E"),
    (11, 22, "Scorpio", "\u264F"),
    (12, 22, "Sagittarius", "\u2650"),
    (12, 31, "Capricorn", "\u2651"),
]

GENERATION_RANGES = [
    (1928, 1945, "Silent Generation"),
    (1946, 1964, "Baby Boomers"),
    (1965, 1980, "Generation X"),
    (1981, 1996, "Millennials"),
    (1997, 2012, "Generation Z"),
    (2013, 2030, "Generation Alpha"),
]

# Approximate center coordinates for Armenian marzes
MARZ_COORDS = {
    'yerevan':     (40.1872, 44.5152),
    'aragatsotn':  (40.5303, 44.2137),
    'ararat':      (39.8303, 44.3650),
    'armavir':     (40.1533, 44.0378),
    'gegharkunik': (40.3499, 45.1260),
    'kotayk':      (40.3172, 44.6346),
    'lori':        (40.9984, 44.4935),
    'shirak':      (40.7951, 43.8472),
    'syunik':      (39.3376, 46.2350),
    'tavush':      (40.9912, 45.1678),
    'vayots_dzor': (39.7591, 45.3322),
}


def is_valid_armenian(text: str) -> bool:
    """Validate that text contains only Armenian characters, spaces, and hyphens."""
    if not text:
        return True
    return bool(ARMENIAN_PATTERN.match(text.strip()))


def get_zodiac_sign(birth_date: str) -> tuple:
    """Get (sign_name, symbol) from a DD/MM/YYYY birth date string."""
    try:
        day, month = int(birth_date[:2]), int(birth_date[3:5])
        for m, d, sign, symbol in ZODIAC_BOUNDARIES:
            if month < m or (month == m and day <= d):
                return sign, symbol
    except (ValueError, IndexError):
        pass
    return "Unknown", "?"


def get_zodiac_from_md(month, day) -> tuple:
    """Get (sign_name, symbol) from numeric month and day."""
    if pd.isna(month) or pd.isna(day):
        return "Unknown", "?"
    month, day = int(month), int(day)
    for m, d, sign, symbol in ZODIAC_BOUNDARIES:
        if month < m or (month == m and day <= d):
            return sign, symbol
    return "Unknown", "?"


def get_generation(birth_year) -> str:
    """Determine generation label from birth year."""
    if pd.isna(birth_year):
        return "Unknown"
    birth_year = int(birth_year)
    for start, end, name in GENERATION_RANGES:
        if start <= birth_year <= end:
            return name
    return "Unknown"


def calculate_days_until_birthday(birth_date: str) -> tuple:
    """Return (days_until_birthday, is_today) from a DD/MM/YYYY string."""
    try:
        day, month = int(birth_date[:2]), int(birth_date[3:5])
        today = date.today()
        this_year = date(today.year, month, day)
        if this_year < today:
            next_bday = date(today.year + 1, month, day)
        elif this_year == today:
            return 0, True
        else:
            next_bday = this_year
        return (next_bday - today).days, False
    except (ValueError, IndexError):
        return -1, False


def calculate_rarity_percentile(name: str, counts_series: pd.Series) -> float:
    """Higher percentile = rarer name."""
    if name not in counts_series.index:
        return 100.0
    count = counts_series[name]
    return (counts_series >= count).sum() / len(counts_series) * 100


def match_region_to_marz(region_name: str):
    """
    Match an Armenian region name to its marz key by inspecting the first
    characters (Armenian Unicode code points).

    Returns (marz_key, lat, lon) or None if no match.
    """
    if not region_name or len(region_name) < 1:
        return None

    first = region_name[0]

    # Single-character disambiguation
    single_map = {
        '\u0535': 'yerevan',      # \u0535 -> Yerevan
        '\u0533': 'gegharkunik',  # \u0533 -> Gegharkunik
        '\u053F': 'kotayk',       # \u053F -> Kotayk
        '\u053C': 'lori',         # \u053C -> Lori
        '\u0547': 'shirak',       # \u0547 -> Shirak
        '\u054D': 'syunik',       # \u054D -> Syunik
        '\u054F': 'tavush',       # \u054F -> Tavush
        '\u054E': 'vayots_dzor',  # \u054E -> Vayots Dzor
    }

    if first in single_map:
        key = single_map[first]
        lat, lon = MARZ_COORDS[key]
        return key, lat, lon

    # \u0531 is shared by Aragatsotn, Ararat, Armavir
    if first == '\u0531' and len(region_name) >= 4:
        c3 = region_name[2] if len(region_name) > 2 else ''
        c4 = region_name[3] if len(region_name) > 3 else ''
        if c3 == '\u0561' and c4 == '\u0563':
            key = 'aragatsotn'
        elif c3 == '\u0561' and c4 == '\u0580':
            key = 'ararat'
        elif c3 == '\u0574':
            key = 'armavir'
        else:
            return None
        lat, lon = MARZ_COORDS[key]
        return key, lat, lon

    return None
