"""
Pre-compute EDA statistics and save to disk.
Run this after preprocessing to generate eda_cache.pkl.
"""

import pickle
import pandas as pd
from data import load_data
from utils import get_generation, get_zodiac_from_md, match_region_to_marz

CACHE_PATH = "eda_cache.pkl"


def precompute():
    print("Loading data...")
    df = load_data()
    print(f"Loaded {len(df):,} records")

    # Parse birth dates
    parsed = pd.to_datetime(df['birth_date'], format='%d/%m/%Y', errors='coerce')
    birth_year = parsed.dt.year
    birth_month = parsed.dt.month
    birth_day = parsed.dt.day
    birth_decade = (birth_year // 10) * 10

    stats = {}

    # === Overview ===
    stats['total_records'] = len(df)
    stats['unique_names'] = df['name'].nunique()
    stats['unique_surnames'] = df['surname'].nunique()
    stats['unique_communities'] = df['community'].nunique()
    stats['unique_regions'] = df['region'].nunique()
    stats['avg_age'] = float(df['age'].mean())
    stats['median_age'] = float(df['age'].median())
    stats['min_age'] = int(df['age'].min())
    stats['max_age'] = int(df['age'].max())

    # === Demographics ===
    print("Computing demographics...")
    age_bins = [0, 18, 25, 35, 45, 55, 65, 75, 85, 150]
    age_labels = ['0-17', '18-24', '25-34', '35-44', '45-54', '55-64', '65-74', '75-84', '85+']
    stats['age_distribution'] = pd.cut(df['age'], bins=age_bins, labels=age_labels).value_counts().sort_index()
    stats['generation_counts'] = birth_year.apply(get_generation).value_counts()
    stats['voting_age'] = int((df['age'] >= 18).sum())
    stats['youth'] = int((df['age'] < 30).sum())
    stats['seniors'] = int((df['age'] >= 65).sum())

    # === Names ===
    print("Computing name statistics...")
    stats['name_counts'] = df['name'].value_counts()
    stats['surname_counts'] = df['surname'].value_counts()
    stats['patronymic_counts'] = df['patronymic'].value_counts()
    stats['name_endings'] = df['name'].str[-2:].value_counts().head(20)
    stats['surname_endings'] = df['surname'].str[-3:].value_counts().head(20)
    stats['common_full_names'] = (df['name'] + ' ' + df['surname']).value_counts().head(20)

    df_temp = df.assign(birth_decade=birth_decade)
    stats['names_by_decade'] = df_temp.groupby('birth_decade')['name'].apply(
        lambda x: x.value_counts().head(5)
    )

    # Name and surname length by year
    print("Computing name length by year...")
    name_lengths = df['name'].str.len()
    surname_lengths = df['surname'].str.len()
    len_df = pd.DataFrame({
        'birth_year': birth_year,
        'name_length': name_lengths,
        'surname_length': surname_lengths,
    }).dropna(subset=['birth_year'])
    len_df['birth_year'] = len_df['birth_year'].astype(int)
    year_counts = len_df['birth_year'].value_counts()
    valid_years = year_counts[year_counts >= 10].index
    len_df = len_df[len_df['birth_year'].isin(valid_years)]
    stats['name_length_by_year'] = len_df.groupby('birth_year')['name_length'].agg(['mean', 'median'])
    stats['surname_length_by_year'] = len_df.groupby('birth_year')['surname_length'].agg(['mean', 'median'])

    # === Geographic ===
    print("Computing geographic statistics...")
    stats['region_counts'] = df['region'].value_counts()
    stats['community_counts'] = df['community'].value_counts()
    stats['regional_avg_age'] = df.groupby('region')['age'].mean().sort_values(ascending=False)
    stats['name_diversity_by_region'] = df.groupby('region')['name'].nunique()

    # Map data
    region_counts = df['region'].value_counts()
    map_rows = []
    for region, count in region_counts.items():
        match = match_region_to_marz(str(region))
        if match:
            key, lat, lon = match
            avg_age = df[df['region'] == region]['age'].mean()
            map_rows.append({
                'region': region, 'marz': key,
                'lat': lat, 'lon': lon,
                'population': count, 'avg_age': round(avg_age, 1),
            })
    stats['map_data'] = pd.DataFrame(map_rows) if map_rows else pd.DataFrame()

    # === Temporal ===
    print("Computing temporal statistics...")
    byc = birth_year.value_counts().sort_index()
    stats['birth_year_counts'] = byc
    stats['birth_month_counts'] = birth_month.value_counts().sort_index()
    stats['birth_day_counts'] = birth_day.value_counts().sort_index()
    stats['peak_birth_year'] = byc.idxmax()
    stats['peak_birth_count'] = int(byc.max())

    # Pre-compute Jan 1st excluded version
    no_jan1 = ~((birth_month == 1) & (birth_day == 1))
    stats['birth_year_counts_no_jan1'] = birth_year[no_jan1].value_counts().sort_index()
    stats['birth_month_counts_no_jan1'] = birth_month[no_jan1].value_counts().sort_index()
    stats['birth_day_counts_no_jan1'] = birth_day[no_jan1].value_counts().sort_index()
    stats['jan1_excluded_count'] = int((~no_jan1).sum())

    # === Birthdays ===
    print("Computing birthday statistics...")
    # Full date counts (MM-DD) for heatmap / daily distribution
    valid_dates = pd.DataFrame({
        'month': birth_month, 'day': birth_day,
    }).dropna()
    valid_dates['month'] = valid_dates['month'].astype(int)
    valid_dates['day'] = valid_dates['day'].astype(int)
    # Day-of-year (1-366)
    valid_dates['day_of_year'] = pd.to_datetime(
        '2000-' + valid_dates['month'].astype(str) + '-' + valid_dates['day'].astype(str),
        format='%Y-%m-%d', errors='coerce',
    ).dt.dayofyear
    stats['birthday_doy_counts'] = valid_dates['day_of_year'].dropna().astype(int).value_counts().sort_index()

    # Per month-day counts for heatmap
    valid_dates['mm_dd'] = valid_dates['month'].astype(str).str.zfill(2) + '-' + valid_dates['day'].astype(str).str.zfill(2)
    stats['birthday_mmdd_counts'] = valid_dates['mm_dd'].value_counts().sort_index()

    # Weekday of birth (approximate — using year 2000 as proxy since we don't know actual year for this stat)
    # Instead use actual birth dates
    full_parsed = pd.to_datetime(df['birth_date'], format='%d/%m/%Y', errors='coerce')
    stats['birth_weekday_counts'] = full_parsed.dt.day_name().value_counts()

    # Conception month estimate (birth month - 9, wrapped)
    conception_month = ((valid_dates['month'] - 9 - 1) % 12) + 1
    stats['conception_month_counts'] = conception_month.value_counts().sort_index()

    # Births per day-of-week by decade (for trends)
    df_wd = pd.DataFrame({
        'weekday': full_parsed.dt.day_name(),
        'decade': (full_parsed.dt.year // 10 * 10),
    }).dropna()
    stats['weekday_by_decade'] = df_wd.groupby('decade')['weekday'].value_counts().unstack(fill_value=0)

    # Most and least common birthdays
    mmdd = stats['birthday_mmdd_counts']
    stats['most_common_birthday'] = mmdd.idxmax()
    stats['most_common_birthday_count'] = int(mmdd.max())
    # Exclude Feb 29 for least common (it's inherently rare)
    mmdd_no_leap = mmdd[mmdd.index != '02-29']
    stats['least_common_birthday'] = mmdd_no_leap.idxmin()
    stats['least_common_birthday_count'] = int(mmdd_no_leap.min())

    # === Fun ===
    print("Computing fun statistics...")
    zodiac_df = pd.DataFrame({'month': birth_month, 'day': birth_day})
    zodiac_series = zodiac_df.apply(
        lambda row: get_zodiac_from_md(row['month'], row['day'])[0], axis=1
    )
    stats['zodiac_counts'] = zodiac_series[zodiac_series != 'Unknown'].value_counts()
    stats['jan1_births'] = int(df['birth_date'].str.startswith('01/01/').sum())
    stats['jan1_pct'] = stats['jan1_births'] / len(df) * 100

    # === Household ===
    print("Computing household statistics...")
    address_counts = df.groupby(['address', 'community', 'region']).size()
    stats['avg_household_size'] = float(address_counts.mean())
    stats['max_household_size'] = int(address_counts.max())
    stats['household_size_dist'] = address_counts.value_counts().sort_index().head(20)

    unique_families = df.groupby(['surname', 'patronymic']).size()
    stats['unique_families'] = len(unique_families)
    stats['avg_family_size'] = len(df) / len(unique_families)
    stats['family_size_dist'] = unique_families.value_counts().sort_index().head(15)

    # === Data Quality ===
    print("Computing data quality statistics...")
    total = len(df)
    quality_rows = []
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        empty_count = int((df[col] == '').sum()) if df[col].dtype == 'object' else 0
        missing = null_count + empty_count
        quality_rows.append({
            'Column': col, 'Null': null_count, 'Empty String': empty_count,
            'Total Missing': missing,
            'Completeness %': round((total - missing) / total * 100, 2),
        })
    stats['missing_data'] = pd.DataFrame(quality_rows)

    # Age anomalies
    stats['age_outliers'] = int(((df['age'] < 0) | (df['age'] > 120)).sum())

    # === Records & Superlatives ===
    print("Computing records & superlatives...")

    # Longest / shortest names
    df['_name_len'] = df['name'].str.len()
    df['_surname_len'] = df['surname'].str.len()
    df['_full_len'] = df['_name_len'] + df['_surname_len']

    longest_name_idx = df['_name_len'].idxmax()
    shortest_name_idx = df.loc[df['_name_len'] > 0, '_name_len'].idxmin()
    longest_surname_idx = df['_surname_len'].idxmax()
    shortest_surname_idx = df.loc[df['_surname_len'] > 0, '_surname_len'].idxmin()
    longest_full_idx = df['_full_len'].idxmax()

    def person_summary(row):
        return {
            'name': row['name'],
            'surname': row['surname'],
            'patronymic': row['patronymic'],
            'age': int(row['age']),
            'region': row['region'],
            'birth_date': row['birth_date'],
        }

    stats['longest_name'] = person_summary(df.loc[longest_name_idx])
    stats['longest_name']['length'] = int(df.loc[longest_name_idx, '_name_len'])
    stats['shortest_name'] = person_summary(df.loc[shortest_name_idx])
    stats['shortest_name']['length'] = int(df.loc[shortest_name_idx, '_name_len'])
    stats['longest_surname'] = person_summary(df.loc[longest_surname_idx])
    stats['longest_surname']['length'] = int(df.loc[longest_surname_idx, '_surname_len'])
    stats['shortest_surname'] = person_summary(df.loc[shortest_surname_idx])
    stats['shortest_surname']['length'] = int(df.loc[shortest_surname_idx, '_surname_len'])
    stats['longest_full_name'] = person_summary(df.loc[longest_full_idx])
    stats['longest_full_name']['length'] = int(df.loc[longest_full_idx, '_full_len'])

    # Oldest / youngest
    oldest_idx = df['age'].idxmax()
    youngest_idx = df['age'].idxmin()
    stats['oldest_person'] = person_summary(df.loc[oldest_idx])
    stats['youngest_person'] = person_summary(df.loc[youngest_idx])

    # Largest household
    largest_hh_key = address_counts.idxmax()
    largest_hh_size = int(address_counts.max())
    largest_hh_members = df[
        (df['address'] == largest_hh_key[0])
        & (df['community'] == largest_hh_key[1])
        & (df['region'] == largest_hh_key[2])
    ][['name', 'surname', 'patronymic', 'age', 'birth_date']].sort_values('age', ascending=False)
    stats['largest_household'] = {
        'address': largest_hh_key[0],
        'community': largest_hh_key[1],
        'region': largest_hh_key[2],
        'size': largest_hh_size,
        'members': largest_hh_members,
    }

    # Most common name + surname combination
    stats['most_common_full_name_count'] = int(stats['common_full_names'].iloc[0])
    stats['most_common_full_name_value'] = stats['common_full_names'].index[0]

    # Rarest name / surname (appearing only once)
    stats['unique_names_count'] = int((stats['name_counts'] == 1).sum())
    stats['unique_surnames_count'] = int((stats['surname_counts'] == 1).sum())

    # Most popular name (already computed, just reference)
    stats['most_popular_name'] = stats['name_counts'].index[0]
    stats['most_popular_name_count'] = int(stats['name_counts'].iloc[0])
    stats['most_popular_surname'] = stats['surname_counts'].index[0]
    stats['most_popular_surname_count'] = int(stats['surname_counts'].iloc[0])

    # Region with most / fewest people
    stats['largest_region'] = stats['region_counts'].index[0]
    stats['largest_region_count'] = int(stats['region_counts'].iloc[0])
    stats['smallest_region'] = stats['region_counts'].index[-1]
    stats['smallest_region_count'] = int(stats['region_counts'].iloc[-1])

    # Largest family (surname + patronymic combo)
    largest_family_key = unique_families.idxmax()
    stats['largest_family'] = {
        'surname': largest_family_key[0],
        'patronymic': largest_family_key[1],
        'size': int(unique_families.max()),
    }

    df.drop(columns=['_name_len', '_surname_len', '_full_len'], inplace=True)

    # Save
    print(f"\nSaving cache to {CACHE_PATH}...")
    with open(CACHE_PATH, 'wb') as f:
        pickle.dump(stats, f, protocol=pickle.HIGHEST_PROTOCOL)

    print("Done!")
    return stats


if __name__ == "__main__":
    precompute()
