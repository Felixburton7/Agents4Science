from __future__ import annotations

import json
import re
from typing import Any

from backend.llm_client import LLMUnavailable, complete_structured
from backend.schemas import ParsedHypothesis


FIELD_HINTS = {
    "mechanism": (" via ", " through ", " by ", " because ", " mediated by "),
    "context": (" in ", " within ", " among ", " during ", " for "),
    "method": (" using ", " measured by ", " tested with ", " evaluated with ", " randomized "),
}


async def parser(state: dict[str, Any]) -> dict[str, ParsedHypothesis]:
    raw_hypothesis = str(state.get("raw_hypothesis", "")).strip()
    if not raw_hypothesis:
        raise ValueError("raw_hypothesis is required for parser")

    system_prompt = (
        "You are the Parser agent for the Hypothesis Steering Engine. "
        "Extract the user's hypothesis into claim, mechanism, context, population, and method. "
        "Preserve the user's intended meaning. Use 'unspecified' for missing fields. "
        "Do not evaluate novelty, feasibility, impact, or add citations."
    )
    user_prompt = json.dumps(
        {
            "raw_hypothesis": raw_hypothesis,
            "output_contract": "Return a ParsedHypothesis object with claim, mechanism, context, population, and method.",
        },
        indent=2,
    )

    try:
        parsed = await complete_structured("parser", system_prompt, user_prompt, ParsedHypothesis, temperature=0.0)
    except (LLMUnavailable, ValueError, TypeError, json.JSONDecodeError):
        parsed = _deterministic_parse(raw_hypothesis)

    return {"parsed": _repair(parsed, raw_hypothesis)}


run = parser


def _deterministic_parse(raw_hypothesis: str) -> ParsedHypothesis:
    normalized = _clean(raw_hypothesis)
    return ParsedHypothesis(
        claim=_claim(normalized),
        mechanism=_field_after_hint(normalized, FIELD_HINTS["mechanism"]),
        context=_field_after_hint(normalized, FIELD_HINTS["context"]),
        population=_population(normalized),
        method=_field_after_hint(normalized, FIELD_HINTS["method"]),
    )


def _repair(parsed: ParsedHypothesis, raw_hypothesis: str) -> ParsedHypothesis:
    values = parsed.model_dump() if hasattr(parsed, "model_dump") else parsed.dict()
    repaired = {
        key: _clean(str(values.get(key) or "unspecified")) or "unspecified"
        for key in ("claim", "mechanism", "context", "population", "method")
    }
    if repaired["claim"] == "unspecified":
        repaired["claim"] = _claim(raw_hypothesis)
    return ParsedHypothesis(**repaired)


def _claim(text: str) -> str:
    sentence = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0]
    return _truncate(sentence or text, 220)


def _field_after_hint(text: str, hints: tuple[str, ...]) -> str:
    lowered = f" {text.lower()} "
    for hint in hints:
        index = lowered.find(hint)
        if index == -1:
            continue
        start = index + len(hint)
        fragment = text[start:].strip(" ,.;:")
        fragment = re.split(r"\b(?:and|but|while|whereas|which)\b|[.;]", fragment, maxsplit=1)[0]
        return _truncate(_clean(fragment), 140) or "unspecified"
    return "unspecified"


def _population(text: str) -> str:
    patterns = (
        r"\b(?:patients|participants|cells|mice|students|researchers|models|datasets|samples)\b[^.;,]*",
        r"\b(?:children|adults|humans|women|men|clinicians|learners)\b[^.;,]*",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _truncate(_clean(match.group(0)), 140)
    return "unspecified"


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _truncate(value: str, limit: int) -> str:
    value = _clean(value)
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip(" ,.;:") + "."