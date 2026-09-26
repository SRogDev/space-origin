# SpaceOrigins

**Open-source single-player space-colony / civilization simulation.** Year 2280.
You are a space-colonization corporation. The fantasy: **"Design humanity from scratch."**

Choose your civilization's principles — liberty vs authority, ecology vs industry,
pacifism vs militarism — then watch population, economy, politics, technology and
culture evolve from those choices. **"What did my civilization become?"**

## Architecture: backend-first

The **FastAPI/Python game core is the real game** — deterministic simulation,
serializable world state, save/load, testable without any UI. The AI
(LangGraph) **interprets** world state into events, news, and narratives —
it never decides the simulation's facts.

**Three.js** is the first client (map, panels, tech trees, HUD) — not disposable,
but never the source of truth. Godot can become a second client later on the
same core.

Content (technologies, policies, events, values, places, lore) is authored as
structured Markdown in [`wiki/`](wiki/) — the game design data the code reads.

## Boundaries

Single-player. No blockchain/P2E. No AAA graphics — systemic depth over visuals.

## Status

Early build — see [PLAN.md](PLAN.md), spec in [docs/product-context.md](docs/product-context.md),
content index in [wiki/README.md](wiki/README.md).

## License

AGPL-3.0 — see [LICENSE](LICENSE).
