---
# Template — copy this file to add a technology
id: fusion-power
name: Fusion Power
branch: energy                    # energy | biology | computing | materials | propulsion | society | ...
tier: 2                           # 1-5, depth in the tree
cost: 500                         # research points
prerequisites: ["advanced-plasma"] # technology ids
unlocks:                          # what becomes available
  - "[[technologies/antimatter-theory]]"
  - "[[policies/energy-abundance-act]]"
effects:                          # systems touched (computed by sim, not prose)
  economy: "+energy production, -energy costs"
  environment: "-pollution if replacing fission"
  unlocks_buildings: ["fusion-reactor"]
stat_modifiers:                   # OPTIONAL machine-readable map, applied by the sim on research.
  # Convention: dotted sim stat -> FRACTIONAL MULTIPLICATIVE delta.
  #   {economy.energy_production: 0.2} means new = old * (1 + 0.2)  (+20%).
  #   Negative values shrink the stat. Result is clamped to the stat's bounds.
  #   Valid dotted paths are whitelisted in api/content.py (derived from api/models.py).
  # economy.energy_production: 0.5
---

# Fusion Power

What it is, flavor, and the strategic questions it raises. Remember the fantasy:
technology should change what *kind* of humanity the player can build, not just
add +10% somewhere.
