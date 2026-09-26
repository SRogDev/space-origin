# space origin

**Content-first space strategy prototype.** Pure Three.js — no game engine. Real backend.

The universe is authored as content: civilizations, technologies, talent trees, places, and lore live as Markdown files in [`wiki/`](wiki/). Gameplay is built *on top of* that content, not the other way around.

## Architecture

- **Frontend**: pure Three.js (no Unity/Godot/Unreal) — HUD/sci-fi aesthetic
- **Backend**: real API serving game content + state (no mocks)
- **Content**: `wiki/` — dozens of `.md` files with structured frontmatter; a UI endpoint lets you add/modify content (talent trees, civilizations, …) without touching code. Markdown is the source of truth (no content DB for now).
- **First slices**: star map viewer, talent tree viewer, battle viewer

## The rule

> No gameplay until there is enough world to play in.

First the civilizations, technologies, talent trees, and places. Then the systems that bring them to life.

## Status

Early scaffold — see [PLAN.md](PLAN.md). Wiki index: [wiki/README.md](wiki/README.md).

## License

TBD (confirm: open source or proprietary?)
