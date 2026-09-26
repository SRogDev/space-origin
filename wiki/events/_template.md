---
# Template — copy this file to add an event archetype
id: food-riots
name: Food Riots
triggers:                         # deterministic state predicates (evaluated by sim)
  # Dotted state paths, comparisons, arithmetic, and/or. Examples:
  - "resources.food_stock < population.size * 0.5"
  - "population.unrest > 0.6"
weight: 0.8                       # relative likelihood when triggers hold
cooldown: 5                       # OPTIONAL: minimum years between firings (default 5)
consequences:                     # state changes (sim applies, AI narrates)
  population: "-satisfaction"
  politics: "+pressure for policy change"
state_changes:                    # OPTIONAL machine-readable map, applied by the sim when fired.
  # Convention: dotted sim stat -> ADDITIVE delta (new = old + delta), clamped
  # to the stat's bounds. Whitelisted paths in api/content.py.
  # population.satisfaction: -0.05
ai_brief: "Generate a news report: which districts, who leads the protests, what the government says."
---

# Food Riots

Design notes: when this fires, what player responses should be meaningful?
Which policies/technologies could have prevented it?
