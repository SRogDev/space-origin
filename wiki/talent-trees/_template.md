---
# Template — copy this file to create a new talent tree
id: my-talent-tree
name: My Talent Tree
civilization: null             # null = universal
nodes:
  - id: root-node
    name: Root Node
    cost: 1
    requires: []
    effects: ["+5% something"]
  - id: advanced-node
    name: Advanced Node
    cost: 2
    requires: ["root-node"]
    effects: ["+10% something"]
---

# My Talent Tree

What progression fantasy this tree serves.
