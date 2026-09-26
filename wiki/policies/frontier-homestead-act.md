---
# EXAMPLE FILE — minimal policy used to validate the content pipeline.
example: true
id: frontier-homestead-act
name: Frontier Homestead Act
category: economy
requirements: []
effects:
  population: "+satisfaction, +migration"
  economy: "-treasury (land grants), +production over time"
tradeoffs: "Costs treasury now for growth later; shifts values toward individualism."
value_shift:
  individualism_collectivism: -0.2
modifiers:
  economy.treasury: -50000
  population.satisfaction: 0.05
---

# Frontier Homestead Act

Grants land to new arrivals. The classic expansionist bet: spend the
treasury's surplus on people, and trust them to build.
