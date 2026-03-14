"""
Shared data loading with runtime age computation.
Supports encrypted (.enc) files for public deployment.
"""

import io
import os
from pathlib import Path

import pandas as pd

DATA_PATH = "elections_cleaned.parquet"
DATA_PATH_ENC = "elections_cleaned.parquet.enc"


def _get_key() -> bytes | None:
    """Get decryption key from Streamlit secrets, .env, or environment."""
    # 1. Streamlit secrets (deployed app)
    try:
        import streamlit as st
        return st.secrets["DATA_KEY"].encode()
    except Exception:
        pass
    # 2. Environment variable / .env file
    key = os.environ.get("DATA_KEY")
    if not key:
        env_path = Path(".env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("DATA_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    if key:
        return key.encode()
    return None


def _decrypt_bytes(encrypted_path: str, key: bytes) -> bytes:
    """Decrypt a Fernet-encrypted file and return raw bytes."""
    from cryptography.fernet import Fernet
    fernet = Fernet(key)
    return fernet.decrypt(Path(encrypted_path).read_bytes())


def compute_age(birth_date_series: pd.Series) -> pd.Series:
    """Compute age from birth_date strings (DD/MM/YYYY) using vectorized operations."""
    parsed = pd.to_datetime(birth_date_series, format='%d/%m/%Y', errors='coerce')
    today = pd.Timestamp.now()
    age = (today - parsed).dt.days // 365

    # Adjust for people who haven't had their birthday yet this year
    birth_md = parsed.dt.month * 100 + parsed.dt.day
    today_md = today.month * 100 + today.day
    age = age.where(birth_md <= today_md, age - 1)

    return age


def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    """Load parquet data and recompute ages at runtime.

    Tries unencrypted file first; falls back to encrypted version.
    """
    if Path(path).exists():
        df = pd.read_parquet(path)
    elif Path(DATA_PATH_ENC).exists():
        key = _get_key()
        if key is None:
            raise RuntimeError(
                "Encrypted data found but DATA_KEY secret is not set. "
                "Add it in .streamlit/secrets.toml or Streamlit Cloud settings."
            )
        raw = _decrypt_bytes(DATA_PATH_ENC, key)
        df = pd.read_parquet(io.BytesIO(raw))
    else:
        raise FileNotFoundError(
            f"Neither {path} nor {DATA_PATH_ENC} found."
        )

    df['age'] = compute_age(df['birth_date'])
    return df
