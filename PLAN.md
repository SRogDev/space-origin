# Space Origins — Build Plan

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

- [ ] `wiki/` schemas finalized (technologies, policies, events, values, places, lore)
- [ ] Content validator (CI): schema, unique ids, unbroken `[[links]]`
- [ ] Content API: `GET /api/content/{type}/{id}` serves wiki as JSON
- [ ] World state model (Pydantic): serializable, save/load

## Phase 1 — Simulation core (deterministic, UI-independent)

- [ ] Colony creation: resources, initial population, value axes
- [ ] Tick engine: `advance_time(years)` — population, economy, resources
- [ ] Policies: apply → systemic consequences
- [ ] Technology research: deep tree from `wiki/technologies/`
- [ ] Events: triggered from simulation state (deterministic predicates)
- [ ] History log accumulation
- [ ] Tests: colony → +10 years → assert plausible deltas; 100/500/1000-year soak runs

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

- [ ] Product name spelling: **Space Origins** (doc) vs **space origin** (repo)?
