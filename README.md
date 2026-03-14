# Armenian Registrar Data Analysis

Exploratory data analysis and search tool for Armenian voter registration records (~2.5M entries).

**Live app:** [armenians-data.streamlit.app](https://armenians-data.streamlit.app/)

## Features

- **Search** — Look up people by name, surname, patronymic, region, or community with exact/partial matching
- **EDA Dashboard** — Demographics, name trends, geographic maps, temporal patterns, birthday analysis, zodiac distribution, household stats, records & superlatives, data quality
- **Comparison Tool** — Compare two regions or two names side by side with interactive charts

## Setup

```bash
pip install -r requirements.txt
```

### Data Preparation

1. Place raw election data CSVs in the project directory
2. Run preprocessing:
   ```bash
   python preprocess.py
   ```
3. Pre-compute EDA statistics:
   ```bash
   python precompute_eda.py
   ```

### Running Locally

```bash
streamlit run streamlit_app.py
```

### Encryption (for public deployment)

Data files are encrypted with Fernet symmetric encryption so the repo can be public without exposing personal data.

```bash
python encrypt_data.py
```

This generates `.enc` files and prints a key. Store the key as `DATA_KEY` in:
- `.streamlit/secrets.toml` (local dev)
- `.env` (CLI scripts)
- Streamlit Cloud Secrets (deployed app)

The app automatically detects whether to load raw or encrypted data.

## Project Structure

```
streamlit_app.py        # Main search page
pages/
  1_📊_EDA.py           # EDA dashboard (reads pre-computed cache)
  2_🔄_Compare.py       # Region/name comparison tool
data.py                 # Shared data loading with runtime age computation
filters.py              # Unified filtering (exact/partial match)
utils.py                # Armenian text validation, zodiac, generation, map utils
preprocess.py           # Raw CSV → cleaned parquet
precompute_eda.py       # Parquet → eda_cache.pkl
encrypt_data.py         # Encrypt data files for public deployment
```

## Tech Stack

Streamlit, Pandas, Plotly, PyArrow, Cryptography
