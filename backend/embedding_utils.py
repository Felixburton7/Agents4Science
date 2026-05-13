from __future__ import annotations

import hashlib
import math
from typing import Optional

from backend.llm_client import _ensure_openai_api_key
from backend.tools.api_cache import get_api_cache

_EMBEDDING_MODEL = "text-embedding-3-small"


def embed_texts(texts: list[str]) -> Optional[list[list[float]]]:
    """Batch-embed texts via OpenAI. Each vector is cached in SQLite by SHA-256.

    Sends at most one API request (all uncached texts in one batch).
    Returns None when the API key is absent or the call fails.
    """
    if not texts:
        return []

    if not _ensure_openai_api_key():
        return None

    cache = get_api_cache()
    result: list[Optional[list[float]]] = [None] * len(texts)
    uncached_positions: list[int] = []
    uncached_texts: list[str] = []

    for i, text in enumerate(texts):
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        cached = cache.get(
            "openai_embeddings",
            "embeddings",
            {"model": _EMBEDDING_MODEL, "input_hash": text_hash},
        )
        if cached is not None:
            result[i] = cached["vector"]
        else:
            uncached_positions.append(i)
            uncached_texts.append(text)

    if uncached_texts:
        try:
            from openai import OpenAI  # lazy — openai is optional at import time

            client = OpenAI()
            response = client.embeddings.create(model=_EMBEDDING_MODEL, input=uncached_texts)
            for j, embedding_data in enumerate(response.data):
                vector = embedding_data.embedding
                original_index = uncached_positions[j]
                result[original_index] = vector
                text_hash = hashlib.sha256(uncached_texts[j].encode("utf-8")).hexdigest()
                cache.set(
                    "openai_embeddings",
                    "embeddings",
                    {"model": _EMBEDDING_MODEL, "input_hash": text_hash},
                    {"vector": vector},
                )
        except Exception:
            return None

    if any(v is None for v in result):
        return None
    return result  # type: ignore[return-value]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def embedding_relevance(query: str, title: str, abstract: str = "") -> Optional[float]:
    """Return cosine similarity between query and (0.6·title + 0.4·abstract).

    Relies on embed_texts caching, so repeated calls for the same texts are free.
    Returns None when embeddings are unavailable.
    """
    texts = [query, title]
    has_abstract = bool(abstract.strip())
    if has_abstract:
        texts.append(abstract)

    vectors = embed_texts(texts)
    if vectors is None:
        return None

    query_vec = vectors[0]
    title_vec = vectors[1]

    if has_abstract:
        abstract_vec = vectors[2]
        paper_vec = [0.6 * t + 0.4 * a for t, a in zip(title_vec, abstract_vec)]
    else:
        paper_vec = title_vec

    return cosine_similarity(query_vec, paper_vec)
