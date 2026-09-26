---
# EXAMPLE FILE — minimal technology used to validate the content pipeline.
example: true
id: fission-power
name: Fission Power
branch: energy
tier: 1
cost: 100
prerequisites: []
unlocks: []
effects:
  economy: "+energy production"
  environment: "+pollution"
stat_modifiers:
  economy.energy_production: 0.5
  environment.pollution: 0.05
---

# Fission Power

The first reliable colonial power source. Cheap, dirty, and politically
simple — the kind of technology that shapes a civilization by default
rather than by choice.
