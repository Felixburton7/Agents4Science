"""
Semantic Scholar Academic Graph API integration.
Pattern borrowed from Denario's literature.py SSAPI() function.
"""

import time
import requests
from ..config import MAX_API_TIMEOUT, SEMANTIC_SCHOLAR_KEY

BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "title,authors,year,abstract,url,citationCount,externalIds"


def search_papers(query: str, limit: int = 8) -> tuple[str, list[dict]]:
    """
    Search Semantic Scholar for papers matching a query.

    Adapted from Denario's SSAPI() with retry logic — Semantic Scholar's
    free tier has aggressive rate limiting.

    Args:
        query: Search query (e.g. "KRAS G12C drug resistance mechanisms").
        limit: Maximum number of papers to return.

    Returns:
        Tuple of (formatted markdown string, list of citation dicts).
    """
    params = {
        "query": query,
        "limit": limit,
        "fields": FIELDS,
    }
    headers = {}
    if SEMANTIC_SCHOLAR_KEY:
        headers["x-api-key"] = SEMANTIC_SCHOLAR_KEY

    # Retry loop (Denario pattern: handles rate-limiting 429s)
    last_error = ""
    for attempt in range(5):
        try:
            resp = requests.get(
                BASE_URL,
                params=params,
                headers=headers if headers else None,
                timeout=MAX_API_TIMEOUT,
            )
            if resp.status_code == 200:
                return _format_results(resp.json(), query)
            elif resp.status_code == 429:
                # Rate limited — back off
                time.sleep(1.0 * (attempt + 1))
                last_error = "Rate limited (429)"
                continue
            else:
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                time.sleep(0.5)
        except requests.Timeout:
            last_error = "Request timed out"
            time.sleep(0.5)
        except requests.RequestException as e:
            last_error = str(e)
            break

    return f"**Semantic Scholar search failed** for '{query}': {last_error}. Try again later.", []


def _format_results(data: dict, query: str) -> tuple[str, list[dict]]:
    """Format Semantic Scholar API response into markdown and structured citations."""
    total = data.get("total", 0)
    papers = data.get("data", [])

    if not papers:
        return f"**No Semantic Scholar results for '{query}'.** Try different terms.", []

    summary = f"**{total} Semantic Scholar results for '{query}'** (showing {len(papers)}):\n\n"
    citations: list[dict] = []

    for idx, paper in enumerate(papers):
        title = paper.get("title", "Untitled") or "Untitled"
        year = paper.get("year", "N/A")
        citation_count = paper.get("citationCount", 0)
        url = paper.get("url", "")

        # Authors (first 3)
        authors_list = paper.get("authors", [])
        author_names = [a.get("name", "Unknown") for a in authors_list[:3]]
        author_str = ", ".join(author_names)
        if len(authors_list) > 3:
            author_str += " et al."

        # Abstract
        abstract = paper.get("abstract", "No abstract available.") or "No abstract available."
        abstract = (abstract[:300] + "...") if len(abstract) > 300 else abstract

        # External IDs (DOI, ArXiv)
        ext_ids = paper.get("externalIds", {}) or {}
        arxiv_id = ext_ids.get("ArXiv", "")
        doi = ext_ids.get("DOI", "")

        # Best link: DOI > ArXiv > Semantic Scholar URL
        if doi:
            link = f"https://doi.org/{doi}"
        elif arxiv_id:
            link = f"https://arxiv.org/abs/{arxiv_id}"
        else:
            link = url

        summary += (
            f"- **{title}** ({year}, {citation_count} citations)\n"
            f"  Authors: {author_str}\n"
            f"  Link: {link}\n"
            f"  Abstract: {abstract}\n\n"
        )

        # Build structured citation
        citations.append({
            "id": f"ss-{idx + 1}",
            "type": "semantic_scholar",
            "title": title,
            "authors": author_str,
            "year": str(year) if year else "",
            "journal": "",
            "url": link,
            "pmid": "",
            "doi": doi,
            "nct_id": "",
            "source_agent": "Literature Miner",
        })

    return summary, citations
