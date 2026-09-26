# Wiki — the universe of space origin

This directory **is** the game design. Every civilization, technology, talent tree, place, and piece of lore lives here as a Markdown file with structured frontmatter. The backend serves this content as JSON; the frontend renders it.

## Structure

| Folder | Contains | Key frontmatter |
|---|---|---|
| `civilizations/` | Playable/NPC factions | `id`, `name`, `ethos`, `home_system`, `bonuses` |
| `technologies/` | Researchable techs | `id`, `name`, `tier`, `cost`, `prerequisites`, `unlocks`, `civilization` |
| `talent-trees/` | Progression trees | `id`, `name`, `nodes[]` (id, name, cost, requires, effects) |
| `places/` | Star systems, planets, stations | `id`, `name`, `type`, `coordinates`, `faction`, `resources` |
| `lore/` | History, events, characters | `id`, `title`, `era`, `related[]` |

## Rules

1. Every file starts with YAML frontmatter — no frontmatter, no game.
2. `id` is unique within its folder, kebab-case.
3. Cross-references use `[[folder/id]]` links (e.g. `[[technologies/plasma-drives]]`).
4. CI validates every file: schema, unique ids, unbroken links.

Each folder has a `_template.md` showing the exact schema. Copy it to start a new entry.
