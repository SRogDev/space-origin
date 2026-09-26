# space origin — Build Plan

> Content-first: the wiki is the game design document that the code reads.

## Proposed stack (to confirm)

- **Frontend**: pure Three.js + TypeScript, Vite, Tailwind for HUD overlays
- **Backend**: FastAPI + Postgres (Supabase or self-hosted) — real API, no mocks
- **Content pipeline**: `wiki/*.md` with YAML frontmatter → validated → served by API

## Phase 0 — Content system (first)

- [ ] Finalize frontmatter schemas (see `wiki/` templates)
- [ ] Content validator (CI checks every `.md` for schema + broken links)
- [ ] Content API: `GET /api/content/{type}/{id}` serves wiki as JSON
- [ ] **Content editor UI**: add/modify talent trees, civilizations, etc. from the browser — no code touched

## Phase 1 — Wiki authoring

- [ ] Dozens of `.md` files: civilizations, technologies, talent trees, places, lore
- [ ] Cross-links (tech X belongs to civilization Y, unlocks talent Z)

## Phase 2 — Three.js prototype slices

- [ ] Star map: navigable 3D map of places from `wiki/places/`
- [ ] Talent tree viewer: renders `wiki/talent-trees/` as interactive 3D/2D graphs
- [ ] Civilization codex: in-game encyclopedia from `wiki/`

## Phase 3 — Gameplay (only after content is rich enough)

- [ ] To be defined from the conversations Roger will send

## Open questions (for Roger)

- [ ] Backend: FastAPI + Supabase, or something else?
- [ ] Content storage: markdown files in repo (git-versioned) vs DB with editor UI — or both (files as source of truth, synced to DB)?
- [ ] Language of game content: English-first? Spanish?
- [ ] License: open source or proprietary?
- [ ] What's the first playable slice — explore map? unlock tech? something else?
