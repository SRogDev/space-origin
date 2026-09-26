---
# EXAMPLE FILE — minimal event used to validate the content pipeline.
example: true
id: solar-flare
name: Solar Flare
triggers:
  - "year > 2280"
weight: 0.3
consequences:
  economy: "-energy production for the year"
  population: "-satisfaction (blackouts)"
state_changes:
  economy.energy_production: -2.0
  population.satisfaction: -0.05
ai_brief: "Generate a news report: which grids failed, how long the blackout lasted, the official response."
---

# Solar Flare

Design notes: a cheap, frequent reminder that the colony depends on fragile
infrastructure. Energy policy and grid redundancy should matter when this fires.
