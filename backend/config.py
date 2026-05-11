from __future__ import annotations

import os
from pathlib import Path


def _load_local_env() -> None:
    env_path = Path(".env")
    if not env_path.exists():
        return

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_local_env()

MAX_API_TIMEOUT = float(os.getenv("MAX_API_TIMEOUT", "20"))
SEMANTIC_SCHOLAR_KEY = os.getenv("SEMANTIC_SCHOLAR_KEY") or os.getenv("S2_API_KEY")
OPENALEX_EMAIL = os.getenv("OPENALEX_EMAIL", "")
CACHE_DB_PATH = os.getenv("LITERATURE_CACHE_DB", "literature_cache.sqlite3")
