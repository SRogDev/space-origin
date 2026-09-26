---
# Template — copy this file to add a policy
id: universal-basic-dividend
name: Universal Basic Dividend
category: economy                  # economy | politics | military | environment | culture | science
requirements:                      # tech or conditions needed
  - "[[technologies/post-scarcity-manufacturing]]"
effects:
  population: "+satisfaction, -unrest"
  economy: "-treasury drain, +consumption"
tradeoffs: "Reduces funds available for military and research; shifts values toward collectivism."
value_shift:                       # pushes on the axes (see ../values/)
  individualism_collectivism: +0.2
modifiers:                        # OPTIONAL machine-readable map, applied ONCE when enacted.
  # Convention: dotted sim stat -> ADDITIVE delta (new = old + delta).
  #   {economy.treasury: -50000} spends 50k from the treasury at enactment.
  #   Result is clamped to the stat's bounds. Whitelisted paths in api/content.py.
  # economy.treasury: -50000
---

# Universal Basic Dividend

What the policy does, who supports/opposes it, and what kind of civilization
it builds. Policies must have real tradeoffs — no free lunches.
