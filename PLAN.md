# SpaceOrigins — Build Plan

> Spec: `docs/product-context.md`. Stack: FastAPI/Python game core + Supabase + Three.js client.
> Backend is the real game. Three.js visualizes; Godot comes later on the same core.

## Confirmed decisions (2026-09-26)

- **Backend**: FastAPI + Supabase (Postgres for saves/world state)
- **AI**: LangGraph + OpenRouter — interprets world state, generates content; NEVER mutates simulation state
- **Content**: `wiki/` structured `.md` files are the game design data (tech, policies, events, values, places, lore) — no content DB for now
- **Client**: pure Three.js + TypeScript (Vite) — HUD/sci-fi grand-strategy presentation
- **Language**: English (for now)
- **License**: AGPL-3.0
- **Scope**: single-player, no blockchain/P2E, no AAA graphics

## Phase 0 — Content system + world model

- [x] `wiki/` schemas finalized (technologies, policies, events, values, places, lore) — `_template.md` per folder + machine-readable maps (`stat_modifiers`/`modifiers`/`state_changes`); 1 example file per folder
- [x] Content validator: `scripts/validate_wiki.py` — schema, unique ids, unbroken `[[links]]` (exit 0; asserted by `api/tests/test_wiki.py`)
- [x] Content API: `GET /api/content/{type}` + `GET /api/content/{type}/{id}` serves wiki as JSON
- [x] World state model (Pydantic v2): serializable, save/load to `api/saves/`

## Phase 1 — Simulation core (deterministic, UI-independent)

- [x] Colony creation: resources, initial population, value axes (`POST /api/games`)
- [x] Tick engine: `advance_time(years)` — population, economy, resources; seeded RNG, deterministic fingerprint
- [x] Policies: apply → systemic consequences + value-axis shifts
- [x] Technology research: from `wiki/technologies/`, prereq + cost gating
- [x] Events: deterministic state predicates (safe parser, no `eval()`), cooldowns
- [x] History log accumulation (per-tick entries)
- [x] Tests: 51 tests — colony → +10y plausible deltas, determinism, 100y soak (no NaN/explosions), event firing; RED→GREEN evidenced

> CI note: no `.github/workflows/` in this repo — the stored GitHub token lacks the
> `workflows` scope, so API pushes cannot write workflow files. Add CI from a
> full-scope token or a local `git push` when available. Intended CI: ruff +
> pytest + `validate_wiki.py` + `npm run build`.

## Phase 2 — AI content layer (LangGraph)

- [ ] State → narrative: news, reports, event descriptions
- [ ] Player Q&A over world state ("why is unemployment rising?")
- [ ] Advisory: consequence previews (information only)

## Phase 3 — Three.js client slices

- [ ] Star map viewer (places from `wiki/places/`)
- [ ] Talent/tech tree viewer (interactive graph from `wiki/technologies/`)
- [ ] Battle viewer (military conflicts resolved by the simulation, visualized)

## Phase 4 — MVP loop

Start colony → design society → manage → tech → evolve → events → respond →
time advances → civilization changes → save/continue. One colony, limited region.

## Open questions (for Roger)

- [x] Product name spelling — resolved 2026-09-26: **SpaceOrigins**, repo `SRogDev/spaceorigins`
