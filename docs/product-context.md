# SpaceOrigins — Product Context

> Extracted from Roger's product conversations (2026-09-26). Canonical spec for builders.

## Identity

**SpaceOrigins** is an open-source **single-player** space-colony / civilization
simulation game. Setting: **Year 2280.**

The player controls a space-colonization corporation establishing human
civilization in a region of the galaxy. Central fantasy: **"Design humanity from scratch."**

Not city-building — designing the principles, institutions, economy, culture,
technology, and society of a new human civilization, then observing what emerges.

Core question: **"What kind of humanity would you create if you could establish
a new civilization?"**

## Value axes (player-designable, combinable — not fixed archetypes)

- Liberty ↔ Authority
- Individualism ↔ Collectivism
- Pacifism ↔ Militarism
- Ecology ↔ Industrialism
- Secular ↔ Spiritual

Principles propagate through the simulation: policies, institutions, tech
priorities, population behavior, events.

## Core loop

Create colony → design society → principles/policies → technology →
allocate resources → population/economy/society/politics evolve →
unexpected events → player responds → consequences emerge →
civilization develops → redesign/adapt…

The hook: **"What did my civilization become?"**

## Simulation (the heart of the game)

Interconnected systems, not decorative stats:

- **Population** (simulated, not a number): size, demographics, growth, birth/death,
  employment, productivity, wealth, social groups, value distributions, migration,
  living conditions, satisfaction/unrest, education, health
- **Economy**: resources, production, labor, consumption, wealth, trade,
  infrastructure, industry, technology, taxation, investment, shortages/surpluses
- **Resources**: scarce; constrain production, tech, construction, trade, military
- **Politics/government**: real mechanics — decision-making, allocation, stability,
  economic behavior, values, military/scientific/environmental policy
- **Technology**: DEEP trees — science, biology, genetics, augmentation, energy,
  fusion, antimatter, computing, AI, quantum, space travel, terraforming, megastructures.
  Tech changes economy, military, population, environment, culture, politics,
  policies, future options. Fantasy = "use technology to shape humanity."
- **Time**: advance years/decades per tick; long runs must work without an LLM call per tick
- **History**: accumulate major events, wars, discoveries, breakthroughs, political/
  demographic/economic changes, leaders, movements, policies
- **Events**: political/economic crises, discoveries, breakthroughs, movements,
  conflicts, disasters — **emerging from the simulation**, not random lists

Goal: interacting systems with interesting consequences. Trade-offs everywhere.

## AI architecture (critical)

**The AI is NOT the simulation engine.** Deterministic simulation produces factual
world state (population −17%, food −32%, …). The AI **interprets** that state:

```
Deterministic Simulation → World State → AI Interpretation / Content
```

NEVER: LLM → randomly changes world state. This keeps the game coherent, testable, cheap.

AI responsibilities (LangGraph orchestration):
- Event generation from world state
- Narrative: news, reports, descriptions, historical narratives
- Characters, social movements, inventions, discoveries, proposals
- Player Q&A: "Why is my population declining?" "What if I change this policy?"
- Advisory layer: consequences and information surfacing — never secret control

This lets a solo dev ship AAA-scale content density without hand-authoring everything.

## Game state

Canonical, serializable world state: Galaxy/Region, Colonies, Population,
Resources, Economy, Government, Society, Politics, Technology, Military,
Environment, Events, History. Save/load supported.

## Architecture: backend-first

```
              SPACEORIGINS
                    │
              REAL GAME CORE (FastAPI/Python)
                    │
        ┌───────────┼───────────┐
        │           │           │
   Simulation     State        AI (LangGraph)
        │           │           │
        └───────────┼───────────┘
                    │
                   API  (create_colony, get_world_state, advance_time,
                         apply_policy, research_technology, simulate_period,
                         save_game, load_game, …)
                    │
                 Three.js  ← first client (visualization, map, panels,
                              tech tree, charts — NOT simulation rules)
                    │
                    ▼
               Future Godot client (same core, no rewrite)
```

Three.js is the first client/prototype of the actual game — not disposable.
Simulation must be testable without the UI (e.g. simulate 100/500/1000 years,
assert plausible states).

## Presentation

Grand-strategy style (Europa Universalis-like): map, overlays, territories,
icons, panels, charts, tech trees, event windows. **No AAA graphics ambition.**
Systemic depth > visual complexity.

## Scope boundaries

- Single-player only. No multiplayer infra in MVP.
- **No blockchain / P2E.** Internal simulation economy only.
- MVP = one colony / limited region proving the central fantasy.
- Done = start colony → design humanity → play → observe evolution →
  decisions → consequences → meaningful end state → save. The player recognizes
  the civilization emerged from their decisions.

## License

AGPL-3.0 (open source, not MIT).

## Non-negotiables

1. About designing humanity. 2. Deep sim, not graphics project.
3. Year 2280, colony corporation. 4. Interacting systems (society, values,
   politics, economy, tech, population, resources). 5. Deep tech trees.
6. AI generates content around the sim. 7. Sim never depends on LLM hallucination.
8. Backend is the real game. 9. Three.js first client. 10. Godot later, same core.
11. Single-player. 12. No blockchain. 13. No AAA. 14. Depth > graphics.
15. AI reduces manual content burden.
