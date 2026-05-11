from __future__ import annotations

import asyncio
import json
import os
from typing import Any, TypeVar

from pydantic import BaseModel

from backend.model_routing import MODEL_ROUTING
from backend.tools.api_cache import get_api_cache


T = TypeVar("T", bound=BaseModel)


class LLMUnavailable(RuntimeError):
    """Raised when the routed OpenAI client cannot be used in this environment."""


async def complete_structured(
    agent_name: str,
    system_prompt: str,
    user_prompt: str,
    response_model: type[T],
    *,
    temperature: float = 0.2,
) -> T:
    """Call the routed OpenAI model and parse a Pydantic structured output.

    The import is intentionally lazy so local smoke tests can run without the
    OpenAI package installed. Successful responses are cached in the same SQLite
    cache as literature calls, keyed by model, prompt, and response schema.
    """

    return await asyncio.to_thread(
        _complete_structured_sync,
        agent_name,
        system_prompt,
        user_prompt,
        response_model,
        temperature,
    )


def _complete_structured_sync(
    agent_name: str,
    system_prompt: str,
    user_prompt: str,
    response_model: type[T],
    temperature: float,
) -> T:
    if not os.getenv("OPENAI_API_KEY"):
        raise LLMUnavailable("OPENAI_API_KEY is not set")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMUnavailable("The openai package is not installed") from exc

    model = MODEL_ROUTING.get(agent_name, agent_name)
    schema = _model_schema(response_model)
    cache_params = {
        "model": model,
        "agent_name": agent_name,
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "response_schema": schema,
        "temperature": temperature,
    }
    cache = get_api_cache()
    cached = cache.get("openai_structured", "structured_completion", cache_params)
    if cached is not None:
        return _validate(response_model, cached["parsed"])

    client = OpenAI()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    errors: list[str] = []

    for caller in (
        lambda: _call_chat_parse(client, model, messages, response_model, temperature),
        lambda: _call_responses_parse(client, model, system_prompt, user_prompt, response_model, temperature),
        lambda: _call_json_schema(client, model, messages, response_model, schema, temperature),
    ):
        try:
            parsed = caller()
        except Exception as exc:  # pragma: no cover - depends on installed OpenAI SDK shape.
            errors.append(f"{type(exc).__name__}: {exc}")
            continue

        cache.set(
            "openai_structured",
            "structured_completion",
            cache_params,
            {"parsed": _dump_model(parsed)},
        )
        return parsed

    raise LLMUnavailable("OpenAI structured output call failed: " + " | ".join(errors))


def _call_chat_parse(
    client: Any,
    model: str,
    messages: list[dict[str, str]],
    response_model: type[T],
    temperature: float,
) -> T:
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=messages,
        response_format=response_model,
        temperature=temperature,
    )
    parsed = completion.choices[0].message.parsed
    if parsed is None:
        content = completion.choices[0].message.content or "{}"
        return _validate(response_model, json.loads(content))
    return _validate(response_model, _dump_model(parsed))


def _call_responses_parse(
    client: Any,
    model: str,
    system_prompt: str,
    user_prompt: str,
    response_model: type[T],
    temperature: float,
) -> T:
    response = client.responses.parse(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        text_format=response_model,
        temperature=temperature,
    )
    parsed = getattr(response, "output_parsed", None)
    if parsed is not None:
        return _validate(response_model, _dump_model(parsed))

    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            parsed_content = getattr(content, "parsed", None)
            if parsed_content is not None:
                return _validate(response_model, _dump_model(parsed_content))
            text = getattr(content, "text", None)
            if text:
                return _validate(response_model, json.loads(text))

    raise LLMUnavailable("Responses API returned no parsed output")


def _call_json_schema(
    client: Any,
    model: str,
    messages: list[dict[str, str]],
    response_model: type[T],
    schema: dict[str, Any],
    temperature: float,
) -> T:
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": response_model.__name__,
                "schema": schema,
                "strict": True,
            },
        },
        temperature=temperature,
    )
    content = completion.choices[0].message.content or "{}"
    return _validate(response_model, json.loads(content))


def _validate(response_model: type[T], payload: dict[str, Any]) -> T:
    if hasattr(response_model, "model_validate"):
        return response_model.model_validate(payload)
    return response_model.parse_obj(payload)


def _dump_model(model: BaseModel | dict[str, Any]) -> dict[str, Any]:
    if isinstance(model, dict):
        return model
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _model_schema(response_model: type[BaseModel]) -> dict[str, Any]:
    if hasattr(response_model, "model_json_schema"):
        return response_model.model_json_schema()
    return response_model.schema()
