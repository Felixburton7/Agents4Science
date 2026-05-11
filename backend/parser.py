from __future__ import annotations

import json
import re
from typing import Any

from backend.evidence_utils import clean_query_text
from backend.llm_client import LLMUnavailable, complete_structured
from backend.schemas import ParsedHypothesis


async def parser(state: dict[str, Any]) -> dict[str, ParsedHypothesis]:
    hypothesis = str(state.get("raw_hypothesis", "")).strip()
    if not hypothesis:
        return {
            "parsed": ParsedHypothesis(
                claim="",
                mechanism="",
                context="",
                population="",
                method="",
            )
        }

    prompt = json.dumps(
        {
            "hypothesis": hypothesis,
            "instruction": (
                "Extract the scientific claim, mechanism, context, population, and method. "
                "Use only information present in the hypothesis. Do not add generic labels."
            ),
        },
        indent=2,
    )
    try:
        parsed = await complete_structured(
            "parser",
            "Parse a research hypothesis into the ParsedHypothesis schema.",
            prompt,
            ParsedHypothesis,
            temperature=0.1,
        )
    except (LLMUnavailable, ValueError, TypeError):
        parsed = _heuristic_parse(hypothesis)

    return {"parsed": _repair_parse(parsed, hypothesis)}


run = parser


def _heuristic_parse(hypothesis: str) -> ParsedHypothesis:
    clean = clean_query_text(hypothesis)
    mechanism = _after_keywords(clean, ("because", "by", "through", "via", "using", "combining"))
    method = _after_keywords(clean, ("using", "combining", "with", "via"))
    context = _context_phrase(clean)
    population = _population_phrase(clean)
    return ParsedHypothesis(
        claim=clean,
        mechanism=mechanism or "mechanism stated in the hypothesis",
        context=context or "research context stated in the hypothesis",
        population=population or "target system or dataset stated in the hypothesis",
        method=method or "method stated in the hypothesis",
    )


def _repair_parse(parsed: ParsedHypothesis, hypothesis: str) -> ParsedHypothesis:
    updates: dict[str, str] = {}
    for field in ("claim", "mechanism", "context", "population", "method"):
        value = clean_query_text(str(getattr(parsed, field, "") or ""))
        if not value or _is_placeholder(value):
            value = _fallback_value(field, hypothesis)
        updates[field] = value
    return parsed.model_copy(update=updates)


def _fallback_value(field: str, hypothesis: str) -> str:
    parsed = _heuristic_parse(hypothesis)
    return getattr(parsed, field)


def _is_placeholder(value: str) -> bool:
    text = value.lower()
    placeholders = (
        "mock ",
        "structured claim extracted",
        "quantitative pathway",
        "literature-backed idea hater demo",
        "target research setting",
        "measurable intervention and outcome",
    )
    return any(placeholder in text for placeholder in placeholders)


def _after_keywords(text: str, keywords: tuple[str, ...]) -> str:
    for keyword in keywords:
        match = re.search(rf"\b{re.escape(keyword)}\b(.+)$", text, flags=re.IGNORECASE)
        if match:
            phrase = match.group(1).strip(" .,;:")
            return _shorten(phrase, 24)
    return ""


def _context_phrase(text: str) -> str:
    markers = (" in ", " for ", " on ")
    for marker in markers:
        if marker in text:
            return _shorten(text.split(marker, 1)[1], 18)
    return ""


def _population_phrase(text: str) -> str:
    words = clean_query_text(text).split()
    domain_terms = [
        word
        for word in words
        if word
        in {
            "patients",
            "cells",
            "proteins",
            "datasets",
            "graphs",
            "galaxies",
            "halos",
            "merger",
            "trees",
            "language",
            "models",
            "parameters",
            "substructures",
        }
    ]
    return " ".join(domain_terms[:10])


def _shorten(text: str, max_words: int) -> str:
    words = clean_query_text(text).split()
    return " ".join(words[:max_words])
