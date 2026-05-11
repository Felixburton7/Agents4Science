from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

import requests

from backend.config import CACHE_DB_PATH


class SQLiteAPICache:
    def __init__(self, path: str = CACHE_DB_PATH) -> None:
        self.path = Path(path)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_cache (
                    cache_key TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    params_json TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_api_cache_provider
                ON api_cache(provider, created_at)
                """
            )

    @staticmethod
    def make_key(provider: str, endpoint: str, params: dict[str, Any]) -> str:
        payload = {
            "provider": provider,
            "endpoint": endpoint,
            "params": params,
        }
        canonical = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def get(self, provider: str, endpoint: str, params: dict[str, Any]) -> Optional[dict[str, Any]]:
        params_json = json.dumps(params, sort_keys=True, default=str)
        cache_key = self.make_key(provider, endpoint, params)
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT response_json
                FROM api_cache
                WHERE cache_key = ? AND params_json = ?
                """,
                (cache_key, params_json),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def set(self, provider: str, endpoint: str, params: dict[str, Any], response: dict[str, Any]) -> None:
        params_json = json.dumps(params, sort_keys=True, default=str)
        response_json = json.dumps(response)
        cache_key = self.make_key(provider, endpoint, params)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO api_cache (
                    cache_key, provider, endpoint, params_json, response_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (cache_key, provider, endpoint, params_json, response_json, time.time()),
            )


_CACHE: SQLiteAPICache | None = None


def get_api_cache() -> SQLiteAPICache:
    global _CACHE
    if _CACHE is None:
        _CACHE = SQLiteAPICache()
    return _CACHE


def cached_get_json(
    provider: str,
    endpoint: str,
    params: dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 20,
) -> tuple[dict[str, Any], bool]:
    cache = get_api_cache()
    cached = cache.get(provider, endpoint, params)
    if cached is not None:
        return cached, True

    response = requests.get(endpoint, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    cache.set(provider, endpoint, params, data)
    return data, False
