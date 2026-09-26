# Wiki — the game design data of SpaceOrigins

This directory is the **game design data** the code reads. Technologies, policies,
events, value axes, places, and lore live here as Markdown files with structured
frontmatter. The backend serves this content as JSON; the Three.js client renders it.

> The wiki describes the *possibility space*. The deterministic simulation decides
> what actually happens in a given playthrough. The AI narrates it.

## Structure

| Folder | Contains | Key frontmatter |
|---|---|---|
| `technologies/` | Deep researchable tech tree (branching) | `id`, `branch`, `tier`, `cost`, `prerequisites`, `unlocks`, `effects` |
| `policies/` | Government/society policies the player can enact | `id`, `category`, `requirements`, `effects`, `tradeoffs` |
| `events/` | Event archetypes triggered by simulation state | `id`, `triggers` (state predicates), `weight`, `consequences` |
| `values/` | The 5 design axes of civilization (reference doc) | — |
| `places/` | Colony sites, regions, points of interest | `id`, `type`, `coordinates`, `resources` |
| `lore/` | History, background, flavor | `id`, `era`, `related` |

## Rules

1. Every content file starts with YAML frontmatter — no frontmatter, no game.
2. `id` is unique within its folder, kebab-case.
3. Cross-references use `[[folder/id]]` links (e.g. `[[technologies/fusion-power]]`).
4. `effects` must name the simulation systems they touch (economy, population,
   military, environment, culture, politics) — effects are *declared* here but
   *computed* by the simulation, never by prose.
5. CI validates every file: schema, unique ids, unbroken links.

Each folder has a `_template.md` showing the exact schema. Copy it to start a new entry.
