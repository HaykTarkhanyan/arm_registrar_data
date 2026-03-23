"""
Preprocessing script for Armenian Registrar Data
- Renames Armenian columns to English
- Calculates age from birth date (also recomputed at runtime by data.py)
- Standardizes text formatting (title case for regions, communities)
- Saves cleaned data to parquet
"""

import pandas as pd


# Column mapping: Armenian -> English
COLUMN_MAPPING = {
    'azganun': 'surname',
    'anun': 'name',
    'haeranun': 'patronymic',
    'or_amis_tari': 'birth_date',
    'marz': 'region',
    'hamaenq': 'community',
    'bnakavaer': 'residence',
    'hasce': 'address',
    'taracq': 'precinct',
    'texamas': 'polling_station'
}


def preprocess_data(input_path: str = "elections.parquet",
                    output_path: str = "elections_cleaned.parquet") -> pd.DataFrame:
    """
    Preprocess the election data:
    1. Rename columns to English
    2. Calculate age (snapshot; recomputed at runtime by data.py for freshness)
    3. Standardize text formatting
    4. Save cleaned data
    """
    print("Loading data...")
    df = pd.read_parquet(input_path)
    print(f"Loaded {len(df):,} records")

    # 1. Rename columns to English
    print("\nRenaming columns...")
    df = df.rename(columns=COLUMN_MAPPING)
    print(f"Columns: {list(df.columns)}")

    # 2. Calculate age using shared logic (also recomputed at runtime by data.py)
    print("\nCalculating ages...")
    from data import compute_age
    df['age'] = compute_age(df['birth_date'])

    print(f"Age range: {df['age'].min()} - {df['age'].max()}")
    print(f"Mean age: {df['age'].mean():.1f}")

    # 3. Standardize text - convert UPPERCASE fields to Title Case
    print("\nStandardizing text formatting...")

    df['region'] = df['region'].str.title()
    print(f"Sample regions: {df['region'].unique()[:5].tolist()}")

    df['community'] = df['community'].str.title()
    print(f"Sample communities: {df['community'].unique()[:5].tolist()}")

    # 4. Reorder columns for better readability
    column_order = [
        'surname', 'name', 'patronymic', 'birth_date', 'age',
        'region', 'community', 'residence', 'address',
        'precinct', 'polling_station'
    ]
    df = df[column_order]

    # 5. Save cleaned data
    print(f"\nSaving cleaned data to {output_path}...")
    df.to_parquet(output_path, index=False)
    print("Done!")

    # Print sample
    print("\n" + "=" * 60)
    print("Sample of cleaned data:")
    print("=" * 60)
    print(df.head(5).to_string())

    return df


if __name__ == "__main__":
    df = preprocess_data()
    print(f"\nPreprocessing complete. Cleaned data has {len(df):,} records.")
