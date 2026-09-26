"""Phase-2 STUB — AI narration layer.

ARCHITECTURAL CONTRACT (non-negotiable):
* ``narrate`` takes ONLY an immutable plain-data mapping. It deep-copies the
  input at the boundary, takes no Game/model arguments, and can never reach —
  let alone mutate — simulation state. The AI narrates facts; it never decides.
* If ``langgraph`` is importable, narration runs as a tiny LangGraph graph
  (format_delta -> llm_call -> output). Otherwise a plain function with the
  identical signature is used. The active path is logged.
* ``narrate`` NEVER raises: missing API key, network errors, malformed input
  all collapse to a deterministic template fallback. No invented numbers.
"""

from __future__ import annotations

import copy
import logging
import os
from typing import Any, Mapping

logger = logging.getLogger(__name__)

try:  # guarded: the core sim and its tests must work without langgraph
    from langgraph.graph import END, StateGraph

    _HAS_LANGGRAPH = True
except ImportError:
    _HAS_LANGGRAPH = False

try:  # guarded for the same reason
    import httpx

    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False

_HAS_OPENROUTER_ENV = bool(os.environ.get("OPENROUTER_API_KEY"))

_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_MODEL = "openai/gpt-4o-mini"
_SYSTEM_PROMPT = (
    "You are the news service of a 2280 space colony. "
    "Turn these FACTS into a 3-5 sentence news bulletin. Do not invent numbers."
)


def _fallback(facts: dict) -> str:
    """Deterministic template bulletin. Never raises, never invents numbers."""

    def get(key: str, default: str = "?") -> Any:
        value = facts.get(key, default)
        return default if value is None else value

    bulletin = (
        f"Colony bulletin {get('year')}: "
        f"population {get('population')}, treasury {get('treasury')} credits."
    )
    latest = facts.get("latest")
    if latest:
        bulletin += f" Latest: {latest}"
    recent = facts.get("recent_events")
    if recent:
        names = ", ".join(str(e) for e in recent) if isinstance(recent, list) else str(recent)
        bulletin += f" Notable events: {names}."
    return bulletin


def _call_openrouter(facts: dict) -> str:
    """POST facts to OpenRouter. Raises on missing key / any error (caller catches)."""
    if not _HAS_HTTPX:
        raise RuntimeError("httpx is not installed")
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    facts_text = "\n".join(f"- {k}: {v}" for k, v in facts.items())
    response = httpx.post(
        _OPENROUTER_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": _MODEL,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": facts_text or "(no facts provided)"},
            ],
            "max_tokens": 300,
        },
        timeout=10.0,
    )
    response.raise_for_status()
    text = response.json()["choices"][0]["message"]["content"]
    if not text or not str(text).strip():
        raise RuntimeError("empty completion")
    return str(text).strip()


_graph: Any = None


def _get_graph() -> Any:
    """Lazily compile the format_delta -> llm_call -> output graph."""
    global _graph
    if _graph is None:
        from typing import TypedDict

        class NarratorState(TypedDict):
            facts: dict
            text: str

        def format_delta(state: NarratorState) -> dict:
            facts = state["facts"]
            rendered = "\n".join(f"- {k}: {v}" for k, v in facts.items())
            return {"facts": {**facts, "rendered": rendered}}

        def llm_call(state: NarratorState) -> dict:
            return {"text": _call_openrouter(state["facts"])}

        def output(state: NarratorState) -> dict:
            return {"text": state.get("text") or _fallback(state["facts"])}

        builder = StateGraph(NarratorState)
        builder.add_node("format_delta", format_delta)
        builder.add_node("llm_call", llm_call)
        builder.add_node("output", output)
        builder.set_entry_point("format_delta")
        builder.add_edge("format_delta", "llm_call")
        builder.add_edge("llm_call", "output")
        builder.add_edge("output", END)
        _graph = builder.compile()
    return _graph


def narrate(state_delta: Mapping) -> str:
    """Turn a plain-data state delta into a news bulletin. Never raises.

    ``state_delta`` is deep-copied at the boundary: the caller keeps its object,
    and this function can never reach the live Game.
    """
    try:
        facts = copy.deepcopy(dict(state_delta))
    except Exception:
        facts = {}
    try:
        if _HAS_LANGGRAPH:
            logger.info("narrator: langgraph path (format_delta -> llm_call -> output)")
            result = _get_graph().invoke({"facts": facts, "text": ""})
            text = result.get("text") if isinstance(result, dict) else None
            return text or _fallback(facts)
        logger.info("narrator: plain-function stub path (langgraph unavailable)")
        return _call_openrouter(facts)
    except Exception as exc:
        logger.warning("narrator: falling back to template (%s)", type(exc).__name__)
        return _fallback(facts)
