from __future__ import annotations

from typing import Any

from backend.evidence_utils import (
    cluster_label,
    normalize_doi,
    normalize_openalex_id,
    paper_evidence_id,
    parsed_query,
    query_candidates,
    text_relevance,
)
from backend.schemas import Paper
from backend.tools.openalex import search_works
from backend.tools.semantic_scholar import search_paper_records


MAX_PAPERS = 50
MAX_QUERY_ATTEMPTS = 5
MAX_SEMANTIC_SCHOLAR_QUERIES = 1


async def cartographer(state: dict[str, Any]) -> dict[str, Any]:
    primary_query = parsed_query(state)
    papers_by_key: dict[str, Paper] = {}
    openalex_total_count: int = 0

    attempted_queries = query_candidates(state, max_candidates=MAX_QUERY_ATTEMPTS)
    for query in attempted_queries:
        papers, count = _openalex_papers(query, primary_query)
        for paper in papers:
            _merge_paper(papers_by_key, paper)
        openalex_total_count = max(openalex_total_count, count)

    for query in attempted_queries[:MAX_SEMANTIC_SCHOLAR_QUERIES]:
        for paper in _semantic_scholar_papers(query, primary_query):
            _merge_paper(papers_by_key, paper)

    papers = list(papers_by_key.values())
    for index, paper in enumerate(papers):
        if not paper.cluster or paper.cluster == "unclustered":
            papers[index] = _copy_model(paper, cluster=cluster_label(paper, primary_query))

    papers = _embed_rerank(papers, primary_query)

    ranked = sorted(
        papers,
        key=lambda paper: (paper.relevance_score, len(paper.source_provenance), paper.citation_count, paper.year or 0),
        reverse=True,
    )[:MAX_PAPERS]
    return {"papers": ranked, "openalex_total_count": openalex_total_count}


run = cartographer


def _openalex_papers(query: str, scoring_query: str) -> tuple[list[Paper], int]:
    try:
        data = search_works(query, per_page=MAX_PAPERS)
    except Exception:
        return [], 0

    total_count: int = int((data.get("meta") or {}).get("count") or 0)
    results = data.get("results", [])
    max_raw_relevance = max((float(work.get("relevance_score") or 0) for work in results), default=0.0)
    papers = []
    for rank, work in enumerate(results, start=1):
        title = (work.get("display_name") or work.get("title") or "").strip()
        if not title:
            continue

        abstract = _openalex_abstract(work.get("abstract_inverted_index") or {})
        doi = normalize_doi(work.get("doi"))
        openalex_id = normalize_openalex_id(work.get("id") or (work.get("ids") or {}).get("openalex"))
        authors = [
            ((authorship.get("author") or {}).get("display_name") or "").strip()
            for authorship in work.get("authorships", [])[:8]
        ]
        authors = [author for author in authors if author]
        lexical_relevance = max(text_relevance(query, title, abstract), text_relevance(scoring_query, title, abstract))
        relevance = lexical_relevance
        raw_relevance = float(work.get("relevance_score") or 0)
        if max_raw_relevance > 0:
            ranked_relevance = (raw_relevance / max_raw_relevance) * 0.55 + max(0.0, 1 - (rank / MAX_PAPERS)) * 0.15
            relevance = max(relevance, min(1.0, (lexical_relevance * 0.75) + (ranked_relevance * 0.25)))
        if relevance < 0.05 or "<mml:" in title.lower():
            continue

        paper = Paper(
            paper_id="",
            title=title,
            authors=authors,
            year=work.get("publication_year"),
            abstract=abstract,
            url=_openalex_url(work),
            citation_count=int(work.get("cited_by_count") or 0),
            relevance_score=round(relevance, 3),
            cluster=_concept_cluster(work),
            doi=doi,
            openalex_id=openalex_id,
            semantic_scholar_id="",
            source_provenance=["openalex"],
        )
        papers.append(_copy_model(paper, paper_id=paper_evidence_id(paper)))
    return papers, total_count


def _semantic_scholar_papers(query: str, scoring_query: str) -> list[Paper]:
    try:
        records = search_paper_records(query, limit=MAX_PAPERS // 2)
    except Exception:
        return []

    papers = []
    for record in records:
        title = (record.get("title") or "").strip()
        if not title:
            continue
        external_ids = record.get("externalIds") or {}
        doi = normalize_doi(external_ids.get("DOI"))
        openalex_id = normalize_openalex_id(external_ids.get("OpenAlex"))
        semantic_scholar_id = (record.get("paperId") or "").strip()
        abstract = record.get("abstract") or ""
        authors = [(author.get("name") or "").strip() for author in record.get("authors", [])[:8]]
        authors = [author for author in authors if author]
        paper = Paper(
            paper_id="",
            title=title,
            authors=authors,
            year=record.get("year"),
            abstract=abstract,
            url=_semantic_scholar_url(record, doi),
            citation_count=int(record.get("citationCount") or 0),
            relevance_score=round(max(text_relevance(query, title, abstract), text_relevance(scoring_query, title, abstract)), 3),
            cluster="unclustered",
            doi=doi,
            openalex_id=openalex_id,
            semantic_scholar_id=semantic_scholar_id,
            source_provenance=["semantic_scholar"],
        )
        papers.append(_copy_model(paper, paper_id=paper_evidence_id(paper)))
    return papers


def _merge_paper(papers_by_key: dict[str, Paper], incoming: Paper) -> None:
    keys = [paper_evidence_id(incoming), incoming.title.strip().lower()]
    existing_key = next((key for key in keys if key in papers_by_key), None)
    if existing_key is None:
        papers_by_key[keys[0]] = incoming
        return

    existing = papers_by_key[existing_key]
    provenance = sorted(set(existing.source_provenance) | set(incoming.source_provenance))
    merged = _copy_model(
        existing,
        authors=existing.authors or incoming.authors,
        year=existing.year or incoming.year,
        abstract=existing.abstract if len(existing.abstract) >= len(incoming.abstract) else incoming.abstract,
        url=existing.url or incoming.url,
        citation_count=max(existing.citation_count, incoming.citation_count),
        relevance_score=round(max(existing.relevance_score, incoming.relevance_score), 3),
        cluster=existing.cluster if existing.cluster != "unclustered" else incoming.cluster,
        doi=existing.doi or incoming.doi,
        openalex_id=existing.openalex_id or incoming.openalex_id,
        semantic_scholar_id=existing.semantic_scholar_id or incoming.semantic_scholar_id,
        source_provenance=provenance,
    )
    merged = _copy_model(merged, paper_id=paper_evidence_id(merged))
    papers_by_key.pop(existing_key, None)
    papers_by_key[paper_evidence_id(merged)] = merged


def _openalex_abstract(index: dict[str, list[int]]) -> str:
    if not index:
        return ""
    positions: dict[int, str] = {}
    for word, offsets in index.items():
        for offset in offsets:
            positions[int(offset)] = word
    return " ".join(positions[position] for position in sorted(positions))


def _openalex_url(work: dict[str, Any]) -> str:
    primary_location = work.get("primary_location") or {}
    source_url = primary_location.get("landing_page_url") or primary_location.get("pdf_url")
    return source_url or work.get("doi") or work.get("id") or ""


def _semantic_scholar_url(record: dict[str, Any], doi: str) -> str:
    if doi:
        return f"https://doi.org/{doi}"
    return record.get("url") or ""


def _concept_cluster(work: dict[str, Any]) -> str:
    concepts = [concept.get("display_name", "") for concept in work.get("concepts", [])[:2] if concept.get("display_name")]
    return " / ".join(concepts) if concepts else "unclustered"


def _embed_rerank(papers: list[Paper], primary_query: str) -> list[Paper]:
    """Re-score papers using embedding similarity, blended with existing lexical scores.

    Sends ONE batch API call for all uncached texts, then updates relevance_score:
        final = max(lexical, 0.4*lexical + 0.6*embedding)
    Falls back to the original papers unchanged if embeddings are unavailable.
    """
    from backend.embedding_utils import embed_texts, embedding_relevance

    # Warm the cache in a single batch call: query + all unique titles/abstracts.
    unique_texts: list[str] = []
    seen: set[str] = set()
    for text in [primary_query] + [p.title for p in papers] + [p.abstract for p in papers if p.abstract.strip()]:
        if text not in seen:
            seen.add(text)
            unique_texts.append(text)

    if embed_texts(unique_texts) is None:
        return papers  # API key absent or call failed — keep lexical scores

    updated: list[Paper] = []
    for paper in papers:
        embedding_score = embedding_relevance(primary_query, paper.title, paper.abstract)
        if embedding_score is None:
            updated.append(paper)
            continue
        lexical = paper.relevance_score
        blended = max(lexical, 0.4 * lexical + 0.6 * embedding_score)
        updated.append(_copy_model(paper, relevance_score=round(blended, 3)))
    return updated


def _copy_model(model: Any, **updates: Any) -> Any:
    if hasattr(model, "model_copy"):
        return model.model_copy(update=updates)
    return model.copy(update=updates)
