"""Tests for the AI narrator stub: read-only, never raises, never touches the Game."""

import copy
import importlib
import inspect
import sys

import pytest

import api.ai.narrator as narrator


def test_signature_takes_only_plain_data():
    sig = inspect.signature(narrator.narrate)
    assert list(sig.parameters) == ["state_delta"]


def test_narrate_never_raises_on_empty_mapping():
    assert isinstance(narrator.narrate({}), str)


def test_narrate_does_not_mutate_input():
    delta = {"year": 2280, "colony": "New Dawn", "population": 10000}
    snapshot = copy.deepcopy(delta)
    text = narrator.narrate(delta)
    assert delta == snapshot
    assert isinstance(text, str) and text


def test_narrate_fallback_mentions_facts():
    text = narrator.narrate({"year": 2285, "population": 12000, "treasury": 900000})
    assert "2285" in text
    assert "12000" in text


def test_stub_mode_without_langgraph(monkeypatch):
    """Simulate langgraph being absent: the guard must kick in, same signature."""
    monkeypatch.setitem(sys.modules, "langgraph", None)
    monkeypatch.setitem(sys.modules, "langgraph.graph", None)
    try:
        importlib.reload(narrator)
        assert narrator._HAS_LANGGRAPH is False
        assert isinstance(narrator.narrate({"year": 2280}), str)
    finally:
        importlib.reload(narrator)  # restore real import state


@pytest.mark.skipif(not narrator._HAS_OPENROUTER_ENV, reason="needs OPENROUTER_API_KEY")
def test_live_call_only_with_key():
    # Never runs in CI; documents the live path without requiring it.
    text = narrator.narrate({"year": 2280, "population": 10000})
    assert isinstance(text, str)
