from __future__ import annotations

import math
import re
from collections import Counter
from datetime import datetime
from typing import Any, Iterable

from backend.schemas import MetricScore, Paper, ParsedHypothesis


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "using",
    "with",
    "plus",
    "should",
    "produce",
    "produces",
    "prediction",
    "predict",
    "improve",
    "improves",
    "contain",
    "contains",
    "information",
    "feature",
    "features",
    "compact",
    "combining",
    "combined",
    "learned",
    "mock",
    "hypothesis",
    "research",
    "stated",
    "structured",
    "extracted",
    "extract",
    "claim",
    "mechanism",
    "context",
    "population",
    "method",
    "target",
    "setting",
    "demo",
    "idea",
    "hater",
    "quantitative",
    "pathway",
    "measurable",
    "intervention",
    "outcome",
}

NOISY_PHRASES = (
    "mock structured claim extracted from",
    "mock mechanism",
    "mock context",
    "mock population",
    "mock method",
    "quantitative pathway 42",
    "literature-backed idea hater demo",
    "target research setting",
    "measurable intervention and outcome",
)


def parsed_query(state: dict[str, Any], *, max_terms: int = 14) -> str:
    parsed = state.get("parsed")
    parts = [state.get("raw_hypothesis", "")]
    if isinstance(parsed, ParsedHypothesis):
        parts.extend([parsed.claim, parsed.mechanism, parsed.context, parsed.population, parsed.method])
    elif parsed:
        dumped = _dump(parsed)
        parts.extend(str(dumped.get(key, "")) for key in ("claim", "mechanism", "context", "population", "method"))

    tokens = tokens_for_text(clean_query_text(" ".join(str(part) for part in parts if part)))
    counts = Counter(tokens)
    ranked = [token for token, _count in counts.most_common(max_terms)]
    return " ".join(ranked) or "research hypothesis"


def query_candidates(state: dict[str, Any], *, max_candidates: int = 6) -> list[str]:
    raw = clean_query_text(str(state.get("raw_hypothesis", "")))
    parsed_text = clean_query_text(hypothesis_text(state))
    candidates = [
        parsed_query(state, max_terms=10),
        _keyword_query(raw, max_terms=10),
        _keyword_query(parsed_text, max_terms=10),
        _keyword_query(raw, max_terms=6),
        _keyword_query(parsed_text, max_terms=6),
        raw,
    ]
    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        candidate = clean_query_text(candidate)
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        deduped.append(candidate)
        if len(deduped) >= max_candidates:
            break
    return deduped or ["research hypothesis"]


def hypothesis_text(state: dict[str, Any]) -> str:
    parsed = state.get("parsed")
    if isinstance(parsed, ParsedHypothesis):
        return clean_query_text(" ".join([parsed.claim, parsed.mechanism, parsed.context, parsed.population, parsed.method]))
    if parsed:
        dumped = _dump(parsed)
        return clean_query_text(" ".join(str(dumped.get(key, "")) for key in ("claim", "mechanism", "context", "population", "method")))
    return clean_query_text(str(state.get("raw_hypothesis", "")))


def paper_evidence_id(paper: Paper) -> str:
    doi = normalize_doi(paper.doi)
    if doi:
        return f"doi:{doi}"
    openalex_id = normalize_openalex_id(paper.openalex_id)
    if openalex_id:
        return f"openalex:{openalex_id}"
    semantic_scholar_id = (paper.semantic_scholar_id or "").strip()
    if semantic_scholar_id:
        return f"s2:{semantic_scholar_id}"
    return paper.paper_id


def normalize_doi(value: str | None) -> str:
    if not value:
        return ""
    doi = value.strip().lower()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    doi = doi.removeprefix("doi:").strip()
    return doi


def normalize_openalex_id(value: str | None) -> str:
    if not value:
        return ""
    openalex_id = value.strip()
    if "/" in openalex_id:
        openalex_id = openalex_id.rsplit("/", 1)[-1]
    return openalex_id.removeprefix("openalex:")


def make_metric(
    name: str,
    score: float,
    rationale: str,
    evidence_ids: Iterable[str] = (),
    weakness: str = "",
    *,
    confidence_span: int = 10,
    confidence_low: int | None = None,
    confidence_high: int | None = None,
    method: str,
) -> MetricScore:
    score_int = clamp_score(score)
    low = max(0, score_int - confidence_span) if confidence_low is None else confidence_low
    high = min(100, score_int + confidence_span) if confidence_high is None else confidence_high
    stable_ids = [evidence_id for evidence_id in evidence_ids if evidence_id]
    return MetricScore(
        name=name,
        score=score_int,
        confidence_low=min(score_int, max(0, int(low))),
        confidence_high=max(score_int, min(100, int(high))),
        rationale=rationale,
        evidence_ids=stable_ids,
        method=method,
        weakness=weakness,
    )


def no_papers_metric(name: str) -> MetricScore:
    return make_metric(
        name,
        40,
        f"{name} is low-confidence because no real literature neighbourhood was available.",
        [],
        "Run cartographer successfully before trusting this dashboard metric.",
        confidence_span=25,
        method="fallback:no_real_papers",
    )


def sorted_papers(state: dict[str, Any], *, min_relevance: float = 0.0) -> list[Paper]:
    papers = [paper for paper in state.get("papers", []) if isinstance(paper, Paper)]
    filtered = [paper for paper in papers if paper.relevance_score >= min_relevance]
    return sorted(filtered, key=lambda paper: (paper.relevance_score, paper.citation_count, paper.year or 0), reverse=True)


def text_relevance(query_text: str, title: str, abstract: str = "") -> float:
    query_tokens = set(tokens_for_text(query_text))
    if not query_tokens:
        return 0.0
    title_tokens = set(tokens_for_text(title))
    abstract_tokens = set(tokens_for_text(abstract))
    title_overlap = len(query_tokens & title_tokens) / len(query_tokens)
    abstract_overlap = len(query_tokens & abstract_tokens) / len(query_tokens)
    return min(1.0, (title_overlap * 0.65) + (abstract_overlap * 0.35))


def tokens_for_text(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9_+-]{2,}", text.lower())
        if token not in STOPWORDS and not token.isdigit()
    ]


def clean_query_text(text: str) -> str:
    cleaned = str(text or "")
    for phrase in NOISY_PHRASES:
        cleaned = re.sub(re.escape(phrase), " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bmock[-_\s]+", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[^a-zA-Z0-9_+\-\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _keyword_query(text: str, *, max_terms: int) -> str:
    tokens = tokens_for_text(text)
    counts = Counter(tokens)
    return " ".join(token for token, _count in counts.most_common(max_terms))


def cluster_label(paper: Paper, query_text: str) -> str:
    tokens = [token for token in tokens_for_text(f"{paper.title} {paper.abstract}") if token not in tokens_for_text(query_text)[:8]]
    if not tokens:
        tokens = tokens_for_text(paper.title)
    common = [token for token, _count in Counter(tokens).most_common(2)]
    return " / ".join(common) if common else "unclustered"


def citation_percentile(papers: list[Paper], paper: Paper) -> float:
    if not papers:
        return 0.0
    below_or_equal = sum(1 for item in papers if item.citation_count <= paper.citation_count)
    return below_or_equal / len(papers)


def recency_score(year: int | None) -> float:
    if not year:
        return 0.4
    age = max(0, datetime.now().year - year)
    return max(0.0, min(1.0, 1 - (age / 12)))


def clamp_score(value: float) -> int:
    if math.isnan(value) or math.isinf(value):
        return 0
    return max(0, min(100, round(value)))


def _dump(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return value
    return {}
