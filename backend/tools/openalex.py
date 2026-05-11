from __future__ import annotations

from typing import Any

from backend.config import MAX_API_TIMEOUT, OPENALEX_EMAIL
from backend.tools.api_cache import cached_get_json


WORKS_URL = "https://api.openalex.org/works"


def search_works(query: str, per_page: int = 50, **extra_params: Any) -> dict[str, Any]:
    params: dict[str, Any] = {
        "search": query,
        "per-page": per_page,
        **extra_params,
    }
    if OPENALEX_EMAIL:
        params["mailto"] = OPENALEX_EMAIL

    data, _from_cache = cached_get_json(
        "openalex",
        WORKS_URL,
        params,
        headers={"User-Agent": "MAgent4Science/0.1"},
        timeout=MAX_API_TIMEOUT,
    )
    return data
