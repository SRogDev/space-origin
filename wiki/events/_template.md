---
# Template — copy this file to add an event archetype
id: food-riots
name: Food Riots
triggers:                         # deterministic state predicates (evaluated by sim)
  - "food_stock < population * 0.5"
  - "unrest > 0.6"
weight: 0.8                       # relative likelihood when triggers hold
consequences:                     # state changes (sim applies, AI narrates)
  population: "-satisfaction"
  politics: "+pressure for policy change"
ai_brief: "Generate a news report: which districts, who leads the protests, what the government says."
---

# Food Riots

Design notes: when this fires, what player responses should be meaningful?
Which policies/technologies could have prevented it?
