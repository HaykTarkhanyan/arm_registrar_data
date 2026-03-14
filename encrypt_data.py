"""
Encrypt data files for safe public deployment.

Usage:
    python encrypt_data.py          # Encrypt files, print key
    python encrypt_data.py --gen    # Just generate a new key

Store the printed key in Streamlit secrets as DATA_KEY.
"""

import sys
from pathlib import Path
from cryptography.fernet import Fernet

FILES_TO_ENCRYPT = [
    "elections_cleaned.parquet",
    "eda_cache.pkl",
]


def generate_key() -> bytes:
    return Fernet.generate_key()


def encrypt_file(path: Path, fernet: Fernet) -> Path:
    data = path.read_bytes()
    encrypted = fernet.encrypt(data)
    out_path = path.with_suffix(path.suffix + ".enc")
    out_path.write_bytes(encrypted)
    size_mb = len(data) / 1024 / 1024
    print(f"  {path.name} ({size_mb:.1f} MB) -> {out_path.name}")
    return out_path


def main():
    if "--gen" in sys.argv:
        print(Fernet.generate_key().decode())
        return

    key = generate_key()

    print(f"\nEncryption key (save this in Streamlit secrets as DATA_KEY):\n")
    print(f"  {key.decode()}\n")

    fernet = Fernet(key)

    print("Encrypting files:")
    for filename in FILES_TO_ENCRYPT:
        path = Path(filename)
        if not path.exists():
            print(f"  SKIP {filename} (not found)")
            continue
        encrypt_file(path, fernet)

    print(f"\nDone! Add the .enc files to git and set the secret:")
    print(f'  [secrets]')
    print(f'  DATA_KEY = "{key.decode()}"')


if __name__ == "__main__":
    main()
