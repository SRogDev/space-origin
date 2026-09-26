"""Wiki content loader: parses frontmatter + markdown body from ``wiki/``.

Content types: technologies, policies, events, values, places, lore.
Also owns the machine-readable modifier whitelist: the valid dotted paths
(``population.satisfaction``, ``economy.treasury``, ...) are derived from
``api/models.py`` so prose and code can never drift apart.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import annotated_types
import yaml
from pydantic import BaseModel

from api.models import Game

CONTENT_TYPES = ("technologies", "policies", "events", "values", "places", "lore")

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)


def wiki_dir() -> Path:
    """Resolve the wiki directory: ``SO_WIKI_DIR`` wins, else ``<repo>/wiki``."""
    env = os.environ.get("SO_WIKI_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent / "wiki"


def parse_file(path: Path) -> dict[str, Any]:
    """Parse one wiki file -> {"id", "meta", "body"}."""
    text = path.read_text(encoding="utf-8")
    m = _FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError(f"{path}: missing YAML frontmatter")
    meta = yaml.safe_load(m.group(1)) or {}
    body = m.group(2).strip()
    cid = meta.get("id") or path.stem
    return {"id": cid, "meta": meta, "body": body}


def list_content(ctype: str) -> list[dict[str, Any]]:
    """List all content items of a type (files starting with ``_`` are skipped)."""
    if ctype not in CONTENT_TYPES:
        raise ValueError(f"unknown content type: {ctype!r}")
    folder = wiki_dir() / ctype
    items = []
    for path in sorted(folder.glob("*.md")):
        if path.name.startswith("_"):
            continue
        items.append(parse_file(path))
    return items


def get_content(ctype: str, cid: str) -> dict[str, Any]:
    """Fetch one content item. Raises KeyError when the id does not exist."""
    if ctype not in CONTENT_TYPES:
        raise ValueError(f"unknown content type: {ctype!r}")
    for item in list_content(ctype):
        if item["id"] == cid:
            return item
    raise KeyError(f"unknown {ctype} id: {cid!r}")


# ---------------------------------------------------------------------------
# Modifier whitelist: dotted float paths derived from the Game model.
# Policies use ADDITIVE deltas, technologies use FRACTIONAL MULTIPLICATIVE
# deltas, events use ADDITIVE deltas (see wiki templates for the convention).
# ---------------------------------------------------------------------------


def _build_modifiable_paths() -> dict[str, tuple[type[BaseModel], str]]:
    """{"section.field": (SectionModel, field_name)} for every float field."""
    paths: dict[str, tuple[type[BaseModel], str]] = {}
    for section_name, field in Game.model_fields.items():
        section_cls = field.annotation
        if not (isinstance(section_cls, type) and issubclass(section_cls, BaseModel)):
            continue
        for sub_name, sub in section_cls.model_fields.items():
            if sub.annotation is float:
                paths[f"{section_name}.{sub_name}"] = (section_cls, sub_name)
    return paths


MODIFIABLE_PATHS: dict[str, tuple[type[BaseModel], str]] = _build_modifiable_paths()


def _field_bounds(section_cls: type[BaseModel], field_name: str) -> tuple[float, float]:
    lo, hi = float("-inf"), float("inf")
    for meta in section_cls.model_fields[field_name].metadata:
        if isinstance(meta, annotated_types.Ge):
            lo = max(lo, meta.ge)
        elif isinstance(meta, annotated_types.Gt):
            lo = max(lo, meta.gt)
        elif isinstance(meta, annotated_types.Le):
            hi = min(hi, meta.le)
        elif isinstance(meta, annotated_types.Lt):
            hi = min(hi, meta.lt)
    return lo, hi


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def apply_modifier(game: Game, path: str, delta: float, mode: str = "additive") -> None:
    """Apply a machine-readable modifier to the game state, bounds-checked.

    mode="additive":        new = old + delta   (policies, events)
    mode="multiplicative":  new = old * (1 + delta)  (technologies)
    """
    if path not in MODIFIABLE_PATHS:
        raise ValueError(f"modifier path not whitelisted: {path!r}")
    try:
        delta_f = float(delta)
    except (TypeError, ValueError) as e:
        raise ValueError(f"modifier delta must be numeric: {delta!r}") from e
    if mode not in ("additive", "multiplicative"):
        raise ValueError(f"unknown modifier mode: {mode!r}")
    section_cls, field_name = MODIFIABLE_PATHS[path]
    section_name = path.split(".")[0]
    section = getattr(game, section_name)
    old = getattr(section, field_name)
    new = old + delta_f if mode == "additive" else old * (1.0 + delta_f)
    lo, hi = _field_bounds(section_cls, field_name)
    setattr(section, field_name, _clamp(new, lo, hi))
