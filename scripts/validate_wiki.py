#!/usr/bin/env python3
"""Validate the SpaceOrigins wiki content (game design data).

Walks wiki/*/, skipping files starting with `_` (templates) and the values/
folder (reference docs only). Checks:

* every file has YAML frontmatter
* per-folder required fields are present
* ids are kebab-case and unique within their folder
* [[folder/id]] links (in frontmatter AND body) resolve to an existing file
* coordinates is a 3-number list; tier is 1..5; weight is 0..1
* plain-id prerequisites/requirements entries exist in their folder

Prints errors, exits 1 on any failure, 0 when the wiki is clean.
Stdlib + PyYAML only.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

WIKI_DIR = Path(__file__).resolve().parent.parent / "wiki"

REQUIRED_FIELDS: dict[str, list[str]] = {
    "technologies": [
        "id",
        "name",
        "branch",
        "tier",
        "cost",
        "prerequisites",
        "unlocks",
        "effects",
    ],
    "policies": ["id", "name", "category", "requirements", "effects", "tradeoffs"],
    "events": ["id", "name", "triggers", "weight", "consequences"],
    "places": ["id", "name", "type", "coordinates", "resources"],
    "lore": ["id", "title", "era"],
}

KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[\[([a-z-]+/[a-z0-9-]+)\]\]")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)


def is_number(v: object) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def load_wiki_index() -> dict[str, dict[str, Path]]:
    """{folder: {id: path}} for every content file (templates skipped)."""
    index: dict[str, dict[str, Path]] = {}
    for folder in REQUIRED_FIELDS:
        index[folder] = {}
        for path in sorted((WIKI_DIR / folder).glob("*.md")):
            if path.name.startswith("_"):
                continue
            index[folder][path.stem] = path
    return index


def parse(path: Path, errors: list[str]) -> tuple[dict, str, str] | None:
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        errors.append(f"{path}: missing YAML frontmatter")
        return None
    raw_frontmatter, body = m.group(1), m.group(2)
    try:
        meta = yaml.safe_load(raw_frontmatter) or {}
    except yaml.YAMLError as e:
        errors.append(f"{path}: invalid YAML frontmatter: {e}")
        return None
    if not isinstance(meta, dict):
        errors.append(f"{path}: frontmatter must be a mapping")
        return None
    return meta, raw_frontmatter, body


def check_links(
    path: Path, raw_frontmatter: str, body: str, index: dict, errors: list[str]
) -> None:
    for link in LINK_RE.findall(raw_frontmatter + "\n" + body):
        folder, cid = link.split("/")
        if folder not in index:
            errors.append(
                f"{path}: link [[{link}]] points at unknown folder {folder!r}"
            )
        elif cid not in index[folder]:
            errors.append(f"{path}: broken link [[{link}]] (no such file)")


def check_id(
    path: Path, meta: dict, folder: str, seen: dict[str, Path], errors: list[str]
) -> None:
    cid = meta.get("id")
    if not isinstance(cid, str) or not KEBAB_RE.match(cid):
        errors.append(f"{path}: id {cid!r} is not kebab-case")
        return
    if cid in seen:
        errors.append(f"{path}: duplicate id {cid!r} (also in {seen[cid].name})")
    else:
        seen[cid] = path


def check_plain_refs(
    path: Path, meta: dict, folder: str, index: dict, errors: list[str]
) -> None:
    """Plain-id prerequisites/requirements must exist; [[links]] are checked separately."""
    if folder == "technologies":
        fields = [("prerequisites", ["technologies"])]
    elif folder == "policies":
        # policy requirements are usually technology ids, occasionally other policies
        fields = [("requirements", ["technologies", "policies"])]
    else:
        return
    for field, search_folders in fields:
        for ref in meta.get(field) or []:
            ref_s = str(ref).strip()
            if ref_s.startswith("[["):
                continue  # link refs are validated by check_links
            if not any(ref_s in index[f] for f in search_folders):
                errors.append(f"{path}: {field} references unknown id {ref_s!r}")


def check_field_types(path: Path, meta: dict, folder: str, errors: list[str]) -> None:
    if folder == "technologies":
        tier = meta.get("tier")
        if not isinstance(tier, int) or isinstance(tier, bool) or not 1 <= tier <= 5:
            errors.append(f"{path}: tier {tier!r} must be an integer 1..5")
    if folder == "events":
        weight = meta.get("weight")
        if not is_number(weight) or not 0 <= weight <= 1:
            errors.append(f"{path}: weight {weight!r} must be a number 0..1")
        triggers = meta.get("triggers")
        if not isinstance(triggers, list) or not triggers:
            errors.append(f"{path}: triggers must be a non-empty list")
    if folder == "places":
        coords = meta.get("coordinates")
        if (
            not isinstance(coords, list)
            or len(coords) != 3
            or not all(is_number(c) for c in coords)
        ):
            errors.append(f"{path}: coordinates {coords!r} must be a 3-number list")


def main() -> int:
    errors: list[str] = []
    if not WIKI_DIR.is_dir():
        print(f"wiki directory not found: {WIKI_DIR}", file=sys.stderr)
        return 1
    index = load_wiki_index()
    checked = 0
    for folder, required in REQUIRED_FIELDS.items():
        seen: dict[str, Path] = {}
        for cid, path in sorted(index[folder].items()):
            parsed = parse(path, errors)
            if parsed is None:
                continue
            meta, raw_frontmatter, body = parsed
            checked += 1
            for field in required:
                if field not in meta:
                    errors.append(f"{path}: missing required field {field!r}")
            check_id(path, meta, folder, seen, errors)
            check_links(path, raw_frontmatter, body, index, errors)
            check_plain_refs(path, meta, folder, index, errors)
            check_field_types(path, meta, folder, errors)
    if errors:
        print(f"{len(errors)} wiki error(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"wiki OK: {checked} files validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
