"""
Armenian Registrar Data Filter App - CLI interface.
Uses partial (substring) matching by default.
"""

from data import load_data
from filters import filter_data


def interactive_search():
    """Interactive command-line search interface."""
    print("=" * 60)
    print("Armenian Registrar Data Search")
    print("=" * 60)
    print("\nLoading data...")

    try:
        df = load_data()
        print(f"Loaded {len(df):,} records.\n")
    except FileNotFoundError:
        print("Error: elections_cleaned.parquet not found!")
        print("Run preprocess.py first to create the cleaned data file.")
        return

    print("Enter search criteria (press Enter to skip a field):\n")

    surname = input("Surname: ").strip() or None
    name = input("Name: ").strip() or None
    patronymic = input("Patronymic: ").strip() or None

    age_min_str = input("Minimum age: ").strip()
    age_min = int(age_min_str) if age_min_str else None

    age_max_str = input("Maximum age: ").strip()
    age_max = int(age_max_str) if age_max_str else None

    region = input("Region: ").strip() or None
    community = input("Community: ").strip() or None
    residence = input("Residence: ").strip() or None
    address = input("Address: ").strip() or None

    precinct_str = input("Precinct number: ").strip()
    precinct = int(precinct_str) if precinct_str else None

    polling_station = input("Polling station: ").strip() or None

    print("\nSearching...")
    results = filter_data(
        df,
        surname=surname,
        name=name,
        patronymic=patronymic,
        age_min=age_min,
        age_max=age_max,
        region=region,
        community=community,
        residence=residence,
        address=address,
        precinct=precinct,
        polling_station=polling_station,
        match_mode="partial",
    )

    print(f"\nFound {len(results):,} matching records.\n")

    if len(results) > 0:
        if len(results) <= 20:
            print(results.to_string(index=False))
        else:
            print("First 20 results:")
            print(results.head(20).to_string(index=False))
            print(f"\n... and {len(results) - 20:,} more records.")

    return results


def main():
    """Main entry point."""
    while True:
        results = interactive_search()
        print("\n" + "-" * 60)
        choice = input("\nSearch again? (y/n): ").strip().lower()
        if choice != 'y':
            break
        print()
    print("\nGoodbye!")


if __name__ == "__main__":
    main()
